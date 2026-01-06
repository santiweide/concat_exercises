"""
Question Service - ZeroMQ backend service.
Handles all question-related business logic.
"""
import asyncio
import structlog
from zmq_service import ZMQServiceServer
from storage import question_store
from models import PaginationResponse
from config import config

logger = structlog.get_logger()


class QuestionServiceImpl:
    """Question service implementation."""
    
    def __init__(self, server: ZMQServiceServer):
        self.server = server
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all handlers."""
        self.server.register("search_questions", self.search_questions)
        self.server.register("get_question", self.get_question)
        self.server.register("batch_get_questions", self.batch_get_questions)
        self.server.register("create_question", self.create_question)
        self.server.register("update_question", self.update_question)
        self.server.register("delete_question", self.delete_question)
        self.server.register("get_all_labels", self.get_all_labels)
        self.server.register("get_all_years", self.get_all_years)
    
    async def search_questions(self, payload: dict) -> dict:
        """Search questions."""
        query = payload.get('query', '')
        year = payload.get('year')
        labels = payload.get('labels', [])
        pagination = payload.get('pagination', {})
        page = pagination.get('page', 1)
        page_size = pagination.get('pageSize', 20)
        
        questions, total = question_store.search(
            query=query,
            year=year,
            labels=labels,
            page=page,
            page_size=page_size
        )
        
        pagination_response = PaginationResponse.create(total, page, page_size)
        
        return {
            "questions": [q.model_dump() for q in questions],
            "pagination": pagination_response.model_dump()
        }
    
    async def get_question(self, payload: dict) -> dict:
        """Get a single question."""
        question_id = payload.get('id')
        question = question_store.get(question_id)
        
        return {
            "question": question.model_dump() if question else None
        }
    
    async def batch_get_questions(self, payload: dict) -> dict:
        """Batch get questions."""
        ids = payload.get('ids', [])
        questions = question_store.batch_get(ids)
        
        return {
            "questions": [q.model_dump() for q in questions]
        }
    
    async def create_question(self, payload: dict) -> dict:
        """Create a new question."""
        question = question_store.create(payload)
        
        return {
            "question": question.model_dump()
        }
    
    async def update_question(self, payload: dict) -> dict:
        """Update an existing question."""
        question_id = payload.get('id')
        question = question_store.update(question_id, payload)
        
        return {
            "question": question.model_dump() if question else None
        }
    
    async def delete_question(self, payload: dict) -> dict:
        """Delete a question."""
        question_id = payload.get('id')
        success = question_store.delete(question_id)
        
        return {"success": success}
    
    async def get_all_labels(self, payload: dict) -> dict:
        """Get all labels."""
        labels = question_store.get_all_labels()
        
        return {"labels": labels}
    
    async def get_all_years(self, payload: dict) -> dict:
        """Get all years."""
        years = question_store.get_all_years()
        
        return {"years": years}


async def run_question_service():
    """Run the question service."""
    server = ZMQServiceServer(
        address=config.ZMQ_QUESTION_SERVICE_ADDR,
        name="question-service"
    )
    
    service = QuestionServiceImpl(server)
    
    logger.info("Starting Question Service", address=config.ZMQ_QUESTION_SERVICE_ADDR)
    await server.start()


if __name__ == "__main__":
    asyncio.run(run_question_service())
