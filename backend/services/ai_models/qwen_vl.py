"""
QwenVL AI model implementation.
"""
import httpx
import json_repair
import structlog
from typing import Optional, Dict, Any, List

from .base import AIModel, AIModelType

logger = structlog.get_logger()


class QwenVLModel(AIModel):
    """Qwen VL model for exam paper extraction using OpenAI-compatible API."""
    
    # Qwen VL model configuration
    # Using qwen-vl-max for best quality, or qwen3-vl-flash for faster response
    MODEL_NAME = "qwen-vl-max"  # Can be changed to "qwen3-vl-flash" for faster processing
    BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    
    @property
    def name(self) -> str:
        return "Qwen VL Max"
    
    @property
    def model_type(self) -> AIModelType:
        return AIModelType.QWEN_VL
    
    async def extract_from_text(self, text_content: str, filename: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Extract exam paper data from text content using Qwen VL API."""
        
        full_prompt = f"""{prompt}

试卷内容：
---
{text_content}
---
"""
        
        logger.info("Calling Qwen VL API (text mode)", 
                   filename=filename,
                   prompt_length=len(full_prompt),
                   model=self.MODEL_NAME)
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                url = f"{self.BASE_URL}/chat/completions"
                response = await client.post(
                    url,
                    json={
                        "model": self.MODEL_NAME,
                        "messages": [
                            {
                                "role": "user",
                                "content": full_prompt
                            }
                        ],
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "max_tokens": 8000,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error("Qwen VL API error", 
                                status=response.status_code, 
                                body=response.text[:500])
                    return None
                
                result = response.json()
                
                # Extract text from OpenAI-compatible response
                if 'choices' in result and len(result['choices']) > 0:
                    choice = result['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        text = choice['message']['content']
                        return self._parse_response(text)
                
                return None
                
        except httpx.TimeoutException:
            logger.error("Qwen VL API timeout")
            return None
        except Exception as e:
            logger.exception("Qwen VL API call failed", error=str(e))
            return None
    
    async def generate_text_raw(self, prompt: str, content: str) -> Optional[str]:
        """Generate raw text (non-JSON) output from Qwen VL API."""
        full_prompt = f"""{prompt}

内容：
---
{content}
---
"""
        
        logger.info("Calling Qwen VL API (raw text mode)",
                   prompt_length=len(full_prompt),
                   model=self.MODEL_NAME)
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                url = f"{self.BASE_URL}/chat/completions"
                response = await client.post(
                    url,
                    json={
                        "model": self.MODEL_NAME,
                        "messages": [
                            {
                                "role": "user",
                                "content": full_prompt
                            }
                        ],
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "max_tokens": 65536,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error("Qwen VL API error (raw text)",
                                status=response.status_code,
                                body=response.text[:500])
                    return None
                
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    choice = result['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        return choice['message']['content']
                
                return None
                
        except httpx.TimeoutException:
            logger.error("Qwen VL API timeout (raw text)")
            return None
        except Exception as e:
            logger.exception("Qwen VL API call failed (raw text)", error=str(e))
            return None
    
    async def extract_from_images(self, images_base64: List[str], filename: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Extract exam paper data from images using Qwen VL API."""
        
        full_prompt = f"""请阅读这些图片中的试卷文档内容。

📄 **重要说明**：
- 这些图片是按照PDF页面顺序排列的（第1页、第2页、第3页...共{len(images_base64)}页）
- 图片之间是连续的，题目、文章、选项可能会跨页分布
- 请特别注意相邻页面的连接处，完整提取跨页的内容
- 不要因为翻页而导致内容戛然而止

{prompt}
"""
        
        # Build content with images and text
        content = []
        
        # Add all images first
        for img_base64 in images_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
        
        # Add prompt text at the end
        content.append({
            "type": "text",
            "text": full_prompt
        })
        
        logger.info("Calling Qwen VL API (image mode)",
                   filename=filename,
                   image_count=len(images_base64),
                   model=self.MODEL_NAME)
        
        try:
            # Use longer timeout for image processing
            async with httpx.AsyncClient(timeout=600.0) as client:
                url = f"{self.BASE_URL}/chat/completions"
                response = await client.post(
                    url,
                    json={
                        "model": self.MODEL_NAME,
                        "messages": [
                            {
                                "role": "user",
                                "content": content
                            }
                        ],
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "max_tokens": 8000,
                        # Enable thinking mode for better reasoning
                        "extra_body": {
                            "enable_thinking": False,  # Disable thinking for cleaner JSON output
                        }
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error("Qwen VL API error (image mode)", 
                                status=response.status_code, 
                                body=response.text[:500])
                    return None
                
                result = response.json()
                
                # Extract text from OpenAI-compatible response
                if 'choices' in result and len(result['choices']) > 0:
                    choice = result['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        text = choice['message']['content']
                        return self._parse_response(text)
                
                return None
                
        except httpx.TimeoutException:
            logger.error("Qwen VL API timeout (image mode)")
            return None
        except Exception as e:
            logger.exception("Qwen VL API call failed (image mode)", error=str(e))
            return None
    
    def _parse_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Qwen VL response text using json_repair."""
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
                logger.warning("Qwen VL returned error", error=data['error'])
                return None
            
            return data
            
        except Exception as e:
            logger.error("Failed to parse Qwen VL response", error=str(e), text=original_text[:500])
            return None
