"""
Question Management Service - Handles soft delete and operation logs for question bank editing.
"""
import structlog
from typing import Optional, Dict, Any, List

from storage import question_store, operation_log_store
from models import ReadingQuestion, QuestionOperationLog, OperationType

logger = structlog.get_logger()


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
            'log': log.model_dump()
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
            'log': log.model_dump()
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
        
        for qid in question_ids:
            result = self.soft_delete_question(qid, operator_email)
            if result['success']:
                deleted_count += 1
            else:
                failed_ids.append(qid)
        
        return {
            'success': len(failed_ids) == 0,
            'deletedCount': deleted_count,
            'failedIds': failed_ids
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


# Singleton instance
question_management_service = QuestionManagementService()
