"""
Pydantic models for the Exam Paper System.
These models match the protobuf/JSON API definitions.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import IntEnum
import time


# ============================================================================
# Common Types
# ============================================================================

class PaginationRequest(BaseModel):
    """Pagination request parameters."""
    page: int = Field(default=1, ge=1, description="Page number, starting from 1")
    pageSize: int = Field(default=20, ge=1, le=100, alias="page_size", description="Items per page")
    
    class Config:
        populate_by_name = True


class PaginationResponse(BaseModel):
    """Pagination response information."""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    pageSize: int = Field(description="Items per page")
    totalPages: int = Field(description="Total number of pages")
    
    @classmethod
    def create(cls, total: int, page: int, page_size: int) -> "PaginationResponse":
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            total=total,
            page=page,
            pageSize=page_size,
            totalPages=total_pages
        )


# ============================================================================
# Core Data Models
# ============================================================================

class ReadingQuestion(BaseModel):
    """Reading comprehension question."""
    id: str = Field(description="Unique question ID")
    title: str = Field(description="Source title (e.g., 2023年全国卷I)")
    year: int = Field(description="Year")
    questionNumber: str = Field(description="Question number (A, B, C, D)")
    articleContent: str = Field(description="Article content")
    questionContent: str = Field(description="Question and options")
    labels: list[str] = Field(default_factory=list, description="Labels")
    answers: list[dict] = Field(default_factory=list, description="Answer list, each item has 'number' (int) and 'answer' (A/B/C/D)")
    createdAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="Created timestamp (ms)")
    updatedAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="Updated timestamp (ms)")


class Queue(BaseModel):
    """Question queue basic info."""
    id: str = Field(description="Unique queue ID")
    name: str = Field(description="Queue name")
    questionIds: list[str] = Field(default_factory=list, description="Ordered question IDs")
    frozen: bool = Field(default=False, description="Whether the queue is frozen")
    owner: str = Field(description="Owner email")
    collaborators: list[str] = Field(default_factory=list, description="Collaborator emails")
    createdAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="Created timestamp (ms)")
    updatedAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="Updated timestamp (ms)")


class QueueDetail(BaseModel):
    """Queue with full question details."""
    queue: Queue
    questions: list[ReadingQuestion] = Field(default_factory=list)


class User(BaseModel):
    """User information."""
    id: str
    email: str
    name: str
    avatarUrl: str = ""
    createdAt: int = Field(default_factory=lambda: int(time.time() * 1000))


# ============================================================================
# Question Service Request/Response Models
# ============================================================================

class SearchQuestionsRequest(BaseModel):
    """Search questions request."""
    query: str = ""
    year: Optional[int] = None
    labels: list[str] = Field(default_factory=list)
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)


class SearchQuestionsResponse(BaseModel):
    """Search questions response."""
    questions: list[ReadingQuestion]
    pagination: PaginationResponse


class GetQuestionResponse(BaseModel):
    """Get single question response."""
    question: Optional[ReadingQuestion] = None


class BatchGetQuestionsRequest(BaseModel):
    """Batch get questions request."""
    ids: list[str]


class BatchGetQuestionsResponse(BaseModel):
    """Batch get questions response."""
    questions: list[ReadingQuestion]


class CreateQuestionRequest(BaseModel):
    """Create question request."""
    title: str
    year: int
    questionNumber: str
    articleContent: str
    questionContent: str
    labels: list[str] = Field(default_factory=list)


class CreateQuestionResponse(BaseModel):
    """Create question response."""
    question: ReadingQuestion


class UpdateQuestionRequest(BaseModel):
    """Update question request."""
    id: str
    title: Optional[str] = None
    year: Optional[int] = None
    questionNumber: Optional[str] = None
    articleContent: Optional[str] = None
    questionContent: Optional[str] = None
    labels: Optional[list[str]] = None


class UpdateQuestionResponse(BaseModel):
    """Update question response."""
    question: ReadingQuestion


class DeleteQuestionRequest(BaseModel):
    """Delete question request."""
    id: str


class GetAllLabelsResponse(BaseModel):
    """Get all labels response."""
    labels: list[str]


class GetAllYearsResponse(BaseModel):
    """Get all years response."""
    years: list[int]


# ============================================================================
# Queue Service Request/Response Models
# ============================================================================

class ListQueuesRequest(BaseModel):
    """List queues request."""
    userEmail: str = Field(alias="user_email")
    pagination: Optional[PaginationRequest] = None
    
    class Config:
        populate_by_name = True


class ListQueuesResponse(BaseModel):
    """List queues response."""
    queues: list[Queue]
    pagination: Optional[PaginationResponse] = None


class GetQueueResponse(BaseModel):
    """Get queue detail response."""
    queue: Optional[QueueDetail] = None


class CreateQueueRequest(BaseModel):
    """Create queue request."""
    name: str
    owner: str


class CreateQueueResponse(BaseModel):
    """Create queue response."""
    queue: Queue


class UpdateQueueRequest(BaseModel):
    """Update queue request."""
    id: str
    name: Optional[str] = None


class UpdateQueueResponse(BaseModel):
    """Update queue response."""
    queue: Queue


class DeleteQueueRequest(BaseModel):
    """Delete queue request."""
    id: str


class AddQuestionToQueueRequest(BaseModel):
    """Add question to queue request."""
    queueId: str = Field(alias="queue_id")
    questionId: str
    position: Optional[int] = None
    
    class Config:
        populate_by_name = True


class AddQuestionToQueueResponse(BaseModel):
    """Add question to queue response."""
    queue: Queue


class RemoveQuestionFromQueueRequest(BaseModel):
    """Remove question from queue request."""
    queueId: str = Field(alias="queue_id")
    questionId: str = Field(alias="question_id")
    
    class Config:
        populate_by_name = True


class RemoveQuestionFromQueueResponse(BaseModel):
    """Remove question from queue response."""
    queue: Queue


class ReorderQueueQuestionsRequest(BaseModel):
    """Reorder queue questions request."""
    queueId: str = Field(alias="queue_id")
    questionIds: list[str]
    
    class Config:
        populate_by_name = True


class ReorderQueueQuestionsResponse(BaseModel):
    """Reorder queue questions response."""
    queue: Queue


class ToggleQueueFreezeRequest(BaseModel):
    """Toggle queue freeze request."""
    queueId: str = Field(alias="queue_id")
    frozen: bool
    
    class Config:
        populate_by_name = True


class ToggleQueueFreezeResponse(BaseModel):
    """Toggle queue freeze response."""
    queue: Queue


class AddCollaboratorRequest(BaseModel):
    """Add collaborator request."""
    queueId: str = Field(alias="queue_id")
    collaboratorEmail: str
    
    class Config:
        populate_by_name = True


class AddCollaboratorResponse(BaseModel):
    """Add collaborator response."""
    queue: Queue


class RemoveCollaboratorRequest(BaseModel):
    """Remove collaborator request."""
    queueId: str = Field(alias="queue_id")
    collaboratorEmail: str = Field(alias="collaborator_email")
    
    class Config:
        populate_by_name = True


class RemoveCollaboratorResponse(BaseModel):
    """Remove collaborator response."""
    queue: Queue


class ExportFormat(IntEnum):
    """Export format enum."""
    UNSPECIFIED = 0
    JSON = 1
    PDF = 2
    WORD = 3


class ExportQueueRequest(BaseModel):
    """Export queue request."""
    queueId: str = Field(alias="queue_id")
    format: ExportFormat
    
    class Config:
        populate_by_name = True


class ExportQueueResponse(BaseModel):
    """Export queue response."""
    data: bytes
    filename: str
    contentType: str


# ============================================================================
# Error Response
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail."""
    field: Optional[str] = None
    reason: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    code: int
    message: str
    details: Optional[ErrorDetail] = None
