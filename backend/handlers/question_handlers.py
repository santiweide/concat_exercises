"""
HTTP handlers for Question Service API endpoints.
"""
from aiohttp import web
import structlog
from models import (
    SearchQuestionsRequest,
    SearchQuestionsResponse,
    GetQuestionResponse,
    BatchGetQuestionsRequest,
    BatchGetQuestionsResponse,
    CreateQuestionRequest,
    CreateQuestionResponse,
    UpdateQuestionRequest,
    UpdateQuestionResponse,
    GetAllLabelsResponse,
    GetAllYearsResponse,
)
from zmq_service import question_client

logger = structlog.get_logger()


async def search_questions(request: web.Request) -> web.Response:
    """
    POST /api/questions/search
    Search questions with semantic search support.
    """
    try:
        body = await request.json()
        req = SearchQuestionsRequest(**body)
        
        result = await question_client.call("search_questions", req.model_dump())
        
        return web.json_response(result)
    except Exception as e:
        logger.error("search_questions error", error=str(e))
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def get_question(request: web.Request) -> web.Response:
    """
    GET /api/questions/{id}
    Get a single question by ID.
    """
    question_id = request.match_info['id']
    
    try:
        result = await question_client.call("get_question", {"id": question_id})
        
        if result.get("question") is None:
            return web.json_response(
                {"code": 404, "message": "Question not found"},
                status=404
            )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("get_question error", error=str(e), id=question_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def batch_get_questions(request: web.Request) -> web.Response:
    """
    POST /api/questions/batch
    Batch get questions by IDs.
    """
    try:
        body = await request.json()
        req = BatchGetQuestionsRequest(**body)
        
        result = await question_client.call("batch_get_questions", req.model_dump())
        
        return web.json_response(result)
    except Exception as e:
        logger.error("batch_get_questions error", error=str(e))
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def create_question(request: web.Request) -> web.Response:
    """
    POST /api/questions
    Create a new question.
    """
    try:
        body = await request.json()
        req = CreateQuestionRequest(**body)
        
        result = await question_client.call("create_question", req.model_dump())
        
        return web.json_response(result, status=201)
    except Exception as e:
        logger.error("create_question error", error=str(e))
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def update_question(request: web.Request) -> web.Response:
    """
    PATCH /api/questions/{id}
    Update an existing question.
    """
    question_id = request.match_info['id']
    
    try:
        body = await request.json()
        body['id'] = question_id
        req = UpdateQuestionRequest(**body)
        
        result = await question_client.call("update_question", req.model_dump(exclude_none=True))
        
        if result.get("question") is None:
            return web.json_response(
                {"code": 404, "message": "Question not found"},
                status=404
            )
        
        return web.json_response(result)
    except Exception as e:
        logger.error("update_question error", error=str(e), id=question_id)
        return web.json_response(
            {"code": 400, "message": str(e)},
            status=400
        )


async def delete_question(request: web.Request) -> web.Response:
    """
    DELETE /api/questions/{id}
    Delete a question.
    """
    question_id = request.match_info['id']
    
    try:
        await question_client.call("delete_question", {"id": question_id})
        
        return web.Response(status=204)
    except Exception as e:
        logger.error("delete_question error", error=str(e), id=question_id)
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def get_all_labels(request: web.Request) -> web.Response:
    """
    GET /api/questions/labels
    Get all available labels.
    """
    try:
        result = await question_client.call("get_all_labels", {})
        
        return web.json_response(result)
    except Exception as e:
        logger.error("get_all_labels error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )


async def get_all_years(request: web.Request) -> web.Response:
    """
    GET /api/questions/years
    Get all available years.
    """
    try:
        result = await question_client.call("get_all_years", {})
        
        return web.json_response(result)
    except Exception as e:
        logger.error("get_all_years error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )
