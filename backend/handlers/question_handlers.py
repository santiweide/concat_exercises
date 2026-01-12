"""
HTTP handlers for Question Service API endpoints.
Now uses question_store directly instead of ZMQ for simplicity.
"""
from aiohttp import web
import structlog
from models import (
    SearchQuestionsRequest,
    GetQuestionResponse,
    BatchGetQuestionsRequest,
    CreateQuestionRequest,
    UpdateQuestionRequest,
    PaginationResponse,
)
from storage import question_store

logger = structlog.get_logger()


async def search_questions(request: web.Request) -> web.Response:
    """
    POST /api/questions/search
    Search questions with filters.
    """
    try:
        body = await request.json()
        req = SearchQuestionsRequest(**body)
        
        # Direct call to question_store
        query = req.query or ''
        year = req.year
        section = req.section
        subsection = req.subsection
        labels = req.labels or []
        page = req.page if hasattr(req, 'page') else 1
        page_size = req.pageSize if hasattr(req, 'pageSize') else 100
        
        questions, total = question_store.search(
            query=query,
            year=year,
            section=section,
            subsection=subsection,
            labels=labels,
            page=page,
            page_size=page_size,
            include_deleted=False  # Never include deleted questions in search
        )
        
        pagination = PaginationResponse.create(total, page, page_size)
        
        return web.json_response({
            "questions": [q.model_dump() for q in questions],
            "pagination": pagination.model_dump()
        })
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
        question = question_store.get(question_id)
        
        if question is None:
            return web.json_response(
                {"code": 404, "message": "Question not found"},
                status=404
            )
        
        return web.json_response({
            "question": question.model_dump()
        })
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
        
        questions = question_store.batch_get(req.ids)
        
        return web.json_response({
            "questions": [q.model_dump() for q in questions]
        })
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
        
        question = question_store.create(req.model_dump())
        
        return web.json_response({
            "question": question.model_dump()
        }, status=201)
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
        
        question = question_store.update(question_id, body)
        
        if question is None:
            return web.json_response(
                {"code": 404, "message": "Question not found"},
                status=404
            )
        
        return web.json_response({
            "question": question.model_dump()
        })
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
        success = question_store.delete(question_id)
        
        if not success:
            return web.json_response(
                {"code": 404, "message": "Question not found"},
                status=404
            )
        
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
        labels = question_store.get_all_labels()
        
        return web.json_response({
            "labels": labels
        })
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
        years = question_store.get_all_years()
        
        return web.json_response({
            "years": years
        })
    except Exception as e:
        logger.error("get_all_years error", error=str(e))
        return web.json_response(
            {"code": 500, "message": str(e)},
            status=500
        )
