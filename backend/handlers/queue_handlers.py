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
    PaginationResponse,
)
from storage import queue_store
from services.auth_service import auth_service
from services.latex_export_service import latex_export_service
from services.latex_proofread_service import latex_proofread_service

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
            "queue": {
                "queue": queue_detail.queue.model_dump(),
                "questions": [q.model_dump() for q in queue_detail.questions]
            }
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


async def proofread_queue(request: web.Request) -> web.Response:
    """
    POST /api/queues/{queue_id}/proofread
    Generate LaTeX for a queue then proofread it using AI against the format RFC.
    Optional body: {"model": "gemini", "autoFix": false}
    """
    queue_id = request.match_info['queue_id']

    try:
        body = await request.json() if request.can_read_body else {}
        model_type = body.get('model', None)
        auto_fix = body.get('autoFix', False)

        # 1. Get queue data
        queue_detail = queue_store.get(queue_id)
        if queue_detail is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )

        # 2. Generate LaTeX
        latex_content = latex_export_service.export_queue_to_latex(queue_detail)

        # 3. Proofread with AI
        if auto_fix:
            result = await latex_proofread_service.proofread_and_fix(
                latex_content, model_type
            )
        else:
            result = await latex_proofread_service.proofread_latex(
                latex_content, model_type
            )

        return web.json_response(result)

    except Exception as e:
        logger.error("proofread_queue error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 500, "message": f"校对失败: {str(e)}"},
            status=500
        )


async def generate_fixed_latex(request: web.Request) -> web.Response:
    """
    POST /api/queues/{queue_id}/proofread/fix
    Generate a corrected LaTeX file based on proofread results.
    Body: {"proofreadResult": {...}, "model": "gemini"}
    """
    queue_id = request.match_info['queue_id']

    try:
        body = await request.json()
        proofread_result = body.get('proofreadResult', {})
        model_type = body.get('model', None)

        if not proofread_result or not proofread_result.get('issues'):
            return web.json_response(
                {"success": False, "error": "缺少校对结果数据"},
                status=400
            )

        # 1. Get queue data
        queue_detail = queue_store.get(queue_id)
        if queue_detail is None:
            return web.json_response(
                {"code": 404, "message": "Queue not found"},
                status=404
            )

        # 2. Generate original LaTeX
        latex_content = latex_export_service.export_queue_to_latex(queue_detail)

        # 3. Use AI to generate corrected LaTeX
        result = await latex_proofread_service.generate_fixed_latex(
            latex_content, proofread_result, model_type
        )

        return web.json_response(result)

    except Exception as e:
        logger.error("generate_fixed_latex error", error=str(e), queue_id=queue_id)
        return web.json_response(
            {"code": 500, "message": f"生成修正版失败: {str(e)}"},
            status=500
        )
