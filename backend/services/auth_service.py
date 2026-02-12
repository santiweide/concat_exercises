"""
Authentication service - Magic Link implementation.
"""
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional
import jwt
import structlog
from aiosmtplib import send as send_email
from email.message import EmailMessage

from config import config

logger = structlog.get_logger()


class AuthService:
    """Authentication service with Magic Link support."""
    
    def __init__(self):
        # In-memory storage for magic link tokens
        # In production, use Redis or database
        self._magic_tokens: dict[str, dict] = {}
        # User sessions (email -> user info)
        self._users: dict[str, dict] = {}
    
    def generate_magic_token(self, email: str) -> str:
        """Generate a magic link token for the given email."""
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + (config.MAGIC_LINK_EXPIRY_MINUTES * 60)
        
        self._magic_tokens[token] = {
            "email": email,
            "expires_at": expires_at,
            "used": False
        }
        
        logger.info("Magic token generated", email=email, expires_in_minutes=config.MAGIC_LINK_EXPIRY_MINUTES)
        return token
    
    def verify_magic_token(self, token: str) -> Optional[str]:
        """Verify a magic link token and return the email if valid."""
        token_data = self._magic_tokens.get(token)
        
        if not token_data:
            logger.warning("Magic token not found", token=token[:10] + "...")
            return None
        
        if token_data["used"]:
            logger.warning("Magic token already used", email=token_data["email"])
            return None
        
        if time.time() > token_data["expires_at"]:
            logger.warning("Magic token expired", email=token_data["email"])
            del self._magic_tokens[token]
            return None
        
        # Mark as used
        token_data["used"] = True
        email = token_data["email"]
        
        # Ensure user exists
        if email not in self._users:
            self._users[email] = {
                "email": email,
                "name": email.split("@")[0],
                "created_at": int(time.time() * 1000)
            }
        
        logger.info("Magic token verified", email=email)
        return email
    
    def generate_jwt(self, email: str) -> str:
        """Generate a JWT token for the authenticated user."""
        now = datetime.utcnow()
        payload = {
            "sub": email,
            "email": email,
            "iat": now,
            "exp": now + timedelta(hours=config.JWT_EXPIRY_HOURS)
        }
        
        token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
        logger.info("JWT generated", email=email, expires_in_hours=config.JWT_EXPIRY_HOURS)
        return token
    
    def verify_jwt(self, token: str) -> Optional[dict]:
        """Verify a JWT token and return the payload if valid."""
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT", error=str(e))
            return None
    
    def get_user(self, email: str) -> Optional[dict]:
        """Get user info by email."""
        return self._users.get(email)
    
    def get_magic_link_url(self, token: str, request_host: Optional[str] = None) -> str:
        """Generate the full magic link URL."""
        # Use hash-based routing for frontend
        # If request_host is provided, use it; otherwise fall back to FRONTEND_URL
        base_url = f"https://{request_host}" if request_host else config.FRONTEND_URL
        return f"{base_url}/#/auth/verify?token={token}"
    
    async def send_magic_link_email(self, email: str, token: str, request_host: Optional[str] = None) -> bool:
        """Send the magic link email."""
        magic_link = self.get_magic_link_url(token, request_host)
        
        # In dev mode, just print to console
        if config.DEV_MODE or not config.SMTP_HOST:
            print("\n" + "=" * 60)
            print("📧 MAGIC LINK (Dev Mode)")
            print("=" * 60)
            print(f"Email: {email}")
            print(f"Link:  {magic_link}")
            print(f"Token: {token}")
            print("=" * 60 + "\n")
            return True
        
        # Send actual email
        try:
            message = EmailMessage()
            message["From"] = config.SMTP_FROM
            message["To"] = email
            message["Subject"] = "登录 - 英语试题组卷系统"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
            </head>
            <body style="font-family: sans-serif; padding: 20px;">
                <h2>登录验证</h2>
                <p>您好，</p>
                <p>请点击下面的链接登录英语试题组卷系统：</p>
                <p>
                    <a href="{magic_link}" 
                       style="display: inline-block; padding: 12px 24px; 
                              background-color: #2563eb; color: white; 
                              text-decoration: none; border-radius: 6px;">
                        点击登录
                    </a>
                </p>
                <p>或复制此链接到浏览器：</p>
                <p style="color: #666; word-break: break-all;">{magic_link}</p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    此链接将在 {config.MAGIC_LINK_EXPIRY_MINUTES} 分钟后过期。<br>
                    如果您没有请求此登录链接，请忽略此邮件。
                </p>
            </body>
            </html>
            """
            
            message.set_content(f"登录链接：{magic_link}\n\n此链接将在 {config.MAGIC_LINK_EXPIRY_MINUTES} 分钟后过期。")
            message.add_alternative(html_content, subtype="html")
            
            await send_email(
                message,
                hostname=config.SMTP_HOST,
                port=config.SMTP_PORT,
                username=config.SMTP_USER,
                password=config.SMTP_PASSWORD,
                start_tls=True
            )
            
            logger.info("Magic link email sent", email=email)
            return True
            
        except Exception as e:
            logger.error("Failed to send magic link email", email=email, error=str(e))
            return False
    
    def cleanup_expired_tokens(self):
        """Remove expired magic tokens."""
        now = time.time()
        expired = [token for token, data in self._magic_tokens.items() 
                   if data["expires_at"] < now]
        for token in expired:
            del self._magic_tokens[token]
        if expired:
            logger.info("Cleaned up expired tokens", count=len(expired))


# Global auth service instance
auth_service = AuthService()
