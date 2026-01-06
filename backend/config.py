"""
Configuration settings for the Exam Paper System backend.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration."""
    
    # HTTP Server
    HTTP_HOST: str = os.getenv("HTTP_HOST", "0.0.0.0")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "8080"))
    
    # ZeroMQ
    ZMQ_QUESTION_SERVICE_ADDR: str = os.getenv("ZMQ_QUESTION_SERVICE_ADDR", "tcp://127.0.0.1:5555")
    ZMQ_QUEUE_SERVICE_ADDR: str = os.getenv("ZMQ_QUEUE_SERVICE_ADDR", "tcp://127.0.0.1:5556")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///exam_paper.db")
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
