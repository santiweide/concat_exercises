"""
HTTP handlers for Question Management API endpoints.
Handles soft delete, restore, and operation logs.
"""
from aiohttp import web
import structlog
from services.question_management_service import question_management_service
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


async def list_questions_for_management(request: web.Request) -> web.Response:
    """
    POST /api/management/questions
    List questions for management with optional filters.
    """
    try:
        body = await request.json()
        query = body.get('query', '')
        year = body.get('year')
        labels = body.get('labels', [])
        page = body.get('page', 1)
        page_size = body.get('pageSize', 20)
        include_deleted = body.get('includeDeleted', False)
        
        result = question_management_service.list_questions(
            query=query,
            year=year,
            labels=labels,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted
        )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("list_questions_for_management error", error=str(e))
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def list_deleted_questions(request: web.Request) -> web.Response:
    """
    GET /api/management/questions/deleted
    List soft-deleted questions.
    """
    try:
        page = int(request.query.get('page', 1))
        page_size = int(request.query.get('pageSize', 20))
        
        result = question_management_service.list_deleted_questions(
            page=page,
            page_size=page_size
        )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("list_deleted_questions error", error=str(e))
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def soft_delete_question(request: web.Request) -> web.Response:
    """
    DELETE /api/management/questions/{id}
    Soft delete a question.
    """
    question_id = request.match_info['id']
    operator_email = get_user_email_from_request(request)
    
    if not operator_email:
        return web.json_response(
            {"code": 401, "message": "Unauthorized"},
            status=401
        )
    
    try:
        result = question_management_service.soft_delete_question(
            question_id=question_id,
            operator_email=operator_email
        )
        
        if not result['success']:
            return web.json_response(
                {"code": 404, "message": result.get('error', 'Delete failed')},
                status=404
            )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("soft_delete_question error", error=str(e), id=question_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def batch_soft_delete_questions(request: web.Request) -> web.Response:
    """
    POST /api/management/questions/batch-delete
    Batch soft delete multiple questions.
    """
    operator_email = get_user_email_from_request(request)
    
    if not operator_email:
        return web.json_response(
            {"code": 401, "message": "Unauthorized"},
            status=401
        )
    
    try:
        body = await request.json()
        question_ids = body.get('ids', [])
        
        if not question_ids:
            return web.json_response(
                {"code": 400, "message": "No question IDs provided"},
                status=400
            )
        
        result = question_management_service.batch_soft_delete(
            question_ids=question_ids,
            operator_email=operator_email
        )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("batch_soft_delete_questions error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def restore_question(request: web.Request) -> web.Response:
    """
    POST /api/management/questions/{id}/restore
    Restore a soft-deleted question.
    """
    question_id = request.match_info['id']
    operator_email = get_user_email_from_request(request)
    
    if not operator_email:
        return web.json_response(
            {"code": 401, "message": "Unauthorized"},
            status=401
        )
    
    try:
        result = question_management_service.restore_question(
            question_id=question_id,
            operator_email=operator_email
        )
        
        if not result['success']:
            return web.json_response(
                {"code": 404, "message": result.get('error', 'Restore failed')},
                status=404
            )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("restore_question error", error=str(e), id=question_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def get_operation_logs(request: web.Request) -> web.Response:
    """
    GET /api/management/logs
    Get operation logs with optional filters.
    """
    try:
        page = int(request.query.get('page', 1))
        page_size = int(request.query.get('pageSize', 20))
        operation_type = request.query.get('operationType')
        question_id = request.query.get('questionId')
        operator_email = request.query.get('operatorEmail')
        
        op_type = int(operation_type) if operation_type else None
        
        result = question_management_service.get_operation_logs(
            page=page,
            page_size=page_size,
            operation_type=op_type,
            question_id=question_id,
            operator_email=operator_email
        )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("get_operation_logs error", error=str(e))
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )
