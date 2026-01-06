"""
Configuration settings for the Exam Paper System backend.
"""
import os
import secrets
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get_cors_origins() -> list[str]:
    """Get CORS origins from environment or defaults."""
    env_origins = os.getenv("CORS_ORIGINS")
    if env_origins:
        return [o.strip() for o in env_origins.split(",")]
    return ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]


def _get_jwt_secret() -> str:
    """Get JWT secret from environment or generate one."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        # Generate a random secret for development
        secret = secrets.token_urlsafe(32)
        print(f"⚠️  No JWT_SECRET set, using random secret (will invalidate on restart)")
    return secret


@dataclass
class Config:
    """Application configuration."""
    
    # HTTP Server
    HTTP_HOST: str = os.getenv("HTTP_HOST", "0.0.0.0")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "8080"))
    
    # Frontend URL (for magic link)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # ZeroMQ
    ZMQ_QUESTION_SERVICE_ADDR: str = os.getenv("ZMQ_QUESTION_SERVICE_ADDR", "tcp://127.0.0.1:5555")
    ZMQ_QUEUE_SERVICE_ADDR: str = os.getenv("ZMQ_QUEUE_SERVICE_ADDR", "tcp://127.0.0.1:5556")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///exam_paper.db")
    
    # CORS
    CORS_ORIGINS: list[str] = field(default_factory=_get_cors_origins)
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Authentication
    JWT_SECRET: str = field(default_factory=_get_jwt_secret)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "168"))  # 7 days
    MAGIC_LINK_EXPIRY_MINUTES: int = int(os.getenv("MAGIC_LINK_EXPIRY_MINUTES", "15"))
    
    # Email (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@exampaper.local")
    
    # Development mode (skip email, print link to console)
    DEV_MODE: bool = os.getenv("DEV_MODE", "true").lower() == "true"


config = Config()
