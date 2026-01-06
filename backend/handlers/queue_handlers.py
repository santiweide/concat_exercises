"""
HTTP handlers for Queue Service API endpoints.
"""
from aiohttp import web
from urllib.parse import unquote
import structlog
from models import (
    ListQueuesRequest,
    CreateQueueRequest,
    UpdateQueueRequest,
    AddQuestionToQueueRequest,
    ReorderQueueQuestionsRequest,
    ToggleQueueFreezeRequest,
    AddCollaboratorRequest,
    ExportQueueRequest,
    ExportFormat,
    PaginationRequest,
)
import zmq_service
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
        
        payload = {
            "userEmail": user_email,
            "pagination": {"page": page, "pageSize": page_size}
        }
        
        result = await zmq_service.queue_client.call("list_queues", payload)
        
        return web.json_response(result)
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
        result = await zmq_service.queue_client.call("get_queue", {"id": queue_id})
        
        if result.get("queue") is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.json_response(result)
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
        
        result = await zmq_service.queue_client.call("create_queue", req.model_dump())
        
        return web.json_response(result, status=201)
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
        body['id'] = queue_id
        req = UpdateQueueRequest(**body)
        
        result = await zmq_service.queue_client.call("update_queue", req.model_dump(exclude_none=True))
        
        if result.get("queue") is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )
        
        return web.json_response(result)
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
        await zmq_service.queue_client.call("delete_queue", {"id": queue_id})
        
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
        body['queueId'] = queue_id
        
        result = await zmq_service.queue_client.call("add_question_to_queue", body)
        
        return web.json_response(result)
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
        result = await zmq_service.queue_client.call("remove_question_from_queue", {
            "queueId": queue_id,
            "questionId": question_id
        })
        
        return web.json_response(result)
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
        body['queueId'] = queue_id
        
        result = await zmq_service.queue_client.call("reorder_queue_questions", body)
        
        return web.json_response(result)
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
        body['queueId'] = queue_id
        
        result = await zmq_service.queue_client.call("toggle_queue_freeze", body)
        
        return web.json_response(result)
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
        body['queueId'] = queue_id
        
        result = await zmq_service.queue_client.call("add_collaborator", body)
        
        return web.json_response(result)
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
        result = await zmq_service.queue_client.call("remove_collaborator", {
            "queueId": queue_id,
            "collaboratorEmail": email
        })
        
        return web.json_response(result)
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
        
        result = await zmq_service.queue_client.call("export_queue", {
            "queueId": queue_id,
            "format": format_value
        })
        
        # Return file as binary response
        content_type = result.get('contentType', 'application/octet-stream')
        filename = result.get('filename', 'export')
        
        # For JSON, return directly
        if format_value == ExportFormat.JSON:
            return web.json_response(result.get('data', {}))
        
        # For binary formats, return as file
        response = web.Response(
            body=bytes(result.get('data', [])),
            content_type=content_type
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error("export_queue error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )
