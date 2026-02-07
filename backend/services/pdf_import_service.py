"""
PDF Import Service - Uses AI models to extract reading questions from exam papers.
Supports multiple AI backends: Gemini, Qwen VL, etc.
"""
import asyncio
import base64
import json
import json_repair
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
from storage import question_store, operation_log_store
from models import ReadingQuestion, OperationType
from services.ai_models import AIModel, AIModelType, GeminiModel, QwenVLModel

# Load environment variables from .env file
load_dotenv()

logger = structlog.get_logger()

# Limits for image processing
MAX_PAGES = 15  # Limit pages to avoid payload too large errors
MAX_IMAGE_SIZE = 1536  # Max dimension for image resizing


class PDFImportService:
    """Service for importing PDF exam papers using AI models."""
    
    def __init__(self, model_type: str = None):
        """
        Initialize PDF import service with specified AI model.
        
        Args:
            model_type: Type of AI model to use ("gemini" or "qwen-vl"). 
                       If None, uses default from config.
        """
        if model_type is None:
            model_type = config.DEFAULT_AI_MODEL
        
        self.model_type = model_type
        self._model = None  # Lazy initialization
    
    @property
    def model(self) -> AIModel:
        """Lazy-load the AI model on first access."""
        if self._model is None:
            self._model = self._create_model(self.model_type)
        return self._model
    
    def _create_model(self, model_type: str) -> AIModel:
        """Create and return the appropriate AI model instance."""
        model_type = model_type.lower()
        
        if model_type == "gemini":
            api_key = config.GEMINI_API_KEY
            if not api_key:
                logger.error("GEMINI_API_KEY not set in environment variables!")
                raise ValueError("GEMINI_API_KEY is required for Gemini model")
            return GeminiModel(api_key)
        
        elif model_type == "qwen-vl":
            api_key = config.QWEN_API_KEY
            if not api_key:
                logger.error("QWEN_API_KEY not set in environment variables!")
                raise ValueError("QWEN_API_KEY is required for Qwen VL model")
            return QwenVLModel(api_key)
        
        else:
            logger.error("Unknown model type", model_type=model_type)
            raise ValueError(f"Unsupported model type: {model_type}")
    
    @staticmethod
    def get_available_models() -> List[Dict[str, str]]:
        """
        Get list of available AI models with their configuration status.
        
        Returns:
            List of dicts with model info: {type, name, available}
        """
        models = []
        
        # Gemini
        models.append({
            "type": "gemini",
            "name": "Google Gemini 2.0 Flash",
            "available": bool(config.GEMINI_API_KEY)
        })
        
        # Qwen VL
        models.append({
            "type": "qwen-vl",
            "name": "Qwen VL Max",
            "available": bool(config.QWEN_API_KEY)
        })
        
        return models
    
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
    
    # Minimum text length threshold to consider text extraction successful
    # If extracted text is shorter than this, treat as scanned/image PDF
    MIN_TEXT_LENGTH = 100
    
    async def parse_pdf(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """
        Parse a PDF file and extract reading questions using AI model.
        Returns parsed data for preview without saving to database.
        
        Args:
            pdf_path: Path to the PDF file
            filename: Original filename for reference
            
        Returns:
            Dictionary with extraction results for preview
        """
        try:
            logger.info("Starting PDF parsing", 
                       filename=filename, 
                       model=self.model.name,
                       model_type=self.model_type)
            
            # Try to extract text from PDF locally first (much faster)
            text_content = self._extract_text_from_pdf(pdf_path)
            text_length = len(text_content.strip())
            
            # Check if text extraction was meaningful
            # Some scanned PDFs have a low-quality OCR layer with garbage text
            is_text_sufficient = text_length >= self.MIN_TEXT_LENGTH
            
            # Get extraction prompt
            prompt = self._get_extraction_prompt()
            
            if text_content.strip() and is_text_sufficient:
                # Text extracted successfully with sufficient content, use text mode
                logger.info("Using text mode for AI extraction", 
                           text_length=text_length,
                           threshold=self.MIN_TEXT_LENGTH,
                           model=self.model.name)
                extracted_data = await self.model.extract_from_text(text_content, filename, prompt)
            else:
                # No text or insufficient text extracted, likely a scanned PDF - use image mode
                if text_length > 0:
                    logger.warning("Text too short, likely garbage OCR layer. Switching to image mode",
                                  text_length=text_length,
                                  threshold=self.MIN_TEXT_LENGTH,
                                  text_preview=text_content[:100] if text_length > 0 else "")
                else:
                    logger.info("No text found, switching to image mode",
                               model=self.model.name)
                
                images_base64 = self._convert_pdf_to_images(pdf_path)
                
                if not images_base64:
                    return {
                        'success': False,
                        'error': 'PDF文件无法处理，请检查文件是否损坏'
                    }
                
                extracted_data = await self.model.extract_from_images(images_base64, filename, prompt)
            
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
            section = q.get('section', '')
            subsection = q.get('subsection', '')
            question_number = q.get('questionNumber', chr(65 + idx))  # A, B, C, D...
            article_content = q.get('articleContent', '')
            question_content = q.get('questionContent', '')
            labels = q.get('labels', [])
            answers = q.get('answers', [])  # List of {number, answer}
            # Use Gemini's subQuestionCount if available, otherwise fallback to local counting
            sub_question_count = q.get('subQuestionCount', 0)
            
            # Skip empty questions (but allow empty articleContent for essays)
            if not article_content and not question_content:
                continue
            
            # Fallback: count sub-questions locally if Gemini didn't provide it
            if sub_question_count <= 0:
                sub_question_count = self._count_sub_questions(question_content)
            
            # Smart defaults for section and subsection if not provided by Gemini
            if not section or not subsection:
                inferred_section, inferred_subsection = self._infer_section_subsection(question_number)
                if not section:
                    section = inferred_section
                if not subsection:
                    subsection = inferred_subsection
            
            # Generate article summary (first 20 words, strip LaTeX commands for display)
            article_summary = self._get_word_summary(self._strip_latex(article_content), 20)
            
            preview_questions.append({
                'id': f"preview-{uuid.uuid4().hex[:8]}",
                'section': section,
                'subsection': subsection,
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
    
    def _infer_section_subsection(self, question_number: str) -> tuple[str, str]:
        """Infer section and subsection from question number."""
        qn = question_number.upper()
        
        # 第二部分 阅读理解 - 第一节 (A, B, C, D)
        if qn in ['A', 'B', 'C', 'D']:
            return '第二部分 阅读理解', '第一节'
        
        # 第一部分 知识运用 - 第一节 (完形填空)
        if '完形填空' in qn or 'CLOZE' in qn:
            return '第一部分 知识运用', '第一节'
        
        # 第一部分 知识运用 - 第二节 (语法填空)
        if '语法填空' in qn or 'GRAMMAR' in qn:
            return '第一部分 知识运用', '第二节'
        
        # 第二部分 阅读理解 - 第二节 (七选五)
        if '七选五' in qn or '7选5' in qn:
            return '第二部分 阅读理解', '第二节'
        
        # 第三部分 书面表达 - 第一节 (阅读表达/改错/续写等)
        if '阅读表达' in qn or '改错' in qn or '续写' in qn:
            return '第三部分 书面表达', '第一节'
        
        # 第三部分 书面表达 - 第二节 (作文)
        if '作文' in qn or 'WRITING' in qn or 'COMPOSITION' in qn:
            return '第三部分 书面表达', '第二节'
        
        # 默认：第二部分 阅读理解 - 第一节
        return '第二部分 阅读理解', '第一节'
    
    def _strip_latex(self, text: str) -> str:
        """Strip common LaTeX commands for plain text display."""
        if not text:
            return ''
        # Remove common LaTeX commands
        result = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)  # \command{content} -> content
        result = re.sub(r'\\[a-zA-Z]+\[[^\]]*\]\{([^}]*)\}', r'\1', result)  # \command[opt]{content} -> content
        result = re.sub(r'\\[a-zA-Z]+', '', result)  # \command -> ''
        result = re.sub(r'[{}]', '', result)  # Remove braces
        result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
        return result.strip()
    
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
    
    async def confirm_import(self, import_data: Dict[str, Any], force_overwrite: bool = False, operator_email: str = "") -> Dict[str, Any]:
        """
        Confirm and save the imported questions to database.
        
        Args:
            import_data: The edited import data from frontend
            force_overwrite: If True, overwrite existing paper with same title
            operator_email: Email of the operator performing the import
            
        Returns:
            Dictionary with import results
        """
        try:
            title = import_data.get('title', '未知来源')
            year = import_data.get('year', 2024)
            questions = import_data.get('questions', [])
            
            # Check if paper with this title already exists
            if self.check_title_exists(title):
                if force_overwrite:
                    # Delete existing questions with this title
                    deleted_count = question_store.delete_by_title(title)
                    logger.info("Overwriting existing paper", title=title, deleted=deleted_count)
                else:
                    return {
                        'success': False,
                        'duplicate': True,
                        'error': f'试卷「{title}」已存在于数据库中，是否覆盖更新？'
                    }
            
            saved_questions = []
            current_time = int(time.time() * 1000)
            
            for q in questions:
                section = q.get('section', '')
                subsection = q.get('subsection', '')
                article_content = q.get('articleContent', '')
                question_content = q.get('questionContent', '')
                question_number = q.get('questionNumber', 'A')
                labels = q.get('labels', [])
                answers = q.get('answers', [])  # List of {number, answer}
                sub_question_count = q.get('subQuestionCount', 0)  # Number of sub-questions
                
                # Skip empty questions (but allow empty articleContent for essays)
                if not question_content and not article_content:
                    continue
                
                # Create question
                question = ReadingQuestion(
                    id=f"q-{uuid.uuid4().hex[:8]}",
                    title=title,
                    year=year,
                    section=section,
                    subsection=subsection,
                    questionNumber=question_number,
                    articleContent=article_content,
                    questionContent=question_content,
                    labels=labels,
                    answers=answers,
                    subQuestionCount=sub_question_count,
                    createdAt=current_time,
                    updatedAt=current_time
                )
                
                # Save to store
                created = question_store.create(question.model_dump())
                saved_questions.append(created)
                
                # Create operation log for the new question
                if operator_email:
                    operation_log_store.create(
                        operation_type=OperationType.CREATE,
                        question=created,
                        operator_email=operator_email
                    )
                
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
                        'section': q.section,
                        'subsection': q.subsection,
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
        """Get the prompt for extracting ALL exam questions in LaTeX format."""
        return r'''你是一个专业的高考英语试卷分析助手。请仔细分析试卷内容，提取其中**所有**题目部分（知识运用、阅读理解、书面表达）及其答案，并以LaTeX格式输出。

## 试卷结构说明

高考英语试卷通常包含以下三个部分：

### 第一部分 知识运用
- **第一节**：完形填空（约10-15道选择题，文章中有编号空格如\clozeblank{1}）
- **第二节**：语法填空（约10道填空题，可能有提示词或无提示词）

### 第二部分 阅读理解
- **第一节**：阅读选择题（通常4篇文章A/B/C/D，每篇3-5道选择题）
- **第二节**：七选五（1篇文章，5个空，从7个选项中选择）

### 第三部分 书面表达
- **第一节**：阅读表达/问答题（阅读短文后回答问题）
- **第二节**：作文（应用文写作，如书信、通知等）

## 输出格式要求

请按照以下JSON格式返回结果，**所有题目内容必须使用LaTeX格式**：

```json
{
    "title": "试卷标题（如：北京市朝阳区高三年级第二学期质量检测一），注意去掉title字段中所有的空格、tab字符",
    "year": 2025,
    "questions": [
        {
            "section": "第一部分 知识运用",
            "subsection": "第一节",
            "questionNumber": "完形填空",
            "articleContent": "LaTeX格式的完形填空文章，空格用\\clozeblank{序号}表示...",
            "questionContent": "LaTeX格式的选项，如：\\textbf{1.} \\option{took}{made}{gave}{brought}（注意：不包含A.B.C.D.前缀）",
            "subQuestionCount": 10,
            "labels": ["记叙文", "成长", "亲子关系"],
            "answers": [
                {"number": 1, "answer": "C"},
                {"number": 2, "answer": "A"}
            ]
        },
        {
            "section": "第一部分 知识运用",
            "subsection": "第二节",
            "questionNumber": "语法填空A",
            "articleContent": "LaTeX格式的语法填空短文A，空格用\\clozeblank{序号}表示...",
            "questionContent": "",
            "subQuestionCount": 3,
            "labels": ["传统文化", "少数民族"],
            "answers": [
                {"number": 11, "answer": "would become"},
                {"number": 12, "answer": "participated"}
            ]
        },
        {
            "section": "第二部分 阅读理解",
            "subsection": "第一节",
            "questionNumber": "A",
            "articleContent": "LaTeX格式的阅读文章原文...",
            "questionContent": "LaTeX格式的题目，如：\\textbf{21.} Why is UNESCO calling for case studies?\\n\\optiontwo{To protect cultural heritage}{To promote tourism}{To study climate change}{To develop new technology}（注意：不包含A.B.C.D.前缀）",
            "subQuestionCount": 3,
            "labels": ["环境", "文化遗产", "说明文"],
            "answers": [
                {"number": 21, "answer": "B"},
                {"number": 22, "answer": "A"}
            ]
        },
        {
            "section": "第二部分 阅读理解",
            "subsection": "第二节",
            "questionNumber": "七选五",
            "articleContent": "LaTeX格式的七选五文章，空格用\\clozeblank{序号}表示...",
            "questionContent": "LaTeX格式的7个选项列表，使用enumerate环境...",
            "subQuestionCount": 5,
            "labels": ["人际关系", "心理学"],
            "answers": [
                {"number": 35, "answer": "F"},
                {"number": 36, "answer": "A"}
            ]
        },
        {
            "section": "第三部分 书面表达",
            "subsection": "第一节",
            "questionNumber": "阅读表达",
            "articleContent": "LaTeX格式的阅读材料...",
            "questionContent": "LaTeX格式的问答题，如：\\textbf{40.} What caused Amelia's silly behaviours?",
            "subQuestionCount": 4,
            "labels": ["记叙文", "代际沟通"],
            "answers": [
                {"number": 40, "answer": "Her literal interpretation of language."}
            ]
        },
        {
            "section": "第三部分 书面表达",
            "subsection": "第二节",
            "questionNumber": "作文",
            "articleContent": "",
            "questionContent": "LaTeX格式的作文题目要求...",
            "subQuestionCount": 1,
            "labels": ["应用文", "书信"],
            "answers": []
        }
    ]
}
```

## LaTeX格式规范

请使用以下LaTeX命令格式化题目内容：

### 选择题选项格式
- `\option{A}{B}{C}{D}` - 四栏排版（选项较短时使用）
- `\optiontwo{A}{B}{C}{D}` - 两栏排版（选项中等长度）
- `\optionone{A}{B}{C}{D}` - 单栏排版（选项较长时使用）
- **重要**：选项内容**不要**包含 A.、B.、C.、D. 前缀，LaTeX命令会自动添加编号
- **示例**：原文是 "A. apple  B. banana  C. orange  D. grape"，应写为 `\option{apple}{banana}{orange}{grape}`

### 填空题格式
- `\clozeblank{序号}` - 完形填空/语法填空空格
- `\myblank[宽度]` - 一般填空下划线，如 `\myblank[1.5cm]`
- **重要**：将原文中的连续下划线（如 `______`、`___`、`____` 等）转换为 `\myblank[1.5cm]` 命令
- **重要**：不要在LaTeX输出中使用原始下划线字符 `_`，必须用 `\myblank` 或 `\clozeblank` 替代

### 文本格式
- `\textbf{1.}` - 题号加粗
- `\textit{斜体文字}` - 斜体
- `\uwave{下划波浪线}` - 波浪下划线
- **重要**：如果文本中包含下划线字符 `_`，且不是填空，则必须转义为 `\_`
- **重要**：如果文本中包含百分号 `%`，必须转义为 `\%`（LaTeX中 `%` 是注释符号）

### 列表格式
- 使用 `\begin{enumerate}[label=\Alph{*}.]...\end{enumerate}` 格式化选项列表
- 使用 `\begin{itemize}...\end{itemize}` 格式化无序列表

### 标题格式
- `\centerline{\textbf{A}}` - 居中的篇章标记

### 段落格式（非常重要！）
LaTeX中的段落分隔与换行有严格区分：

**段落分隔（新段落）：**
- 使用**两个换行符**（空行）来分隔段落：`段落1内容\\n\\n段落2内容`
- 段落之间会有明显的缩进和间距
- **适用场景**：文章的不同段落、题目之间的分隔

**普通换行（同一段落内）：**
- 使用 `\\\\` 命令实现强制换行但保持在同一段落内
- 或者使用 `\\newline` 命令
- **适用场景**：同一段落内需要换行但不开始新段落

**错误示例（所有换行都变成段落）：**
```
段落1第一句。
段落1第二句。
段落1第三句。
```
这样会被LaTeX渲染为3个独立段落（每个都有首行缩进）。

**正确示例（保持段落结构）：**
```
段落1第一句。\\\\段落1第二句。\\\\段落1第三句。

段落2第一句。\\\\段落2第二句。

段落3内容。
```

**重要提示**：
1. 当原文是**同一段落的多行文本**时，句子之间用 `\\\\` 连接（不要用 `\\n`）
2. 当原文是**不同段落**时，段落之间用 `\\n\\n` 分隔（空行）
3. 识别段落的依据：原文中有明显的段落缩进、空行、段落间距等视觉标志
4. 英文文章通常：首行缩进或段落间有空行 = 新段落；纯粹换行继续写 = 同段落强制换行

## 提取要求

1. **识别试卷来源和年份**：从试卷标题或页眉提取
2. **section**：必须是"第一部分 知识运用"、"第二部分 阅读理解"或"第三部分 书面表达"之一
3. **subsection**：必须是"第一节"或"第二节"
4. **questionNumber字段**：
   - 阅读理解第一节：A、B、C、D
   - 完形填空：完形填空
   - 语法填空：语法填空A、语法填空B、语法填空C（如有多篇短文）
   - 七选五：七选五
   - 阅读表达：阅读表达
   - 作文：作文
5. **articleContent**：文章/短文原文（LaTeX格式），作文题可为空
6. **questionContent**：题目和选项（LaTeX格式）
   - **重要**：题目内容中**可以保留题号**（如 `\textbf{21.}`），导出时系统会自动重新编号
   - 也可以不包含题号，只写题干和选项，导出时会自动添加编号
7. **subQuestionCount**：该题包含的小题数量（非常重要！用于自动编号）
8. **labels**：3-5个语义标签（主题、体裁、话题）
9. **answers**：从参考答案部分提取，number为原试卷题号，answer为答案
   - 第一部分知识运用-第一节（完形填空）：选择题答案为A/B/C/D
   - 第一部分知识运用-第二节（语法填空）：填空题答案为具体单词或短语
   - 第二部分阅读理解-第一节（阅读选择题A/B/C/D）：选择题答案为A/B/C/D
   - 第二部分阅读理解-第二节（七选五）：选择题答案为A/B/C/D/E/F/G
   - 第三部分书面表达-第一节（阅读表达）：答案为完整的英文句子或短语，直接从参考答案抄录
   - 第三部分书面表达-第二节（作文）：answers数组可为空（作文无标准答案）
   - **注意**：number 字段保留原试卷题号即可，导出时会自动重新编号

## 注意事项

- 同一道题目可能跨页，请完整提取
- 保持原文格式，不要添加或删除内容
- **正确区分段落分隔和换行**：
  - 原文中不同段落（有缩进或空行）：段落间用 `\\n\\n` 分隔
  - 原文中同一段落的多行文本：行与行之间用 `\\\\` 连接
  - 不要把每一行文本都当成独立段落！
- **将所有连续下划线（`______`、`___`等）转换为LaTeX填空命令 `\\myblank[1.5cm]`**
- **确保所有题目、文章、选项内容都使用正确的LaTeX命令格式化**
- **不要在输出中保留任何原始下划线字符串（如`______`），必须全部转换为LaTeX格式**
- 如果某部分在试卷中不存在，不要捏造，直接跳过

## 输出要求（重要）

**请直接输出纯JSON，不要使用Markdown代码块格式（不要包含```json或```）。不要添加任何解释性文字。**

### JSON格式中的LaTeX转义规则（非常重要！）

输出内容包含LaTeX命令（如\clozeblank、\textbf、\option等）。因为输出必须是有效的JSON，你**必须**对所有LaTeX命令中的反斜杠进行双重转义（使用\\\\而不是\\）。

**错误写法（会导致JSON解析失败）：**
```
"articleContent": "Hello \clozeblank{1} world"
```

**正确写法：**
```
"articleContent": "Hello \\clozeblank{1} world"
```

### 段落格式处理示例（重要！）

假设原文如下（第一段有3句话，第二段有2句话）：

```
    Mary went to the park. She saw a beautiful bird. The bird was singing.
    
    Tom joined her later. They had a great time.
```

**错误的JSON输出（每个句子都成了独立段落）：**
```json
{
    "articleContent": "Mary went to the park.\nShe saw a beautiful bird.\nThe bird was singing.\nTom joined her later.\nThey had a great time."
}
```
这样会导致5个段落，每个都有首行缩进。

**正确的JSON输出（保持原始段落结构）：**
```json
{
    "articleContent": "Mary went to the park. \\\\She saw a beautiful bird. \\\\The bird was singing.\n\nTom joined her later. \\\\They had a great time."
}
```
或者如果句子本身就在同一行，可以直接空格分隔：
```json
{
    "articleContent": "Mary went to the park. She saw a beautiful bird. The bird was singing.\n\nTom joined her later. They had a great time."
}
```

**要点**：
- 同一段落的句子：可以用空格连接（如果原文就在一行），或用 `\\\\` 强制换行
- 不同段落之间：用 `\n\n`（在JSON中直接写成字符串的换行）分隔
- 识别段落的关键：原文中是否有明显的段落缩进或空行

所有LaTeX命令都需要这样处理：
- \\clozeblank{} 
- \\textbf{}
- \\option{}
- \\optiontwo{}
- \\optionone{}
- \\myblank[]
- \\textit{}
- \\uwave{}
- \\centerline{}
- \\begin{} 和 \\end{}

**特别提醒：**
1. 原文中的 `______` 或 `___` 这样的下划线必须转换为 `\\myblank[1.5cm]`（JSON中写为 `\\\\myblank[1.5cm]`）
2. 完形填空/语法填空的编号空格必须使用 `\\clozeblank{序号}`（JSON中写为 `\\\\clozeblank{序号}`）
3. 选择题选项必须使用 `\\option{}`、`\\optiontwo{}` 或 `\\optionone{}`（JSON中写为 `\\\\option{}`等）
   - **选项内容不要包含 A.、B.、C.、D. 前缀**，LaTeX命令会自动添加编号
   - 例如：原文 "A. apple  B. banana" 应写为 `\\\\option{apple}{banana}{...}{...}`
4. 文本中的百分号 `%` 必须转义为 `\\%`（JSON中写为 `\\\\%`），因为在LaTeX中 `%` 是注释符号
5. 绝对不要在输出中保留原始下划线字符串（如 `______`）
6. **段落格式处理（关键！）**：
   - 原文不同段落之间：在JSON字符串中使用 `\\n\\n` 分隔（实际是两个换行符）
   - 原文同一段落内换行：在JSON字符串中使用 `\\\\\\\\` 分隔（JSON转义后为LaTeX的 `\\\\`）
   - 示例：`"articleContent": "段落1第一句。\\\\\\\\段落1第二句。\\n\\n段落2第一句。"`
   - 这样可以保持文章的原始段落结构，避免所有换行都变成新段落

如果无法识别为英语试卷，返回：
{"error": "无法识别为英语试卷，具体原因：..."}
'''


# Default singleton instance (uses default model from config)
pdf_import_service = PDFImportService()

