"""
Gemini AI model implementation.
"""
import httpx
import json_repair
import structlog
import re
import sys
from typing import Optional, Dict, Any, List

from .base import AIModel, AIModelType

logger = structlog.get_logger()


def clean_url_string(s: str) -> str:
    """Remove all non-printable ASCII characters from a string."""
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
    return cleaned


class GeminiModel(AIModel):
    """Gemini AI model for exam paper extraction."""
    
    # Use gemini-2.0-flash for faster processing
    TEXT_MODEL = "gemini-2.0-flash"
    IMAGE_MODEL = "gemini-2.0-flash"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, api_key: str):
        """Initialize Gemini model with API key."""
        super().__init__(api_key)
    
    @property
    def name(self) -> str:
        return "Google Gemini 2.0 Flash"
    
    @property
    def model_type(self) -> AIModelType:
        return AIModelType.GEMINI
    
    async def extract_from_text(self, text_content: str, filename: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Extract exam paper data from text content using Gemini API."""
        
        full_prompt = f"""{prompt}

试卷内容：
---
{text_content}
---
"""
        
        logger.info("Calling Gemini API (text mode)", 
                   filename=filename,
                   prompt_length=len(full_prompt),
                   model=self.TEXT_MODEL)
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Clean API key - remove ALL non-printable characters
                cleaned_api_key = clean_url_string(self.api_key)
                base_url = clean_url_string(self.BASE_URL)
                model_name = clean_url_string(self.TEXT_MODEL)
                url = f"{base_url}/{model_name}:generateContent?key={cleaned_api_key}"
                
                response = await client.post(
                    url,
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {
                                        "text": full_prompt
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
                        return self._parse_response(text)
                
                return None
                
        except httpx.TimeoutException:
            logger.error("Gemini API timeout")
            return None
        except Exception as e:
            logger.exception("Gemini API call failed", error=str(e))
            return None
    
    async def extract_from_images(self, images_base64: List[str], filename: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Extract exam paper data from images using Gemini API."""
        
        full_prompt = f"""请阅读这些图片中的试卷文档内容。

{prompt}
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
            "text": full_prompt
        })
        
        logger.info("Calling Gemini API (image mode)",
                   filename=filename,
                   image_count=len(images_base64),
                   model=self.IMAGE_MODEL)
        
        try:
            # Use longer timeout for image processing
            async with httpx.AsyncClient(timeout=600.0) as client:
                url = f"{self.BASE_URL}/{self.IMAGE_MODEL}:generateContent?key={self.api_key}"
                
                response = await client.post(
                    url,
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
                        return self._parse_response(text)
                
                return None
                
        except httpx.TimeoutException:
            logger.error("Gemini API timeout (image mode)")
            return None
        except Exception as e:
            logger.exception("Gemini API call failed (image mode)", error=str(e))
            return None
    
    def _parse_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Gemini response text using json_repair."""
        try:
            original_text = text
            
            # Try to extract JSON from markdown code blocks
            if '```json' in text:
                start = text.find('```json') + 7
                end = text.find('```', start)
                if end > start:
                    text = text[start:end].strip()
                else:
                    text = text[start:].strip()
                    if text.endswith('```'):
                        text = text[:-3].strip()
            elif '```' in text:
                start = text.find('```') + 3
                newline_pos = text.find('\n', start)
                if newline_pos != -1 and newline_pos - start < 20:
                    start = newline_pos + 1
                end = text.find('```', start)
                if end > start:
                    text = text[start:end].strip()
                else:
                    text = text[start:].strip()
                    if text.endswith('```'):
                        text = text[:-3].strip()
            
            # Additional cleanup
            text = text.strip('`').strip()
            
            if not text.startswith('{'):
                json_start = text.find('{')
                if json_start != -1:
                    text = text[json_start:]
            
            if not text.endswith('}'):
                last_brace = text.rfind('}')
                if last_brace != -1:
                    text = text[:last_brace + 1]
            
            # Use json_repair to handle broken JSON
            data = json_repair.loads(text)
            
            # Check for error response
            if 'error' in data:
                logger.error("Gemini returned error", error=data['error'])
                return None
            
            return data
            
        except Exception as e:
            logger.error("Failed to parse Gemini response", error=str(e), text=original_text[:500])
            return None
