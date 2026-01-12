"""
Question Management Service - Handles soft delete and operation logs for question bank editing.
"""
import structlog
from typing import Optional, Dict, Any, List
import time

from storage import question_store, operation_log_store, queue_store
from models import ReadingQuestion, QuestionOperationLog, OperationType

logger = structlog.get_logger()

# Constants
PHYSICAL_DELETE_DAYS = 3  # Number of days after which soft-deleted questions are physically deleted


class QuestionManagementService:
    """Service for managing question bank with soft delete and audit logs."""
    
    def list_questions(self, query: str = "", year: Optional[int] = None, 
                      labels: List[str] = None, page: int = 1, 
                      page_size: int = 20, include_deleted: bool = False) -> Dict[str, Any]:
        """
        List questions with filters.
        
        Args:
            query: Search query
            year: Filter by year
            labels: Filter by labels
            page: Page number
            page_size: Items per page
            include_deleted: Whether to include soft-deleted questions
            
        Returns:
            Dictionary with questions list and pagination info
        """
        questions, total = question_store.search(
            query=query,
            year=year,
            labels=labels,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted
        )
        
        return {
            'questions': [q.model_dump() for q in questions],
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    
    def list_deleted_questions(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        List soft-deleted questions.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            Dictionary with deleted questions list and pagination info
        """
        questions, total = question_store.list_deleted(page=page, page_size=page_size)
        
        return {
            'questions': [q.model_dump() for q in questions],
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    
    def soft_delete_question(self, question_id: str, operator_email: str) -> Dict[str, Any]:
        """
        Soft delete a question and create an operation log.
        
        Args:
            question_id: The question ID to delete
            operator_email: The email of the operator performing the delete
            
        Returns:
            Dictionary with success status and deleted question info
        """
        # Get the question first (before deletion) to log its content
        question = question_store.get(question_id)
        if not question:
            return {
                'success': False,
                'error': f'题目不存在: {question_id}'
            }
        
        # Perform soft delete
        deleted_question = question_store.soft_delete(question_id)
        if not deleted_question:
            return {
                'success': False,
                'error': '删除失败'
            }
        
        # Remove from all queues
        queues_updated = queue_store.remove_question_from_all_queues(question_id)
        logger.info("Removed question from queues", 
                   question_id=question_id, 
                   queues_count=queues_updated)
        
        # Create operation log
        log = operation_log_store.create(
            operation_type=OperationType.DELETE,
            question=question,  # Use original question data for logging
            operator_email=operator_email
        )
        
        logger.info("Question soft deleted with log", 
                   question_id=question_id, 
                   operator=operator_email,
                   log_id=log.id)
        
        return {
            'success': True,
            'question': deleted_question.model_dump(),
            'log': log.model_dump(),
            'queuesAffected': queues_updated
        }
    
    def restore_question(self, question_id: str, operator_email: str) -> Dict[str, Any]:
        """
        Restore a soft-deleted question and create an operation log.
        
        Args:
            question_id: The question ID to restore
            operator_email: The email of the operator performing the restore
            
        Returns:
            Dictionary with success status and restored question info
        """
        # Get the deleted question
        question = question_store.get(question_id, include_deleted=True)
        if not question:
            return {
                'success': False,
                'error': f'题目不存在: {question_id}'
            }
        
        if not getattr(question, 'deleted', False):
            return {
                'success': False,
                'error': '该题目未被删除'
            }
        
        # Perform restore
        restored_question = question_store.restore(question_id)
        if not restored_question:
            return {
                'success': False,
                'error': '恢复失败'
            }
        
        # Create operation log
        log = operation_log_store.create(
            operation_type=OperationType.RESTORE,
            question=restored_question,
            operator_email=operator_email
        )
        
        logger.info("Question restored with log", 
                   question_id=question_id, 
                   operator=operator_email,
                   log_id=log.id)
        
        return {
            'success': True,
            'question': restored_question.model_dump(),
            'log': log.model_dump(),
            'queuesAffected': queues_updated
        }
    
    def batch_soft_delete(self, question_ids: List[str], operator_email: str) -> Dict[str, Any]:
        """
        Soft delete multiple questions at once.
        
        Args:
            question_ids: List of question IDs to delete
            operator_email: The email of the operator
            
        Returns:
            Dictionary with success status and deleted count
        """
        deleted_count = 0
        failed_ids = []
        total_queues_affected = 0
        
        for qid in question_ids:
            result = self.soft_delete_question(qid, operator_email)
            if result['success']:
                deleted_count += 1
                total_queues_affected += result.get('queuesAffected', 0)
            else:
                failed_ids.append(qid)
        
        return {
            'success': len(failed_ids) == 0,
            'deletedCount': deleted_count,
            'failedIds': failed_ids,
            'queuesAffected': total_queues_affected
        }
    
    def get_operation_logs(self, page: int = 1, page_size: int = 20,
                          operation_type: Optional[int] = None,
                          question_id: Optional[str] = None,
                          operator_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Get operation logs with optional filters.
        
        Args:
            page: Page number
            page_size: Items per page
            operation_type: Filter by operation type (1=CREATE, 2=DELETE, 3=RESTORE)
            question_id: Filter by question ID
            operator_email: Filter by operator email
            
        Returns:
            Dictionary with logs list and pagination info
        """
        op_type = None
        if operation_type is not None:
            try:
                op_type = OperationType(operation_type)
            except ValueError:
                pass
        
        logs, total = operation_log_store.list(
            page=page,
            page_size=page_size,
            operation_type=op_type,
            question_id=question_id,
            operator_email=operator_email
        )
        
        return {
            'logs': [log.model_dump() for log in logs],
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    
    def log_question_create(self, question: ReadingQuestion, operator_email: str) -> QuestionOperationLog:
        """
        Create an operation log for a newly created question.
        
        Args:
            question: The created question
            operator_email: The email of the operator
            
        Returns:
            The created operation log
        """
        return operation_log_store.create(
            operation_type=OperationType.CREATE,
            question=question,
            operator_email=operator_email
        )
    
    def cleanup_old_deleted_questions(self) -> Dict[str, Any]:
        """
        Physically delete questions that have been soft-deleted for more than PHYSICAL_DELETE_DAYS.
        This should be called on server startup.
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            current_time = int(time.time() * 1000)  # Current time in milliseconds
            cutoff_time = current_time - (PHYSICAL_DELETE_DAYS * 24 * 60 * 60 * 1000)  # 3 days ago
            
            # Get all deleted questions
            all_questions = question_store.list_all()
            deleted_questions = [q for q in all_questions if q.deleted and q.deletedAt]
            
            # Find questions deleted more than PHYSICAL_DELETE_DAYS ago
            old_deleted = [q for q in deleted_questions if q.deletedAt < cutoff_time]
            
            if not old_deleted:
                logger.info("No old deleted questions to clean up")
                return {
                    'success': True,
                    'deletedCount': 0,
                    'questionIds': []
                }
            
            deleted_ids = []
            for question in old_deleted:
                # Physically delete the question
                if question_store.delete(question.id):
                    deleted_ids.append(question.id)
                    logger.info("Physically deleted old question", 
                              question_id=question.id,
                              deleted_at=question.deletedAt,
                              title=question.title)
            
            logger.info("Cleanup completed", 
                       total_deleted=len(deleted_ids),
                       cutoff_days=PHYSICAL_DELETE_DAYS)
            
            return {
                'success': True,
                'deletedCount': len(deleted_ids),
                'questionIds': deleted_ids
            }
            
        except Exception as e:
            logger.error("Error during cleanup of old deleted questions", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
question_management_service = QuestionManagementService()
