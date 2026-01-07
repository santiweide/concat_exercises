"""
PDF Import Service - Uses Gemini AI to extract reading questions from exam papers.
"""
import asyncio
import base64
import json
import os
import re
import time
import uuid
import httpx
import structlog
from typing import Optional, Dict, Any, List
from io import BytesIO

import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv

from config import config
from storage import question_store
from models import ReadingQuestion

# Load environment variables from .env file
load_dotenv()

logger = structlog.get_logger()

# Gemini API configuration - loaded from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set in environment variables!")
# Use gemini-1.5-flash for faster image processing
GEMINI_API_URL_TEXT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_URL_IMAGE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Limits for image processing
MAX_PAGES = 15  # Limit pages to avoid payload too large errors
MAX_IMAGE_SIZE = 1536  # Max dimension for image resizing


class PDFImportService:
    """Service for importing PDF exam papers using Gemini AI."""
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF using pdfplumber."""
        text_content = ""
        page_count = 0
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    # pdfplumber can also extract tables, here we only get text
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            
            if not text_content.strip():
                logger.warning("Empty text extracted (likely a scanned image PDF)")
            else:
                logger.info("PDF text extracted", pages=page_count, chars=len(text_content))
        except Exception as e:
            logger.error("Failed to extract PDF text", error=str(e))
            raise
        return text_content
    
    def _convert_pdf_to_images(self, pdf_path: str) -> List[str]:
        """
        Convert PDF pages to compressed, base64 encoded JPEG images.
        Uses thumbnail resizing and quality compression to reduce payload size.
        
        IMPORTANT: This returns pure inline data, NOT using upload_file API.
        """
        images_base64 = []
        try:
            # Convert PDF to images with moderate DPI (200 is enough for text clarity)
            logger.info("Converting PDF to images...")
            images = convert_from_path(pdf_path, dpi=200)
            total_pages = len(images)
            logger.info("PDF converted to images", total_pages=total_pages)
            
            # Limit pages to avoid payload too large (Google API ~20MB limit)
            if total_pages > MAX_PAGES:
                logger.warning(f"PDF has {total_pages} pages, truncating to {MAX_PAGES}")
                images = images[:MAX_PAGES]
            
            for i, img in enumerate(images):
                # Resize image to reduce size - Gemini works well with 1024-2048px
                # Original scanned images might be 4000+ px
                img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
                
                # Convert to JPEG bytes with compression
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=80, optimize=True)
                img_bytes = buffer.getvalue()
                
                # Encode to base64
                img_base64 = base64.standard_b64encode(img_bytes).decode('utf-8')
                images_base64.append(img_base64)
                
                logger.debug(f"Page {i+1} processed", size_kb=len(img_bytes)//1024)
            
            total_size_mb = sum(len(base64.b64decode(img)) for img in images_base64) / (1024 * 1024)
            logger.info("Images prepared for API", 
                       count=len(images_base64), 
                       total_size_mb=round(total_size_mb, 2))
            
        except Exception as e:
            logger.error("Failed to convert PDF to images", error=str(e))
            raise
        return images_base64
    
    async def parse_pdf(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """
        Parse a PDF file and extract reading questions using Gemini AI.
        Returns parsed data for preview without saving to database.
        
        Args:
            pdf_path: Path to the PDF file
            filename: Original filename for reference
            
        Returns:
            Dictionary with extraction results for preview
        """
        try:
            # Try to extract text from PDF locally first (much faster)
            text_content = self._extract_text_from_pdf(pdf_path)
            
            if text_content.strip():
                # Text extracted successfully, use text mode
                logger.info("Using text mode for Gemini API")
                extracted_data = await self._call_gemini_api_text(text_content, filename)
            else:
                # No text extracted, likely a scanned PDF - use image mode
                logger.info("No text found, switching to image mode for Gemini API")
                images_base64 = self._convert_pdf_to_images(pdf_path)
                
                if not images_base64:
                    return {
                        'success': False,
                        'error': 'PDF文件无法处理，请检查文件是否损坏'
                    }
                
                extracted_data = await self._call_gemini_api_images(images_base64, filename)
            
            if not extracted_data:
                return {
                    'success': False,
                    'error': 'AI解析失败，请确保PDF内容清晰'
                }
            
            # Generate preview data without saving
            preview_data = self._generate_preview(extracted_data)
            
            return {
                'success': True,
                'preview': preview_data
            }
            
        except Exception as e:
            logger.exception("PDF processing error", error=str(e))
            return {
                'success': False,
                'error': f'处理出错: {str(e)}'
            }
    
    def _generate_preview(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data from extracted data."""
        title = extracted_data.get('title', '未知来源')
        year = extracted_data.get('year', 2024)
        questions = extracted_data.get('questions', [])
        
        preview_questions = []
        for idx, q in enumerate(questions):
            question_number = q.get('questionNumber', chr(65 + idx))  # A, B, C, D...
            article_content = q.get('articleContent', '')
            question_content = q.get('questionContent', '')
            labels = q.get('labels', [])
            answers = q.get('answers', [])  # List of {number, answer}
            
            # Skip empty questions
            if not article_content and not question_content:
                continue
            
            # Count sub-questions (usually numbered 1., 2., 3., etc. or A., B., etc.)
            sub_question_count = self._count_sub_questions(question_content)
            
            # Generate article summary (first 20 words)
            article_summary = self._get_word_summary(article_content, 20)
            
            preview_questions.append({
                'id': f"preview-{uuid.uuid4().hex[:8]}",
                'questionNumber': question_number,
                'articleContent': article_content,
                'questionContent': question_content,
                'articleSummary': article_summary,
                'subQuestionCount': sub_question_count,
                'labels': labels,
                'answers': answers,
            })
        
        return {
            'title': title,
            'year': year,
            'totalQuestions': len(preview_questions),
            'questions': preview_questions,
        }
    
    def _count_sub_questions(self, question_content: str) -> int:
        """Count the number of sub-questions in the question content."""
        # Match patterns like "21.", "22.", "1.", "2.", "(1)", "(2)", etc.
        patterns = [
            r'^\s*\d+\s*[\.、]',  # 1. 2. 3. or 1、2、3、
            r'^\s*\(\d+\)',       # (1) (2) (3)
            r'^\s*[A-Z]\s*[\.、]',  # A. B. C. or A、B、
        ]
        
        lines = question_content.split('\n')
        count = 0
        for line in lines:
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    count += 1
                    break
        
        # If no matches found, try to count by looking for question markers
        if count == 0:
            # Count occurrences of common question patterns
            count = len(re.findall(r'\b(?:What|Which|Who|Where|When|Why|How|According)\b', question_content, re.IGNORECASE))
        
        return max(count, 1)  # At least 1 question
    
    def _get_word_summary(self, text: str, word_count: int) -> str:
        """Get first N words of text as summary."""
        if not text:
            return ''
        
        # Clean the text
        text = ' '.join(text.split())
        
        # Split into words
        words = text.split()
        
        if len(words) <= word_count:
            return text
        
        return ' '.join(words[:word_count]) + '...'
    
    def check_title_exists(self, title: str) -> bool:
        """Check if a paper with the given title already exists in database."""
        return question_store.exists_by_title(title)
    
    async def confirm_import(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Confirm and save the imported questions to database.
        
        Args:
            import_data: The edited import data from frontend
            
        Returns:
            Dictionary with import results
        """
        try:
            title = import_data.get('title', '未知来源')
            year = import_data.get('year', 2024)
            questions = import_data.get('questions', [])
            
            # Check if paper with this title already exists
            if self.check_title_exists(title):
                return {
                    'success': False,
                    'duplicate': True,
                    'error': f'试卷「{title}」已存在于数据库中，请勿重复导入'
                }
            
            saved_questions = []
            current_time = int(time.time() * 1000)
            
            for q in questions:
                article_content = q.get('articleContent', '')
                question_content = q.get('questionContent', '')
                question_number = q.get('questionNumber', 'A')
                labels = q.get('labels', [])
                answers = q.get('answers', [])  # List of {number, answer}
                
                # Skip empty questions
                if not article_content or not question_content:
                    continue
                
                # Create question
                question = ReadingQuestion(
                    id=f"q-{uuid.uuid4().hex[:8]}",
                    title=title,
                    year=year,
                    questionNumber=question_number,
                    articleContent=article_content,
                    questionContent=question_content,
                    labels=labels,
                    answers=answers,
                    createdAt=current_time,
                    updatedAt=current_time
                )
                
                # Save to store
                created = question_store.create(question.model_dump())
                saved_questions.append(created)
                
                logger.info("Question saved", 
                           id=created.id, 
                           title=title, 
                           questionNumber=question_number,
                           labels=labels)
            
            return {
                'success': True,
                'title': title,
                'questionsImported': len(saved_questions),
                'questions': [
                    {
                        'id': q.id,
                        'questionNumber': q.questionNumber,
                        'labels': q.labels
                    }
                    for q in saved_questions
                ]
            }
            
        except Exception as e:
            logger.exception("Import confirmation error", error=str(e))
            return {
                'success': False,
                'error': f'保存失败: {str(e)}'
            }
    
    def _get_extraction_prompt(self) -> str:
        """Get the prompt for extracting reading questions and answers."""
        return """你是一个专业的高考英语试卷分析助手。请仔细分析试卷内容，提取其中的阅读理解部分及其答案。

请按照以下JSON格式返回结果：

```json
{
    "title": "试卷标题（如：2023年全国卷I）",
    "year": 2023,
    "questions": [
        {
            "questionNumber": "A",
            "articleContent": "阅读文章的完整原文内容...",
            "questionContent": "题目和选项的完整内容，包括所有小题...",
            "labels": ["主题标签1", "主题标签2", "主题标签3"],
            "answers": [
                {"number": 21, "answer": "B"},
                {"number": 22, "answer": "A"},
                {"number": 23, "answer": "D"}
            ]
        }
    ]
}
```

要求：
1. 识别试卷来源和年份（从试卷标题或页眉提取）
2. 提取所有阅读理解题目（通常在大标题"第二部分 阅读理解"下的第一节，通常标记为A、B、C、D四篇）
3. articleContent：完整提取每篇阅读的文章原文
4. questionContent：提取该篇文章对应的所有题目和选项，通常题目序号分别为21-23，24-27，28-31，32-35。注意每个编号表示一个小题，而不是每个选项代表一个小题（因为是选择题）。
5. labels：根据文章内容生成3-5个语义标签，描述文章的主题、体裁、话题等
   - 主题标签示例：科技、环境、文化、教育、健康、社会、历史、艺术、体育、经济
   - 体裁标签示例：记叙文、说明文、议论文、新闻报道、人物传记
   - 话题标签示例：人工智能、气候变化、传统文化、青少年成长等
6. answers：从"英语参考答案"部分的"第二部分 阅读理解"中提取每个小题的答案
   - number：小题题号（如21, 22, 23等整数）
   - answer：该小题的正确答案（A、B、C或D）
   - 如果找不到答案部分，answers数组可以为空

请只返回JSON格式的结果，不要包含其他文字说明。如果无法识别为英语试卷，返回：
```json
{"error": "无法识别为英语试卷"}
```
"""
    
    async def _call_gemini_api_text(self, text_content: str, filename: str) -> Optional[Dict[str, Any]]:
        """Call Gemini API to extract reading questions from text content."""
        
        base_prompt = self._get_extraction_prompt()
        prompt = f"""{base_prompt}

试卷内容：
---
{text_content}
---
"""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{GEMINI_API_URL_TEXT}?key={self.api_key}",
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {
                                        "text": prompt
                                    }
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.1,
                            "topK": 40,
                            "topP": 0.95,
                            "maxOutputTokens": 65536,
                        }
                    },
                    headers={
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error("Gemini API error", 
                                status=response.status_code, 
                                body=response.text[:500])
                    return None
                
                result = response.json()
                
                # Extract text from response
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        text = candidate['content']['parts'][0].get('text', '')
                        
                        # Parse JSON from response
                        return self._parse_gemini_response(text)
                
                return None
                
        except httpx.TimeoutException:
            logger.error("Gemini API timeout")
            return None
        except Exception as e:
            logger.exception("Gemini API call failed", error=str(e))
            return None
    
    async def _call_gemini_api_images(self, images_base64: List[str], filename: str) -> Optional[Dict[str, Any]]:
        """Call Gemini API to extract reading questions from images (for scanned PDFs)."""
        
        base_prompt = self._get_extraction_prompt()
        prompt = f"""请阅读这些图片中的试卷文档内容。

{base_prompt}
"""

        # Build parts with images and prompt
        parts = []
        
        # Add all images first
        for img_base64 in images_base64:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": img_base64
                }
            })
        
        # Add prompt text at the end
        parts.append({
            "text": prompt
        })

        try:
            # Use longer timeout for image processing (multiple images can take time)
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{GEMINI_API_URL_IMAGE}?key={self.api_key}",
                    json={
                        "contents": [
                            {
                                "parts": parts
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.1,
                            "topK": 40,
                            "topP": 0.95,
                            "maxOutputTokens": 65536,
                        }
                    },
                    headers={
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error("Gemini API error (image mode)", 
                                status=response.status_code, 
                                body=response.text[:500])
                    return None
                
                result = response.json()
                
                # Extract text from response
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        text = candidate['content']['parts'][0].get('text', '')
                        
                        # Parse JSON from response
                        return self._parse_gemini_response(text)
                
                return None
                
        except httpx.TimeoutException:
            logger.error("Gemini API timeout (image mode)")
            return None
        except Exception as e:
            logger.exception("Gemini API call failed (image mode)", error=str(e))
            return None
    
    def _parse_gemini_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Gemini response text."""
        try:
            # Try to extract JSON from markdown code blocks
            if '```json' in text:
                start = text.find('```json') + 7
                end = text.find('```', start)
                if end > start:
                    text = text[start:end].strip()
            elif '```' in text:
                start = text.find('```') + 3
                end = text.find('```', start)
                if end > start:
                    text = text[start:end].strip()
            
            # Parse JSON
            data = json.loads(text)
            
            # Check for error response
            if 'error' in data:
                logger.warning("Gemini returned error", error=data['error'])
                return None
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini response", error=str(e), text=text[:500])
            return None


# Singleton instance
pdf_import_service = PDFImportService()
