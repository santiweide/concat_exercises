"""
Main entry point for the Exam Paper System backend.

This script can run:
1. All-in-one mode: HTTP server + ZMQ services in one process
2. Separate mode: Run individual components separately

Usage:
    # All-in-one mode (for development)
    python main.py
    
    # Run only HTTP server
    python main.py --http-only
    
    # Run only Question Service
    python main.py --question-service
    
    # Run only Queue Service
    python main.py --queue-service
"""
import asyncio
import argparse
import signal
import sys
import structlog
from aiohttp import web

from config import config
from server import create_app
from zmq_service import init_clients, close_clients, ZMQServiceServer
from services.question_service import QuestionServiceImpl
from services.queue_service import QueueServiceImpl

# Configure structlog
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
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

import logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, config.LOG_LEVEL.upper())
)

logger = structlog.get_logger()


async def run_http_server():
    """Run the HTTP server only."""
    # Initialize ZMQ clients
    await init_clients(
        config.ZMQ_QUESTION_SERVICE_ADDR,
        config.ZMQ_QUEUE_SERVICE_ADDR
    )
    
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, config.HTTP_HOST, config.HTTP_PORT)
    await site.start()
    
    logger.info(
        "HTTP server started",
        host=config.HTTP_HOST,
        port=config.HTTP_PORT,
        url=f"http://{config.HTTP_HOST}:{config.HTTP_PORT}"
    )
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()
        await close_clients()


async def run_all_in_one():
    """Run everything in one process (for development)."""
    
    # Start ZMQ services
    question_server = ZMQServiceServer(
        address=config.ZMQ_QUESTION_SERVICE_ADDR,
        name="question-service"
    )
    QuestionServiceImpl(question_server)
    
    queue_server = ZMQServiceServer(
        address=config.ZMQ_QUEUE_SERVICE_ADDR,
        name="queue-service"
    )
    QueueServiceImpl(queue_server)
    
    # Start services in background
    question_task = asyncio.create_task(question_server.start())
    queue_task = asyncio.create_task(queue_server.start())
    
    # Wait a moment for services to start
    await asyncio.sleep(0.5)
    
    # Initialize ZMQ clients for HTTP server
    await init_clients(
        config.ZMQ_QUESTION_SERVICE_ADDR,
        config.ZMQ_QUEUE_SERVICE_ADDR
    )
    
    # Start HTTP server
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, config.HTTP_HOST, config.HTTP_PORT)
    await site.start()
    
    logger.info(
        "All-in-one server started",
        http_url=f"http://{config.HTTP_HOST}:{config.HTTP_PORT}",
        question_service=config.ZMQ_QUESTION_SERVICE_ADDR,
        queue_service=config.ZMQ_QUEUE_SERVICE_ADDR
    )
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           Exam Paper System Backend Started                  ║
╠══════════════════════════════════════════════════════════════╣
║  HTTP API:        http://{config.HTTP_HOST}:{config.HTTP_PORT:<24}║
║  Question Service:{config.ZMQ_QUESTION_SERVICE_ADDR:<30}║
║  Queue Service:   {config.ZMQ_QUEUE_SERVICE_ADDR:<30}║
╠══════════════════════════════════════════════════════════════╣
║  Health Check:    http://{config.HTTP_HOST}:{config.HTTP_PORT}/health             ║
║  API Docs:        See idl/API.md                             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Handle shutdown
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Wait for shutdown
    await stop_event.wait()
    
    # Cleanup
    logger.info("Shutting down...")
    await runner.cleanup()
    await close_clients()
    await question_server.stop()
    await queue_server.stop()
    question_task.cancel()
    queue_task.cancel()
    
    logger.info("Shutdown complete")


async def run_question_service():
    """Run only the question service."""
    from services.question_service import run_question_service as run_svc
    await run_svc()


async def run_queue_service():
    """Run only the queue service."""
    from services.queue_service import run_queue_service as run_svc
    await run_svc()


def main():
    parser = argparse.ArgumentParser(description="Exam Paper System Backend")
    parser.add_argument("--http-only", action="store_true", help="Run only HTTP server")
    parser.add_argument("--question-service", action="store_true", help="Run only Question Service")
    parser.add_argument("--queue-service", action="store_true", help="Run only Queue Service")
    
    args = parser.parse_args()
    
    try:
        if args.http_only:
            asyncio.run(run_http_server())
        elif args.question_service:
            asyncio.run(run_question_service())
        elif args.queue_service:
            asyncio.run(run_queue_service())
        else:
            # All-in-one mode
            asyncio.run(run_all_in_one())
    except KeyboardInterrupt:
        logger.info("Interrupted")


if __name__ == "__main__":
    main()
