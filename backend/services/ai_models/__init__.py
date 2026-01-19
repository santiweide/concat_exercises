"""
AI Model abstraction layer for exam paper extraction.
"""

from .base import AIModel, AIModelType
from .gemini import GeminiModel
from .qwen_vl import QwenVLModel

__all__ = ['AIModel', 'AIModelType', 'GeminiModel', 'QwenVLModel']
