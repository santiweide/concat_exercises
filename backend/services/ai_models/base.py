"""
Base AI model interface for exam paper extraction.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List


class AIModelType(str, Enum):
    """Supported AI model types."""
    GEMINI = "gemini"
    QWEN_VL = "qwen-vl"


class AIModel(ABC):
    """Abstract base class for AI models used in exam paper extraction."""
    
    def __init__(self, api_key: str):
        """
        Initialize the AI model.
        
        Args:
            api_key: API key for the model service
        """
        # Strip whitespace and newlines from API key (Secret Manager may add them)
        self.api_key = api_key.strip() if api_key else ""
    
    @abstractmethod
    async def extract_from_text(self, text_content: str, filename: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Extract exam paper data from text content.
        
        Args:
            text_content: Extracted text from PDF
            filename: Original filename for reference
            prompt: Extraction prompt template
            
        Returns:
            Extracted data dictionary or None on failure
        """
        pass
    
    @abstractmethod
    async def extract_from_images(self, images_base64: List[str], filename: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Extract exam paper data from images (for scanned PDFs).
        
        Args:
            images_base64: List of base64-encoded JPEG images
            filename: Original filename for reference
            prompt: Extraction prompt template
            
        Returns:
            Extracted data dictionary or None on failure
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the display name of the model."""
        pass
    
    @property
    @abstractmethod
    def model_type(self) -> AIModelType:
        """Return the model type enum."""
        pass
