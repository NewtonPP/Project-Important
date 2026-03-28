from datetime import datetime
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, Field
from uuid import uuid4


class TaskItem(BaseModel):
    """Individual task item."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    is_completed: bool = False
    original_thought_snippet: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    priority: Literal["low", "medium", "high"] = "medium"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionResponse(BaseModel):
    """Response containing session with tasks or clarification request."""
    
    session_id: str
    needs_clarification: bool
    clarity_score: int = Field(ge=1, le=10)
    tasks: List[TaskItem]
    follow_up_question: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptionResponse(BaseModel):
    """Response from audio transcription."""
    
    transcript_id: str
    raw_transcript: str
    audio_duration_seconds: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskExtractionRequest(BaseModel):
    """Request to extract tasks from transcript."""
    
    transcript: str
    user_context: Optional[Dict[str, Any]] = None


class ClarificationRequest(BaseModel):
    """Request to refine tasks with clarification answer."""
    
    session_id: str
    clarification_answer: str


class TaskUpdateRequest(BaseModel):
    """Request to update task status."""
    
    is_completed: bool


class SessionListResponse(BaseModel):
    """Response for listing sessions."""
    
    sessions: List["SessionSummary"]
    pagination: "PaginationInfo"


class SessionSummary(BaseModel):
    """Summary of a session for list view."""
    
    session_id: str
    clarity_score: Optional[int]
    task_count: int
    completed_task_count: int
    created_at: datetime


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    
    page: int
    limit: int
    total_pages: int
    total_count: int


class ErrorResponse(BaseModel):
    """Standardized error response."""
    
    error: "ErrorDetail"


class ErrorDetail(BaseModel):
    """Error details."""
    
    code: str
    message: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
