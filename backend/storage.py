"""
JSON file-based persistent storage.
In production, replace with a proper database.
"""
from __future__ import annotations
import json
import os
import time
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import structlog

from models import ReadingQuestion, Queue, QueueDetail, QuestionOperationLog, OperationType

logger = structlog.get_logger()

# Data directory
DATA_DIR = Path(__file__).parent / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"
QUEUES_FILE = DATA_DIR / "queues.json"
USERS_FILE = DATA_DIR / "users.json"
OPERATION_LOGS_FILE = DATA_DIR / "operation_logs.json"


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load data from JSON file."""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load JSON file", path=str(filepath), error=str(e))
        return {}


def save_json_file(filepath: Path, data: Dict[str, Any]):
    """Save data to JSON file."""
    ensure_data_dir()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error("Failed to save JSON file", path=str(filepath), error=str(e))


class QuestionStore:
    """Persistent question storage using JSON file."""
    
    def __init__(self):
        self.questions: Dict[str, ReadingQuestion] = {}
        self._load()
    
    def _load(self):
        """Load questions from file."""
        data = load_json_file(QUESTIONS_FILE)
        for qid, qdata in data.items():
            self.questions[qid] = ReadingQuestion(**qdata)
        
        logger.info("Questions loaded", count=len(self.questions))
    
    def _save(self):
        """Save questions to file."""
        data = {qid: q.model_dump() for qid, q in self.questions.items()}
        save_json_file(QUESTIONS_FILE, data)
    
    def search(self, query: str = "", year: Optional[int] = None, section: Optional[str] = None,
               subsection: Optional[str] = None, labels: List[str] = None,
               page: int = 1, page_size: int = 20, include_deleted: bool = False) -> tuple[List[ReadingQuestion], int]:
        results = list(self.questions.values())
        # Filter out deleted questions unless explicitly requested
        if not include_deleted:
            results = [q for q in results if not getattr(q, 'deleted', False)]
        if year:
            results = [q for q in results if q.year == year]
        if section:
            results = [q for q in results if getattr(q, 'section', '') == section]
        if subsection:
            results = [q for q in results if getattr(q, 'subsection', '') == subsection]
        if labels:
            results = [q for q in results if any(l in q.labels for l in labels)]
        if query:
            query_lower = query.lower()
            results = [q for q in results if 
                      query_lower in q.title.lower() or 
                      query_lower in q.articleContent.lower() or
                      query_lower in q.questionContent.lower() or
                      any(query_lower in label.lower() for label in q.labels)]
        total = len(results)
        start = (page - 1) * page_size
        results = results[start:start + page_size]
        return results, total
    
    def get(self, id: str, include_deleted: bool = False) -> Optional[ReadingQuestion]:
        question = self.questions.get(id)
        if question and not include_deleted and getattr(question, 'deleted', False):
            return None
        return question
    
    def batch_get(self, ids: List[str], include_deleted: bool = False) -> List[ReadingQuestion]:
        results = [self.questions[id] for id in ids if id in self.questions]
        if not include_deleted:
            results = [q for q in results if not getattr(q, 'deleted', False)]
        return results
    
    def create(self, data: dict) -> ReadingQuestion:
        now = int(time.time() * 1000)
        # If data already has all fields (from ReadingQuestion.model_dump()), use it directly
        # Otherwise, create with provided fields
        if 'id' in data and data['id'].startswith('q-'):
            # Already a complete question dict, just update timestamps if needed
            question_data = data.copy()
            if 'createdAt' not in question_data:
                question_data['createdAt'] = now
            if 'updatedAt' not in question_data:
                question_data['updatedAt'] = now
            question = ReadingQuestion(**question_data)
        else:
            # Create new question from partial data
            question = ReadingQuestion(
                id=f"q-{uuid.uuid4().hex[:8]}",
                title=data['title'],
                year=data['year'],
                section=data.get('section', ''),
                subsection=data.get('subsection', ''),
                questionNumber=data['questionNumber'],
                articleContent=data['articleContent'],
                questionContent=data['questionContent'],
                labels=data.get('labels', []),
                answers=data.get('answers', []),
                subQuestionCount=data.get('subQuestionCount', 0),
                createdAt=now,
                updatedAt=now
            )
        self.questions[question.id] = question
        self._save()
        return question
    
    def update(self, id: str, data: dict) -> Optional[ReadingQuestion]:
        question = self.questions.get(id)
        if not question:
            return None
        update_data = question.model_dump()
        for key, value in data.items():
            if value is not None and key != 'id':
                update_data[key] = value
        update_data['updatedAt'] = int(time.time() * 1000)
        updated = ReadingQuestion(**update_data)
        self.questions[id] = updated
        self._save()
        return updated
    
    def delete(self, id: str) -> bool:
        if id in self.questions:
            del self.questions[id]
            self._save()
            return True
        return False
    
    def soft_delete(self, id: str) -> Optional[ReadingQuestion]:
        """Soft delete a question by setting deleted flag."""
        question = self.questions.get(id)
        if not question or getattr(question, 'deleted', False):
            return None
        now = int(time.time() * 1000)
        update_data = question.model_dump()
        update_data['deleted'] = True
        update_data['deletedAt'] = now
        update_data['updatedAt'] = now
        updated = ReadingQuestion(**update_data)
        self.questions[id] = updated
        self._save()
        logger.info("Question soft deleted", id=id)
        return updated
    
    def set_queue_store(self, queue_store):
        """Set queue store reference for cleanup operations."""
        self._queue_store = queue_store
    
    def restore(self, id: str) -> Optional[ReadingQuestion]:
        """Restore a soft-deleted question."""
        question = self.questions.get(id)
        if not question or not getattr(question, 'deleted', False):
            return None
        now = int(time.time() * 1000)
        update_data = question.model_dump()
        update_data['deleted'] = False
        update_data['deletedAt'] = None
        update_data['updatedAt'] = now
        updated = ReadingQuestion(**update_data)
        self.questions[id] = updated
        self._save()
        logger.info("Question restored", id=id)
        return updated
    
    def list_deleted(self, page: int = 1, page_size: int = 20) -> tuple[List[ReadingQuestion], int]:
        """List all soft-deleted questions."""
        results = [q for q in self.questions.values() if getattr(q, 'deleted', False)]
        results.sort(key=lambda q: q.deletedAt or 0, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        results = results[start:start + page_size]
        return results, total
    
    def exists_by_title(self, title: str) -> bool:
        """Check if any non-deleted question with the given title exists."""
        for q in self.questions.values():
            # Skip deleted questions
            if getattr(q, 'deleted', False):
                continue
            if q.title == title:
                return True
        return False
    
    def delete_by_title(self, title: str) -> int:
        """Delete all non-deleted questions with the given title. Returns count of deleted questions."""
        # Only delete questions that are not already soft-deleted
        to_delete = [qid for qid, q in self.questions.items() 
                     if q.title == title and not getattr(q, 'deleted', False)]
        for qid in to_delete:
            del self.questions[qid]
        if to_delete:
            self._save()
            logger.info("Deleted questions by title", title=title, count=len(to_delete))
        return len(to_delete)
    
    def get_all_labels(self) -> List[str]:
        labels = set()
        for q in self.questions.values():
            # Skip deleted questions
            if not getattr(q, 'deleted', False):
                labels.update(q.labels)
        return sorted(list(labels))
    
    def get_all_years(self) -> List[int]:
        # Only include years from non-deleted questions
        years = set(q.year for q in self.questions.values() 
                   if not getattr(q, 'deleted', False))
        return sorted(list(years), reverse=True)


class QueueStore:
    """Persistent queue storage using JSON file."""
    
    def __init__(self, question_store: QuestionStore):
        self.queues: Dict[str, Queue] = {}
        self.question_store = question_store
        self._load()
    
    def _load(self):
        data = load_json_file(QUEUES_FILE)
        for qid, qdata in data.items():
            self.queues[qid] = Queue(**qdata)
        logger.info("Queues loaded", count=len(self.queues))
    
    def _save(self):
        data = {qid: q.model_dump() for qid, q in self.queues.items()}
        save_json_file(QUEUES_FILE, data)
    
    def list(self, user_email: str, page: int = 1, page_size: int = 20) -> tuple[List[Queue], int]:
        results = [q for q in self.queues.values() 
                  if q.owner == user_email or user_email in q.collaborators]
        results.sort(key=lambda q: q.updatedAt, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        results = results[start:start + page_size]
        return results, total
    
    def get(self, id: str) -> Optional[QueueDetail]:
        queue = self.queues.get(id)
        if not queue:
            return None
        logger.info("Loading queue", queue_id=id, question_ids=queue.questionIds, question_count=len(queue.questionIds))
        # 默认不包含已删除的题目
        questions = self.question_store.batch_get(queue.questionIds, include_deleted=False)
        logger.info("Loaded questions for queue", queue_id=id, loaded_count=len(questions), expected_count=len(queue.questionIds))
        return QueueDetail(queue=queue, questions=questions)
    
    def get_basic(self, id: str) -> Optional[Queue]:
        return self.queues.get(id)
    
    def create(self, data: dict) -> Queue:
        now = int(time.time() * 1000)
        queue = Queue(
            id=f"queue-{uuid.uuid4().hex[:8]}",
            name=data['name'],
            questionIds=[],
            frozen=False,
            owner=data['owner'],
            collaborators=[],
            createdAt=now,
            updatedAt=now
        )
        self.queues[queue.id] = queue
        self._save()
        return queue
    
    def update(self, id: str, data: dict) -> Optional[Queue]:
        queue = self.queues.get(id)
        if not queue:
            return None
        update_data = queue.model_dump()
        for key, value in data.items():
            if value is not None and key != 'id':
                update_data[key] = value
        update_data['updatedAt'] = int(time.time() * 1000)
        updated = Queue(**update_data)
        self.queues[id] = updated
        self._save()
        return updated
    
    def delete(self, id: str) -> bool:
        if id in self.queues:
            del self.queues[id]
            self._save()
            return True
        return False
    
    def add_question(self, queue_id: str, question_id: str, position: Optional[int] = None) -> Optional[Queue]:
        queue = self.queues.get(queue_id)
        if not queue:
            return None
        if question_id in queue.questionIds:
            return queue
        question_ids = list(queue.questionIds)
        if position is not None and 0 <= position <= len(question_ids):
            question_ids.insert(position, question_id)
        else:
            question_ids.append(question_id)
        return self.update(queue_id, {'questionIds': question_ids})
    
    def remove_question(self, queue_id: str, question_id: str) -> Optional[Queue]:
        queue = self.queues.get(queue_id)
        if not queue:
            return None
        question_ids = [qid for qid in queue.questionIds if qid != question_id]
        return self.update(queue_id, {'questionIds': question_ids})
    
    def reorder_questions(self, queue_id: str, question_ids: List[str]) -> Optional[Queue]:
        queue = self.queues.get(queue_id)
        if not queue:
            return None
        return self.update(queue_id, {'questionIds': question_ids})
    
    def add_collaborator(self, queue_id: str, email: str) -> Optional[Queue]:
        queue = self.queues.get(queue_id)
        if not queue:
            return None
        if email in queue.collaborators:
            return queue
        collaborators = list(queue.collaborators) + [email]
        return self.update(queue_id, {'collaborators': collaborators})
    
    def remove_collaborator(self, queue_id: str, email: str) -> Optional[Queue]:
        queue = self.queues.get(queue_id)
        if not queue:
            return None
        collaborators = [e for e in queue.collaborators if e != email]
        return self.update(queue_id, {'collaborators': collaborators})
    
    def remove_question_from_all_queues(self, question_id: str) -> int:
        """Remove a question from all queues. Returns count of queues updated."""
        count = 0
        for queue_id, queue in self.queues.items():
            if question_id in queue.questionIds:
                # Don't use remove_question as it checks frozen status
                question_ids = [qid for qid in queue.questionIds if qid != question_id]
                self.update(queue_id, {'questionIds': question_ids})
                count += 1
                logger.info("Removed question from queue", question_id=question_id, queue_id=queue_id, queue_name=queue.name)
        return count
    
    def has_access(self, queue_id: str, user_email: str) -> bool:
        queue = self.queues.get(queue_id)
        if not queue:
            return False
        return queue.owner == user_email or user_email in queue.collaborators
    
    def is_owner(self, queue_id: str, user_email: str) -> bool:
        queue = self.queues.get(queue_id)
        if not queue:
            return False
        return queue.owner == user_email


class UserStore:
    """Persistent user storage using JSON file."""
    
    def __init__(self):
        self.users: Dict[str, dict] = {}
        self._load()
    
    def _load(self):
        self.users = load_json_file(USERS_FILE)
        logger.info("Users loaded", count=len(self.users))
    
    def _save(self):
        save_json_file(USERS_FILE, self.users)
    
    def get(self, email: str) -> Optional[dict]:
        return self.users.get(email)
    
    def create_or_update(self, email: str, name: str = None) -> dict:
        now = int(time.time() * 1000)
        if email in self.users:
            self.users[email]['lastLoginAt'] = now
            if name:
                self.users[email]['name'] = name
        else:
            self.users[email] = {
                'email': email,
                'name': name or email.split('@')[0],
                'createdAt': now,
                'lastLoginAt': now
            }
        self._save()
        return self.users[email]


# Global stores
question_store = QuestionStore()
queue_store = QueueStore(question_store)
user_store = UserStore()


class OperationLogStore:
    """Persistent operation log storage using JSON file."""
    
    def __init__(self):
        self.logs: Dict[str, QuestionOperationLog] = {}
        self._load()
    
    def _load(self):
        """Load logs from file."""
        data = load_json_file(OPERATION_LOGS_FILE)
        for log_id, log_data in data.items():
            self.logs[log_id] = QuestionOperationLog(**log_data)
        logger.info("Operation logs loaded", count=len(self.logs))
    
    def _save(self):
        """Save logs to file."""
        data = {log_id: log.model_dump() for log_id, log in self.logs.items()}
        save_json_file(OPERATION_LOGS_FILE, data)
    
    def create(self, operation_type: OperationType, question: ReadingQuestion, operator_email: str) -> QuestionOperationLog:
        """Create a new operation log entry."""
        now = int(time.time() * 1000)
        log = QuestionOperationLog(
            id=f"log-{uuid.uuid4().hex[:8]}",
            operationType=operation_type,
            questionId=question.id,
            questionTitle=question.title,
            questionNumber=question.questionNumber,
            articleContent=question.articleContent,
            questionContent=question.questionContent,
            answers=question.answers,
            operatorEmail=operator_email,
            operatedAt=now
        )
        self.logs[log.id] = log
        self._save()
        logger.info("Operation log created", log_id=log.id, operation=operation_type.name, question_id=question.id)
        return log
    
    def list(self, page: int = 1, page_size: int = 20, 
             operation_type: Optional[OperationType] = None,
             question_id: Optional[str] = None,
             operator_email: Optional[str] = None) -> tuple[List[QuestionOperationLog], int]:
        """List operation logs with optional filters."""
        results = list(self.logs.values())
        
        if operation_type is not None:
            results = [log for log in results if log.operationType == operation_type]
        if question_id:
            results = [log for log in results if log.questionId == question_id]
        if operator_email:
            results = [log for log in results if log.operatorEmail == operator_email]
        
        # Sort by operation time, newest first
        results.sort(key=lambda log: log.operatedAt, reverse=True)
        
        total = len(results)
        start = (page - 1) * page_size
        results = results[start:start + page_size]
        return results, total
    
    def get(self, log_id: str) -> Optional[QuestionOperationLog]:
        """Get a single log by ID."""
        return self.logs.get(log_id)


# Initialize operation log store
operation_log_store = OperationLogStore()
