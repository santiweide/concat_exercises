"""
HTTP handlers for Authentication API endpoints.
"""
import re
from aiohttp import web
import structlog

from services.auth_service import auth_service

logger = structlog.get_logger()

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


async def send_magic_link(request: web.Request) -> web.Response:
    """
    POST /api/auth/send-magic-link
    Send a magic link to the user's email.
    """
    try:
        body = await request.json()
        email = body.get('email', '').strip().lower()
        
        # Validate email
        if not email:
            return web.json_response(
                {"code": 400, "message": "邮箱地址不能为空"},
                status=400
            )
        
        if not EMAIL_REGEX.match(email):
            return web.json_response(
                {"code": 400, "message": "邮箱地址格式不正确"},
                status=400
            )
        
        # Generate magic link token
        token = auth_service.generate_magic_token(email)
        
        # Send email (or print to console in dev mode)
        success = await auth_service.send_magic_link_email(email, token)
        
        if not success:
            return web.json_response(
                {"code": 500, "message": "发送邮件失败，请稍后重试"},
                status=500
            )
        
        return web.json_response({
            "success": True,
            "message": "登录链接已发送到您的邮箱"
        })
        
    except Exception as e:
        logger.error("send_magic_link error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def verify_magic_link(request: web.Request) -> web.Response:
    """
    POST /api/auth/verify
    Verify the magic link token and return a JWT.
    """
    try:
        body = await request.json()
        token = body.get('token', '')
        
        if not token:
            return web.json_response(
                {"code": 400, "message": "验证令牌不能为空"},
                status=400
            )
        
        # Verify magic link token
        email = auth_service.verify_magic_token(token)
        
        if not email:
            return web.json_response(
                {"code": 401, "message": "验证链接无效或已过期"},
                status=401
            )
        
        # Generate JWT
        jwt_token = auth_service.generate_jwt(email)
        
        # Get user info
        user = auth_service.get_user(email)
        
        return web.json_response({
            "success": True,
            "token": jwt_token,
            "user": user
        })
        
    except Exception as e:
        logger.error("verify_magic_link error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def get_current_user(request: web.Request) -> web.Response:
    """
    GET /api/auth/me
    Get the current authenticated user.
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {"code": 401, "message": "未登录"},
                status=401
            )
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Verify JWT
        payload = auth_service.verify_jwt(token)
        
        if not payload:
            return web.json_response(
                {"code": 401, "message": "登录已过期，请重新登录"},
                status=401
            )
        
        email = payload.get('email')
        user = auth_service.get_user(email)
        
        if not user:
            return web.json_response(
                {"code": 404, "message": "用户不存在"},
                status=404
            )
        
        return web.json_response({
            "user": user
        })
        
    except Exception as e:
        logger.error("get_current_user error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def logout(request: web.Request) -> web.Response:
    """
    POST /api/auth/logout
    Logout the current user (client-side token removal).
    """
    # JWT is stateless, so logout is handled client-side
    # This endpoint is just for consistency
    return web.json_response({
        "success": True,
        "message": "已退出登录"
    })
