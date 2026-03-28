from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from sqlalchemy import text
from config import settings


class UserDB(SQLModel, table=True):
    """Database model for authenticated users."""

    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    google_sub: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = Field(default=None)
    picture: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: List["SessionDB"] = Relationship(back_populates="user")


class SessionDB(SQLModel, table=True):
    """Database model for sessions storing transcripts and extraction results."""
    
    __tablename__ = "sessions"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)
    raw_transcript: str = Field(index=False)
    clarity_score: Optional[int] = Field(default=None, ge=1, le=10)
    needs_clarification: bool = Field(default=False)
    follow_up_question: Optional[str] = Field(default=None)
    suggested_breakdown_categories: Optional[str] = Field(default=None)
    breakdown_mode: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    tasks: List["TaskDB"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    user: Optional[UserDB] = Relationship(back_populates="sessions")


class TaskDB(SQLModel, table=True):
    """Database model for individual tasks."""
    
    __tablename__ = "tasks"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    text: str
    is_completed: bool = Field(default=False)
    original_thought_snippet: Optional[str] = Field(default=None)
    estimated_duration_minutes: Optional[int] = Field(default=None)
    priority: str = Field(default="medium")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    session: Optional[SessionDB] = Relationship(back_populates="tasks")


engine = create_engine(settings.database_url, echo=False)


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check whether a column exists in a SQLite table."""
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return any(row[1] == column_name for row in rows)


def _apply_migrations():
    """Apply lightweight schema migrations required for the MVP."""
    if not _column_exists("sessions", "user_id"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN user_id TEXT"))
            conn.commit()


def init_db():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)
    _apply_migrations()


def get_db_session():
    """Dependency for database sessions."""
    with Session(engine) as session:
        yield session
