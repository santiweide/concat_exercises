"""
aiohttp HTTP server with routing.
"""
from aiohttp import web
import aiohttp_cors
import structlog
from config import config
from handlers import question_handlers, queue_handlers

logger = structlog.get_logger()


def create_app() -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()
    
    # Setup routes
    setup_routes(app)
    
    # Setup CORS
    setup_cors(app)
    
    # Setup middleware
    app.middlewares.append(error_middleware)
    app.middlewares.append(logging_middleware)
    
    return app


def setup_routes(app: web.Application):
    """Setup all API routes."""
    
    # Question Service Routes
    app.router.add_post('/api/questions/search', question_handlers.search_questions)
    app.router.add_get('/api/questions/labels', question_handlers.get_all_labels)
    app.router.add_get('/api/questions/years', question_handlers.get_all_years)
    app.router.add_post('/api/questions/batch', question_handlers.batch_get_questions)
    app.router.add_post('/api/questions', question_handlers.create_question)
    app.router.add_get('/api/questions/{id}', question_handlers.get_question)
    app.router.add_patch('/api/questions/{id}', question_handlers.update_question)
    app.router.add_delete('/api/questions/{id}', question_handlers.delete_question)
    
    # Queue Service Routes
    app.router.add_get('/api/queues', queue_handlers.list_queues)
    app.router.add_post('/api/queues', queue_handlers.create_queue)
    app.router.add_get('/api/queues/{id}', queue_handlers.get_queue)
    app.router.add_patch('/api/queues/{id}', queue_handlers.update_queue)
    app.router.add_delete('/api/queues/{id}', queue_handlers.delete_queue)
    app.router.add_post('/api/queues/{queue_id}/questions', queue_handlers.add_question_to_queue)
    app.router.add_delete('/api/queues/{queue_id}/questions/{question_id}', queue_handlers.remove_question_from_queue)
    app.router.add_put('/api/queues/{queue_id}/reorder', queue_handlers.reorder_queue_questions)
    app.router.add_put('/api/queues/{queue_id}/freeze', queue_handlers.toggle_queue_freeze)
    app.router.add_post('/api/queues/{queue_id}/collaborators', queue_handlers.add_collaborator)
    app.router.add_delete('/api/queues/{queue_id}/collaborators/{email}', queue_handlers.remove_collaborator)
    app.router.add_post('/api/queues/{queue_id}/export', queue_handlers.export_queue)
    
    # Health check
    app.router.add_get('/health', health_check)
    
    logger.info("Routes configured")


def setup_cors(app: web.Application):
    """Setup CORS for the application."""
    cors = aiohttp_cors.setup(app, defaults={
        origin: aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        )
        for origin in config.CORS_ORIGINS
    })
    
    # Apply CORS to all routes
    for route in list(app.router.routes()):
        cors.add(route)
    
    logger.info("CORS configured", origins=config.CORS_ORIGINS)


@web.middleware
async def error_middleware(request: web.Request, handler):
    """Global error handling middleware."""
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error", path=request.path, method=request.method)
        return web.json_response(
            {
                "code": 500,
                "message": "Internal server error",
                "details": {"reason": str(e)}
            },
            status=500
        )


@web.middleware
async def logging_middleware(request: web.Request, handler):
    """Request logging middleware."""
    logger.info("Request", method=request.method, path=request.path)
    response = await handler(request)
    logger.info("Response", method=request.method, path=request.path, status=response.status)
    return response


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy"})
