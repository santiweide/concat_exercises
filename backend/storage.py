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

from models import ReadingQuestion, Queue, QueueDetail

logger = structlog.get_logger()

# Data directory
DATA_DIR = Path(__file__).parent / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"
QUEUES_FILE = DATA_DIR / "queues.json"
USERS_FILE = DATA_DIR / "users.json"


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
        
        if not self.questions:
            self._init_mock_data()
            self._save()
        
        logger.info("Questions loaded", count=len(self.questions))
    
    def _save(self):
        """Save questions to file."""
        data = {qid: q.model_dump() for qid, q in self.questions.items()}
        save_json_file(QUESTIONS_FILE, data)
    
    def _init_mock_data(self):
        """Initialize with mock data for testing."""
        mock_questions = [
            ReadingQuestion(
                id="q-001",
                title="2023年全国卷I",
                year=2023,
                questionNumber="A",
                articleContent="In recent years, artificial intelligence has made remarkable progress...",
                questionContent="1. What is the main idea of the passage?\nA. AI development\nB. Technology history\nC. Future predictions\nD. Scientific research",
                labels=["科技", "人工智能"],
                createdAt=1704067200000,
                updatedAt=1704067200000
            ),
            ReadingQuestion(
                id="q-002",
                title="2023年全国卷I",
                year=2023,
                questionNumber="B",
                articleContent="Climate change has become one of the most pressing issues of our time...",
                questionContent="1. According to the passage, what is the main cause of climate change?\nA. Natural cycles\nB. Human activities\nC. Solar radiation\nD. Volcanic eruptions",
                labels=["环境", "气候"],
                createdAt=1704067200000,
                updatedAt=1704067200000
            ),
            ReadingQuestion(
                id="q-003",
                title="2022年全国卷II",
                year=2022,
                questionNumber="C",
                articleContent="The history of tea dates back thousands of years to ancient China...",
                questionContent="1. When did tea first become popular outside of China?\nA. 16th century\nB. 17th century\nC. 18th century\nD. 19th century",
                labels=["文化", "历史"],
                createdAt=1704067200000,
                updatedAt=1704067200000
            ),
            ReadingQuestion(
                id="q-004",
                title="2022年全国卷II",
                year=2022,
                questionNumber="D",
                articleContent="The global economy has undergone significant changes in the past decade...",
                questionContent="1. What factor contributed most to economic growth?\nA. Technology innovation\nB. Trade agreements\nC. Government policies\nD. Consumer spending",
                labels=["经济", "社会"],
                createdAt=1704067200000,
                updatedAt=1704067200000
            ),
            ReadingQuestion(
                id="q-005",
                title="2021年全国卷I",
                year=2021,
                questionNumber="A",
                articleContent="Space exploration has entered a new era with private companies leading the way...",
                questionContent="1. What makes the new era of space exploration different?\nA. Government funding\nB. Private investment\nC. International cooperation\nD. Scientific discoveries",
                labels=["科技", "航天"],
                createdAt=1704067200000,
                updatedAt=1704067200000
            ),
        ]
        for q in mock_questions:
            self.questions[q.id] = q
    
    def search(self, query: str = "", year: Optional[int] = None, labels: List[str] = None,
               page: int = 1, page_size: int = 20) -> tuple[List[ReadingQuestion], int]:
        results = list(self.questions.values())
        if year:
            results = [q for q in results if q.year == year]
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
    
    def get(self, id: str) -> Optional[ReadingQuestion]:
        return self.questions.get(id)
    
    def batch_get(self, ids: List[str]) -> List[ReadingQuestion]:
        return [self.questions[id] for id in ids if id in self.questions]
    
    def create(self, data: dict) -> ReadingQuestion:
        now = int(time.time() * 1000)
        question = ReadingQuestion(
            id=f"q-{uuid.uuid4().hex[:8]}",
            title=data['title'],
            year=data['year'],
            questionNumber=data['questionNumber'],
            articleContent=data['articleContent'],
            questionContent=data['questionContent'],
            labels=data.get('labels', []),
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
    
    def exists_by_title(self, title: str) -> bool:
        """Check if any question with the given title exists."""
        for q in self.questions.values():
            if q.title == title:
                return True
        return False
    
    def delete_by_title(self, title: str) -> int:
        """Delete all questions with the given title. Returns count of deleted questions."""
        to_delete = [qid for qid, q in self.questions.items() if q.title == title]
        for qid in to_delete:
            del self.questions[qid]
        if to_delete:
            self._save()
            logger.info("Deleted questions by title", title=title, count=len(to_delete))
        return len(to_delete)
    
    def get_all_labels(self) -> List[str]:
        labels = set()
        for q in self.questions.values():
            labels.update(q.labels)
        return sorted(list(labels))
    
    def get_all_years(self) -> List[int]:
        years = set(q.year for q in self.questions.values())
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
        if not self.queues:
            self._init_mock_data()
            self._save()
        logger.info("Queues loaded", count=len(self.queues))
    
    def _save(self):
        data = {qid: q.model_dump() for qid, q in self.queues.items()}
        save_json_file(QUEUES_FILE, data)
    
    def _init_mock_data(self):
        mock_queues = [
            Queue(
                id="queue-001",
                name="2024高考模拟卷1",
                questionIds=["q-001", "q-002"],
                frozen=False,
                owner="user@example.com",
                collaborators=["other@example.com"],
                createdAt=1704067200000,
                updatedAt=1704067200000
            ),
            Queue(
                id="queue-002",
                name="科技类专题练习",
                questionIds=["q-001", "q-005"],
                frozen=False,
                owner="user@example.com",
                collaborators=[],
                createdAt=1704067200000,
                updatedAt=1704067200000
            ),
        ]
        for q in mock_queues:
            self.queues[q.id] = q
    
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
        questions = self.question_store.batch_get(queue.questionIds)
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
        if not queue or queue.frozen:
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
        if not queue or queue.frozen:
            return None
        question_ids = [qid for qid in queue.questionIds if qid != question_id]
        return self.update(queue_id, {'questionIds': question_ids})
    
    def reorder_questions(self, queue_id: str, question_ids: List[str]) -> Optional[Queue]:
        queue = self.queues.get(queue_id)
        if not queue or queue.frozen:
            return None
        return self.update(queue_id, {'questionIds': question_ids})
    
    def toggle_freeze(self, queue_id: str, frozen: bool) -> Optional[Queue]:
        return self.update(queue_id, {'frozen': frozen})
    
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
