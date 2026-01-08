"""
aiohttp HTTP server with routing.
"""
from aiohttp import web
import aiohttp_cors
import structlog
from config import config
from handlers import question_handlers, queue_handlers, auth_handlers, pdf_handlers, management_handlers
from services.auth_service import auth_service

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
    
    # Auth Routes (no authentication required)
    app.router.add_post('/api/auth/send-magic-link', auth_handlers.send_magic_link)
    app.router.add_post('/api/auth/verify', auth_handlers.verify_magic_link)
    app.router.add_get('/api/auth/me', auth_handlers.get_current_user)
    app.router.add_post('/api/auth/logout', auth_handlers.logout)
    
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
    
    # PDF Import Routes
    app.router.add_post('/api/papers/parse', pdf_handlers.parse_paper)
    app.router.add_post('/api/papers/confirm', pdf_handlers.confirm_import)
    app.router.add_post('/api/papers/import', pdf_handlers.import_paper)  # Legacy
    
    # Question Management Routes (soft delete, restore, operation logs)
    app.router.add_post('/api/management/questions', management_handlers.list_questions_for_management)
    app.router.add_get('/api/management/questions/deleted', management_handlers.list_deleted_questions)
    app.router.add_delete('/api/management/questions/{id}', management_handlers.soft_delete_question)
    app.router.add_post('/api/management/questions/batch-delete', management_handlers.batch_soft_delete_questions)
    app.router.add_post('/api/management/questions/{id}/restore', management_handlers.restore_question)
    app.router.add_get('/api/management/logs', management_handlers.get_operation_logs)
    
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


def setup_logging():
    """Setup file-based logging with rotation."""
    import os
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Create log directory if not exists
    log_dir = config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    
    service_name = config.SERVICE_NAME
    log_file = os.path.join(log_dir, f"{service_name}.log")
    log_file_wf = os.path.join(log_dir, f"{service_name}.log.wf")
    
    # Create formatters
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler for all logs (INFO and above) -> {service_name}.log
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # File handler for warnings and errors -> {service_name}.log.wf
    wf_handler = RotatingFileHandler(
        log_file_wf,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=3,
        encoding='utf-8'
    )
    wf_handler.setLevel(logging.WARNING)
    wf_handler.setFormatter(formatter)
    root_logger.addHandler(wf_handler)
    
    # Console handler (optional, for debugging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure structlog to use stdlib logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return log_file, log_file_wf


if __name__ == "__main__":
    """Simple standalone HTTP server startup (without ZMQ services)."""
    
    # Setup file-based logging
    log_file, log_file_wf = setup_logging()
    
    logger.info("Logging initialized", 
                service=config.SERVICE_NAME,
                log_file=log_file, 
                log_file_wf=log_file_wf)
    
    app = create_app()
    logger.info("Starting HTTP server", host=config.HTTP_HOST, port=config.HTTP_PORT)
    web.run_app(app, host=config.HTTP_HOST, port=config.HTTP_PORT, print=None)
