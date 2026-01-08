"""
PDF Import handlers for parsing exam papers using Gemini API.
"""
from aiohttp import web
import structlog
import tempfile
import os
from services.pdf_import_service import pdf_import_service
from services.auth_service import auth_service

logger = structlog.get_logger()


def get_user_email_from_request(request: web.Request) -> str:
    """Extract user email from Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = auth_service.verify_jwt(token)
        if payload:
            return payload.get('email', '')
    return ''


async def parse_paper(request: web.Request) -> web.Response:
    """
    POST /api/papers/parse
    Parse a PDF exam paper and return preview data without saving.
    """
    try:
        # Parse multipart form data
        reader = await request.multipart()
        
        pdf_content = None
        filename = None
        
        async for field in reader:
            if field.name == 'file':
                filename = field.filename
                pdf_content = await field.read()
                break
        
        if not pdf_content:
            return web.json_response(
                {"success": False, "message": "未找到PDF文件"},
                status=400
            )
        
        if not filename or not filename.lower().endswith('.pdf'):
            return web.json_response(
                {"success": False, "message": "请上传PDF格式文件"},
                status=400
            )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_path = tmp_file.name
        
        try:
            # Parse the PDF using Gemini AI (without saving)
            result = await pdf_import_service.parse_pdf(tmp_path, filename)
            
            if result['success']:
                return web.json_response({
                    "success": True,
                    "preview": result['preview'],
                })
            else:
                return web.json_response({
                    "success": False,
                    "message": result.get('error', '解析失败'),
                }, status=400)
                
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        logger.exception("parse_paper error", error=str(e))
        return web.json_response(
            {"success": False, "message": f"处理失败: {str(e)}"},
            status=500
        )


async def confirm_import(request: web.Request) -> web.Response:
    """
    POST /api/papers/confirm
    Confirm and save the parsed questions to database.
    """
    try:
        body = await request.json()
        
        if not body:
            return web.json_response(
                {"success": False, "message": "请求数据为空"},
                status=400
            )
        
        # Extract forceOverwrite flag from request body
        force_overwrite = body.pop('forceOverwrite', False)
        
        # Get operator email from auth token
        operator_email = get_user_email_from_request(request)
        
        # Confirm import and save to database
        result = await pdf_import_service.confirm_import(
            body, 
            force_overwrite=force_overwrite,
            operator_email=operator_email
        )
        
        if result['success']:
            return web.json_response({
                "success": True,
                "title": result['title'],
                "questionsImported": result['questionsImported'],
                "questions": result['questions'],
            })
        else:
            # Return duplicate flag if applicable
            response_data = {
                "success": False,
                "message": result.get('error', '保存失败'),
            }
            if result.get('duplicate'):
                response_data['duplicate'] = True
                response_data['error'] = result.get('error')
            return web.json_response(response_data, status=400)
            
    except Exception as e:
        logger.exception("confirm_import error", error=str(e))
        return web.json_response(
            {"success": False, "message": f"保存失败: {str(e)}"},
            status=500
        )


# Keep backward compatibility
async def import_paper(request: web.Request) -> web.Response:
    """
    POST /api/papers/import
    Legacy endpoint - redirects to parse then confirm flow.
    """
    return await parse_paper(request)
