"""
In-memory storage for development/testing.
In production, replace with actual database.
"""
import time
import uuid
from typing import Optional
from models import ReadingQuestion, Queue, QueueDetail


class QuestionStore:
    """In-memory question storage."""
    
    def __init__(self):
        self.questions: dict[str, ReadingQuestion] = {}
        self._init_mock_data()
    
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
    
    def search(
        self, 
        query: str = "", 
        year: Optional[int] = None, 
        labels: list[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[ReadingQuestion], int]:
        """Search questions with filters."""
        results = list(self.questions.values())
        
        # Filter by year
        if year:
            results = [q for q in results if q.year == year]
        
        # Filter by labels
        if labels:
            results = [q for q in results if any(l in q.labels for l in labels)]
        
        # Filter by query (simple text match)
        if query:
            query_lower = query.lower()
            results = [q for q in results if 
                      query_lower in q.title.lower() or 
                      query_lower in q.articleContent.lower() or
                      query_lower in q.questionContent.lower() or
                      any(query_lower in label.lower() for label in q.labels)]
        
        total = len(results)
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        results = results[start:end]
        
        return results, total
    
    def get(self, id: str) -> Optional[ReadingQuestion]:
        """Get a question by ID."""
        return self.questions.get(id)
    
    def batch_get(self, ids: list[str]) -> list[ReadingQuestion]:
        """Get multiple questions by IDs."""
        return [self.questions[id] for id in ids if id in self.questions]
    
    def create(self, data: dict) -> ReadingQuestion:
        """Create a new question."""
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
        return question
    
    def update(self, id: str, data: dict) -> Optional[ReadingQuestion]:
        """Update an existing question."""
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
        return updated
    
    def delete(self, id: str) -> bool:
        """Delete a question."""
        if id in self.questions:
            del self.questions[id]
            return True
        return False
    
    def get_all_labels(self) -> list[str]:
        """Get all unique labels."""
        labels = set()
        for q in self.questions.values():
            labels.update(q.labels)
        return sorted(list(labels))
    
    def get_all_years(self) -> list[int]:
        """Get all unique years (descending)."""
        years = set(q.year for q in self.questions.values())
        return sorted(list(years), reverse=True)


class QueueStore:
    """In-memory queue storage."""
    
    def __init__(self, question_store: QuestionStore):
        self.queues: dict[str, Queue] = {}
        self.question_store = question_store
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize with mock data for testing."""
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
    
    def list(self, user_email: str, page: int = 1, page_size: int = 20) -> tuple[list[Queue], int]:
        """List queues for a user (as owner or collaborator)."""
        results = [q for q in self.queues.values() 
                  if q.owner == user_email or user_email in q.collaborators]
        
        total = len(results)
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        results = results[start:end]
        
        return results, total
    
    def get(self, id: str) -> Optional[QueueDetail]:
        """Get queue with full question details."""
        queue = self.queues.get(id)
        if not queue:
            return None
        
        questions = self.question_store.batch_get(queue.questionIds)
        return QueueDetail(queue=queue, questions=questions)
    
    def create(self, data: dict) -> Queue:
        """Create a new queue."""
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
        return queue
    
    def update(self, id: str, data: dict) -> Optional[Queue]:
        """Update queue basic info."""
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
        return updated
    
    def delete(self, id: str) -> bool:
        """Delete a queue."""
        if id in self.queues:
            del self.queues[id]
            return True
        return False
    
    def add_question(self, queue_id: str, question_id: str, position: Optional[int] = None) -> Optional[Queue]:
        """Add a question to a queue."""
        queue = self.queues.get(queue_id)
        if not queue or queue.frozen:
            return None
        
        if question_id in queue.questionIds:
            return queue  # Already exists
        
        question_ids = list(queue.questionIds)
        if position is not None and 0 <= position <= len(question_ids):
            question_ids.insert(position, question_id)
        else:
            question_ids.append(question_id)
        
        return self.update(queue_id, {'questionIds': question_ids})
    
    def remove_question(self, queue_id: str, question_id: str) -> Optional[Queue]:
        """Remove a question from a queue."""
        queue = self.queues.get(queue_id)
        if not queue or queue.frozen:
            return None
        
        question_ids = [qid for qid in queue.questionIds if qid != question_id]
        return self.update(queue_id, {'questionIds': question_ids})
    
    def reorder_questions(self, queue_id: str, question_ids: list[str]) -> Optional[Queue]:
        """Reorder questions in a queue."""
        queue = self.queues.get(queue_id)
        if not queue or queue.frozen:
            return None
        
        return self.update(queue_id, {'questionIds': question_ids})
    
    def toggle_freeze(self, queue_id: str, frozen: bool) -> Optional[Queue]:
        """Freeze or unfreeze a queue."""
        return self.update(queue_id, {'frozen': frozen})
    
    def add_collaborator(self, queue_id: str, email: str) -> Optional[Queue]:
        """Add a collaborator to a queue."""
        queue = self.queues.get(queue_id)
        if not queue:
            return None
        
        if email in queue.collaborators:
            return queue  # Already exists
        
        collaborators = list(queue.collaborators) + [email]
        return self.update(queue_id, {'collaborators': collaborators})
    
    def remove_collaborator(self, queue_id: str, email: str) -> Optional[Queue]:
        """Remove a collaborator from a queue."""
        queue = self.queues.get(queue_id)
        if not queue:
            return None
        
        collaborators = [e for e in queue.collaborators if e != email]
        return self.update(queue_id, {'collaborators': collaborators})


# Global stores
question_store = QuestionStore()
queue_store = QueueStore(question_store)
