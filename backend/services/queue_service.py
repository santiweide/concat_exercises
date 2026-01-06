"""
Queue Service - ZeroMQ backend service.
Handles all queue-related business logic.
"""
import asyncio
import json
import structlog
from zmq_service import ZMQServiceServer
from storage import queue_store
from models import PaginationResponse, ExportFormat
from config import config

logger = structlog.get_logger()


class QueueServiceImpl:
    """Queue service implementation."""
    
    def __init__(self, server: ZMQServiceServer):
        self.server = server
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all handlers."""
        self.server.register("list_queues", self.list_queues)
        self.server.register("get_queue", self.get_queue)
        self.server.register("create_queue", self.create_queue)
        self.server.register("update_queue", self.update_queue)
        self.server.register("delete_queue", self.delete_queue)
        self.server.register("add_question_to_queue", self.add_question_to_queue)
        self.server.register("remove_question_from_queue", self.remove_question_from_queue)
        self.server.register("reorder_queue_questions", self.reorder_queue_questions)
        self.server.register("toggle_queue_freeze", self.toggle_queue_freeze)
        self.server.register("add_collaborator", self.add_collaborator)
        self.server.register("remove_collaborator", self.remove_collaborator)
        self.server.register("export_queue", self.export_queue)
    
    async def list_queues(self, payload: dict) -> dict:
        """List queues for a user."""
        user_email = payload.get('userEmail', '')
        pagination = payload.get('pagination', {})
        page = pagination.get('page', 1)
        page_size = pagination.get('pageSize', 20)
        
        queues, total = queue_store.list(
            user_email=user_email,
            page=page,
            page_size=page_size
        )
        
        pagination_response = PaginationResponse.create(total, page, page_size)
        
        return {
            "queues": [q.model_dump() for q in queues],
            "pagination": pagination_response.model_dump()
        }
    
    async def get_queue(self, payload: dict) -> dict:
        """Get queue details with questions."""
        queue_id = payload.get('id')
        queue_detail = queue_store.get(queue_id)
        
        if queue_detail:
            return {
                "queue": {
                    "queue": queue_detail.queue.model_dump(),
                    "questions": [q.model_dump() for q in queue_detail.questions]
                }
            }
        return {"queue": None}
    
    async def create_queue(self, payload: dict) -> dict:
        """Create a new queue."""
        queue = queue_store.create(payload)
        
        return {
            "queue": queue.model_dump()
        }
    
    async def update_queue(self, payload: dict) -> dict:
        """Update queue basic info."""
        queue_id = payload.get('id')
        queue = queue_store.update(queue_id, payload)
        
        return {
            "queue": queue.model_dump() if queue else None
        }
    
    async def delete_queue(self, payload: dict) -> dict:
        """Delete a queue."""
        queue_id = payload.get('id')
        success = queue_store.delete(queue_id)
        
        return {"success": success}
    
    async def add_question_to_queue(self, payload: dict) -> dict:
        """Add a question to a queue."""
        queue_id = payload.get('queueId')
        question_id = payload.get('questionId')
        position = payload.get('position')
        
        queue = queue_store.add_question(queue_id, question_id, position)
        
        return {
            "queue": queue.model_dump() if queue else None
        }
    
    async def remove_question_from_queue(self, payload: dict) -> dict:
        """Remove a question from a queue."""
        queue_id = payload.get('queueId')
        question_id = payload.get('questionId')
        
        queue = queue_store.remove_question(queue_id, question_id)
        
        return {
            "queue": queue.model_dump() if queue else None
        }
    
    async def reorder_queue_questions(self, payload: dict) -> dict:
        """Reorder questions in a queue."""
        queue_id = payload.get('queueId')
        question_ids = payload.get('questionIds', [])
        
        queue = queue_store.reorder_questions(queue_id, question_ids)
        
        return {
            "queue": queue.model_dump() if queue else None
        }
    
    async def toggle_queue_freeze(self, payload: dict) -> dict:
        """Freeze or unfreeze a queue."""
        queue_id = payload.get('queueId')
        frozen = payload.get('frozen', False)
        
        queue = queue_store.toggle_freeze(queue_id, frozen)
        
        return {
            "queue": queue.model_dump() if queue else None
        }
    
    async def add_collaborator(self, payload: dict) -> dict:
        """Add a collaborator to a queue."""
        queue_id = payload.get('queueId')
        email = payload.get('collaboratorEmail')
        
        queue = queue_store.add_collaborator(queue_id, email)
        
        return {
            "queue": queue.model_dump() if queue else None
        }
    
    async def remove_collaborator(self, payload: dict) -> dict:
        """Remove a collaborator from a queue."""
        queue_id = payload.get('queueId')
        email = payload.get('collaboratorEmail')
        
        queue = queue_store.remove_collaborator(queue_id, email)
        
        return {
            "queue": queue.model_dump() if queue else None
        }
    
    async def export_queue(self, payload: dict) -> dict:
        """Export a queue."""
        queue_id = payload.get('queueId')
        format_type = payload.get('format', ExportFormat.JSON)
        
        queue_detail = queue_store.get(queue_id)
        if not queue_detail:
            raise ValueError("Queue not found")
        
        if format_type == ExportFormat.JSON:
            data = {
                "queue": queue_detail.queue.model_dump(),
                "questions": [q.model_dump() for q in queue_detail.questions]
            }
            return {
                "data": data,
                "filename": f"{queue_detail.queue.name}.json",
                "contentType": "application/json"
            }
        elif format_type == ExportFormat.PDF:
            # TODO: Implement PDF export
            return {
                "data": [],
                "filename": f"{queue_detail.queue.name}.pdf",
                "contentType": "application/pdf"
            }
        elif format_type == ExportFormat.WORD:
            # TODO: Implement Word export
            return {
                "data": [],
                "filename": f"{queue_detail.queue.name}.docx",
                "contentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


async def run_queue_service():
    """Run the queue service."""
    server = ZMQServiceServer(
        address=config.ZMQ_QUEUE_SERVICE_ADDR,
        name="queue-service"
    )
    
    service = QueueServiceImpl(server)
    
    logger.info("Starting Queue Service", address=config.ZMQ_QUEUE_SERVICE_ADDR)
    await server.start()


if __name__ == "__main__":
    asyncio.run(run_queue_service())
