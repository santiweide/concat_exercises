"""
HTTP handlers for Queue Service API endpoints.
Now uses queue_store directly instead of ZMQ for simplicity.
"""
from aiohttp import web
from urllib.parse import unquote
import structlog
from models import (
    CreateQueueRequest,
    UpdateQueueRequest,
    ExportFormat,
    PaginationResponse,
)
from storage import queue_store
from services.auth_service import auth_service

logger = structlog.get_logger()


def get_user_from_request(request: web.Request) -> dict | None:
    """Extract user info from JWT token in Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    return auth_service.verify_jwt(token)


async def list_queues(request: web.Request) -> web.Response:
    """
    GET /api/queues?page={page}&pageSize={pageSize}
    List queues for the authenticated user.
    """
    try:
        # Get user from JWT token
        user = get_user_from_request(request)
        if not user:
            return web.json_response(
                {"code": 401, "message": "Authentication required"},
                status=401
            )
        
        user_email = user.get('email', '')
        page = int(request.query.get('page', '1'))
        page_size = int(request.query.get('pageSize', '20'))
        
        queues, total = queue_store.list(user_email, page, page_size)
        pagination = PaginationResponse.create(total, page, page_size)
        
        return web.json_response({
            "queues": [q.model_dump() for q in queues],
            "pagination": pagination.model_dump()
        })
    except Exception as e:
        logger.error("list_queues error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def get_queue(request: web.Request) -> web.Response:
    """
    GET /api/queues/{id}
    Get queue details with questions.
    """
    queue_id = request.match_info['id']
    
    try:
        queue_detail = queue_store.get(queue_id)
        
        if queue_detail is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.json_response({
            "queue": queue_detail.queue.model_dump(),
            "questions": [q.model_dump() for q in queue_detail.questions]
        })
    except Exception as e:
        logger.error("get_queue error", error=str(e), id=queue_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def create_queue(request: web.Request) -> web.Response:
    """
    POST /api/queues
    Create a new queue.
    """
    try:
        # Get user from JWT token
        user = get_user_from_request(request)
        if not user:
            return web.json_response(
                {"code": 401, "message": "Authentication required"},
                status=401
            )
        
        body = await request.json()
        # Set the owner to the authenticated user
        body['owner'] = user.get('email', '')
        req = CreateQueueRequest(**body)
        
        queue = queue_store.create(req.model_dump())
        
        return web.json_response({
            "queue": queue.model_dump()
        }, status=201)
    except Exception as e:
        logger.error("create_queue error", error=str(e))
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def update_queue(request: web.Request) -> web.Response:
    """
    PATCH /api/queues/{id}
    Update queue basic info.
    """
    queue_id = request.match_info['id']
    
    try:
        body = await request.json()
        
        queue = queue_store.update(queue_id, body)
        
        if queue is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.json_response({
            "queue": queue.model_dump()
        })
    except Exception as e:
        logger.error("update_queue error", error=str(e), id=queue_id)
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def delete_queue(request: web.Request) -> web.Response:
    """
    DELETE /api/queues/{id}
    Delete a queue.
    """
    queue_id = request.match_info['id']
    
    try:
        success = queue_store.delete(queue_id)
        
        if not success:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.Response(status=204)
    except Exception as e:
        logger.error("delete_queue error", error=str(e), id=queue_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def add_question_to_queue(request: web.Request) -> web.Response:
    """
    POST /api/queues/{queue_id}/questions
    Add a question to a queue.
    """
    queue_id = request.match_info['queue_id']
    
    try:
        body = await request.json()
        question_id = body.get('questionId')
        position = body.get('position')
        
        queue = queue_store.add_question(queue_id, question_id, position)
        
        if queue is None:
            return web.json_response(
                {"code": 400, "message": "Queue not found or frozen"},
                status=400
            )
        
        return web.json_response({
            "queue": queue.model_dump()
        })
    except Exception as e:
        logger.error("add_question_to_queue error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def remove_question_from_queue(request: web.Request) -> web.Response:
    """
    DELETE /api/queues/{queue_id}/questions/{question_id}
    Remove a question from a queue.
    """
    queue_id = request.match_info['queue_id']
    question_id = request.match_info['question_id']
    
    try:
        queue = queue_store.remove_question(queue_id, question_id)
        
        if queue is None:
            return web.json_response(
                {"code": 400, "message": "Queue not found or frozen"},
                status=400
            )
        
        return web.json_response({
            "queue": queue.model_dump()
        })
    except Exception as e:
        logger.error("remove_question_from_queue error", error=str(e), 
                    queue_id=queue_id, question_id=question_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def reorder_queue_questions(request: web.Request) -> web.Response:
    """
    PUT /api/queues/{queue_id}/reorder
    Reorder questions in a queue.
    """
    queue_id = request.match_info['queue_id']
    
    try:
        body = await request.json()
        question_ids = body.get('questionIds', [])
        
        queue = queue_store.reorder_questions(queue_id, question_ids)
        
        if queue is None:
            return web.json_response(
                {"code": 400, "message": "Queue not found or frozen"},
                status=400
            )
        
        return web.json_response({
            "queue": queue.model_dump()
        })
    except Exception as e:
        logger.error("reorder_queue_questions error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def toggle_queue_freeze(request: web.Request) -> web.Response:
    """
    PUT /api/queues/{queue_id}/freeze
    Freeze or unfreeze a queue.
    """
    queue_id = request.match_info['queue_id']
    
    try:
        body = await request.json()
        frozen = body.get('frozen', False)
        
        queue = queue_store.toggle_freeze(queue_id, frozen)
        
        if queue is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.json_response({
            "queue": queue.model_dump()
        })
    except Exception as e:
        logger.error("toggle_queue_freeze error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def add_collaborator(request: web.Request) -> web.Response:
    """
    POST /api/queues/{queue_id}/collaborators
    Add a collaborator to a queue.
    """
    queue_id = request.match_info['queue_id']
    
    try:
        body = await request.json()
        email = body.get('collaboratorEmail')
        
        queue = queue_store.add_collaborator(queue_id, email)
        
        if queue is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.json_response({
            "queue": queue.model_dump()
        })
    except Exception as e:
        logger.error("add_collaborator error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def remove_collaborator(request: web.Request) -> web.Response:
    """
    DELETE /api/queues/{queue_id}/collaborators/{email}
    Remove a collaborator from a queue.
    """
    queue_id = request.match_info['queue_id']
    email = unquote(request.match_info['email'])
    
    try:
        queue = queue_store.remove_collaborator(queue_id, email)
        
        if queue is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.json_response({
            "queue": queue.model_dump()
        })
    except Exception as e:
        logger.error("remove_collaborator error", error=str(e), 
                    queue_id=queue_id, email=email)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def export_queue(request: web.Request) -> web.Response:
    """
    POST /api/queues/{queue_id}/export
    Export a queue to a file.
    """
    queue_id = request.match_info['queue_id']
    
    try:
        body = await request.json()
        format_value = body.get('format', 1)
        
        queue_detail = queue_store.get(queue_id)
        if queue_detail is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        # For JSON, return directly
        if format_value == ExportFormat.JSON:
            return web.json_response({
                "queue": queue_detail.queue.model_dump(),
                "questions": [q.model_dump() for q in queue_detail.questions]
            })
        
        # For other formats, not implemented yet
        return web.json_response(
            {"code": 501, "message": "Export format not implemented"},
            status=501
        )
        
    except Exception as e:
        logger.error("export_queue error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )
