import os
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlmodel import Session, select
from models.database import SessionDB, TaskDB, UserDB, get_db_session
from models.schemas import (
    TranscriptionResponse,
    TaskExtractionRequest,
    SessionResponse,
    TaskItem,
    ClarificationRequest,
    TaskUpdateRequest,
    SessionListResponse,
    SessionSummary,
    PaginationInfo,
    GuidedBreakdownRequest,
    GuidedBreakdownResponse,
    GoogleAuthRequest,
    AuthResponse,
    UserProfile
)
from api.dependencies import get_current_user
from services.auth import verify_google_id_token, create_access_token
from services.transcription import TranscriptionService
from services.task_extraction import TaskExtractionService
from config import settings
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["clarityvoice"])

transcription_service = TranscriptionService()
task_extraction_service = TaskExtractionService()

ALLOWED_EXTENSIONS = {".mp3", ".m4a", ".wav", ".webm", ".ogg"}


@router.post("/auth/google", response_model=AuthResponse)
async def auth_google(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db_session)
):
    """Exchange a Google ID token for a ClarityVoice API JWT."""
    claims = verify_google_id_token(request.id_token)

    google_sub = claims.get("sub")
    email = claims.get("email")
    if not google_sub or not email:
        raise Exception("INVALID_GOOGLE_TOKEN")

    statement = select(UserDB).where(UserDB.google_sub == google_sub)
    user = db.exec(statement).first()

    if not user:
        user = UserDB(
            id=str(uuid4()),
            google_sub=google_sub,
            email=email,
            name=claims.get("name"),
            picture=claims.get("picture"),
        )
    else:
        user.email = email
        user.name = claims.get("name")
        user.picture = claims.get("picture")
        user.updated_at = datetime.utcnow()

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        access_token=access_token,
        expires_in=settings.jwt_expires_minutes * 60,
        user=UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture
        )
    )


@router.get("/auth/me", response_model=UserProfile)
async def auth_me(current_user: UserDB = Depends(get_current_user)):
    """Get profile of currently authenticated user."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture
    )


@router.post("/audio/upload", response_model=TranscriptionResponse)
async def upload_audio(
    audio_file: UploadFile = File(...),
    # db: Session = Depends(get_db_session),
    # current_user: UserDB = Depends(get_current_user)
):
    """
    Upload audio file and get transcription.
    Person 3: Audio Lead endpoint.
    """
    file_ext = Path(audio_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise Exception(f"INVALID_FILE_FORMAT: Allowed formats are {', '.join(ALLOWED_EXTENSIONS)}")
    
    unique_filename = f"{uuid4()}_{audio_file.filename}"
    file_path = os.path.join(settings.temp_audio_dir, unique_filename)
    
    try:
        file_size_mb = 0
        with open(file_path, "wb") as buffer:
            content = await audio_file.read()
            file_size_mb = len(content) / (1024 * 1024)
            
            if file_size_mb > settings.max_upload_size_mb:
                raise Exception(f"FILE_TOO_LARGE: File size {file_size_mb:.2f}MB exceeds limit of {settings.max_upload_size_mb}MB")
            
            buffer.write(content)
        
        logger.info(f"Audio file saved: {file_path} ({file_size_mb:.2f}MB)")
        
        transcript = transcription_service.transcribe_audio(file_path)
        
        return TranscriptionResponse(
            transcript_id=str(uuid4()),
            raw_transcript=transcript,
            audio_duration_seconds=0.0,
            created_at=datetime.utcnow()
        )
    
    finally:
        transcription_service.cleanup_audio_file(file_path)


@router.post("/tasks/extract", response_model=SessionResponse)
async def extract_tasks(
    request: TaskExtractionRequest,
    db: Session = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Extract tasks from transcript text.
    Person 1: Architect endpoint.
    """
    extraction_result = task_extraction_service.extract_tasks(request.transcript)
    
    suggested_categories = extraction_result.get("suggested_breakdown_categories")
    
    session = SessionDB(
        id=str(uuid4()),
        user_id=current_user.id,
        raw_transcript=request.transcript,
        clarity_score=extraction_result["clarity_score"],
        needs_clarification=extraction_result["needs_clarification"],
        follow_up_question=extraction_result.get("follow_up_question"),
        suggested_breakdown_categories=",".join(suggested_categories) if suggested_categories else None,
        breakdown_mode=False
    )
    db.add(session)
    
    task_items = []
    for task_data in extraction_result["tasks"]:
        task = TaskDB(
            id=str(uuid4()),
            session_id=session.id,
            text=task_data["text"],
            original_thought_snippet=task_data.get("original_thought_snippet"),
            priority=task_data.get("priority", "medium"),
            estimated_duration_minutes=task_data.get("estimated_duration_minutes")
        )
        db.add(task)
        task_items.append(TaskItem(
            id=task.id,
            text=task.text,
            is_completed=task.is_completed,
            original_thought_snippet=task.original_thought_snippet,
            estimated_duration_minutes=task.estimated_duration_minutes,
            priority=task.priority,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))
    
    db.commit()
    
    return SessionResponse(
        session_id=session.id,
        needs_clarification=session.needs_clarification,
        clarity_score=session.clarity_score,
        tasks=task_items,
        follow_up_question=session.follow_up_question,
        suggested_breakdown_categories=suggested_categories,
        metadata={
            "transcript_length": len(request.transcript)
        }
    )


@router.post("/tasks/refine", response_model=SessionResponse)
async def refine_tasks(
    request: ClarificationRequest,
    db: Session = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Refine tasks with clarification answer.
    Person 1: Architect refinement endpoint.
    """
    statement = select(SessionDB).where(
        SessionDB.id == request.session_id,
        SessionDB.user_id == current_user.id
    )
    session = db.exec(statement).first()
    
    if not session:
        raise Exception("SESSION_NOT_FOUND")
    
    refinement_result = task_extraction_service.refine_with_clarification(
        original_transcript=session.raw_transcript,
        follow_up_question=session.follow_up_question or "",
        clarification_answer=request.clarification_answer
    )
    
    session.clarity_score = refinement_result["clarity_score"]
    session.needs_clarification = refinement_result["needs_clarification"]
    session.follow_up_question = refinement_result.get("follow_up_question")
    session.updated_at = datetime.utcnow()
    
    suggested_categories = refinement_result.get("suggested_breakdown_categories")
    if suggested_categories:
        session.suggested_breakdown_categories = ",".join(suggested_categories)
        session.breakdown_mode = True
    
    task_items = []
    for task_data in refinement_result["tasks"]:
        task = TaskDB(
            id=str(uuid4()),
            session_id=session.id,
            text=task_data["text"],
            original_thought_snippet=task_data.get("original_thought_snippet"),
            priority=task_data.get("priority", "medium"),
            estimated_duration_minutes=task_data.get("estimated_duration_minutes")
        )
        db.add(task)
        task_items.append(TaskItem(
            id=task.id,
            text=task.text,
            is_completed=task.is_completed,
            original_thought_snippet=task.original_thought_snippet,
            estimated_duration_minutes=task.estimated_duration_minutes,
            priority=task.priority,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))
    
    db.commit()
    
    return SessionResponse(
        session_id=session.id,
        needs_clarification=session.needs_clarification,
        clarity_score=session.clarity_score,
        tasks=task_items,
        follow_up_question=session.follow_up_question,
        suggested_breakdown_categories=suggested_categories
    )


@router.post("/process", response_model=SessionResponse)
async def process_audio(
    audio_file: UploadFile = File(...),
    # db: Session = Depends(get_db_session),
    # current_user: UserDB = Depends(get_current_user)
):

    """
    Main endpoint: Upload audio -> Transcribe -> Extract tasks -> Save.
    Combines all three team members' work into one workflow.
    """
    file_ext = Path(audio_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise Exception(f"INVALID_FILE_FORMAT: Allowed formats are {', '.join(ALLOWED_EXTENSIONS)}")
    
    unique_filename = f"{uuid4()}_{audio_file.filename}"
    file_path = os.path.join(settings.temp_audio_dir, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await audio_file.read()
            file_size_mb = len(content) / (1024 * 1024)
            
            if file_size_mb > settings.max_upload_size_mb:
                raise Exception(f"FILE_TOO_LARGE: File size {file_size_mb:.2f}MB exceeds limit")
            
            buffer.write(content)
        
        logger.info(f"Processing audio file: {audio_file.filename}")
        
        transcript = transcription_service.transcribe_audio(file_path)
        
        extraction_result = task_extraction_service.extract_tasks(transcript)
        
        suggested_categories = extraction_result.get("suggested_breakdown_categories")
        
        session = SessionDB(
            id=str(uuid4()),
            # user_id=current_user.id,
            raw_transcript=transcript,
            clarity_score=extraction_result["clarity_score"],
            needs_clarification=extraction_result["needs_clarification"],
            follow_up_question=extraction_result.get("follow_up_question"),
            suggested_breakdown_categories=",".join(suggested_categories) if suggested_categories else None,
            breakdown_mode=False
        )
        # db.add(session)
        
        task_items = []
        for task_data in extraction_result["tasks"]:
            task = TaskDB(
                id=str(uuid4()),
                session_id=session.id,
                text=task_data["text"],
                original_thought_snippet=task_data.get("original_thought_snippet"),
                priority=task_data.get("priority", "medium"),
                estimated_duration_minutes=task_data.get("estimated_duration_minutes")
            )
            # db.add(task)
            task_items.append(TaskItem(
                id=task.id,
                text=task.text,
                is_completed=task.is_completed,
                original_thought_snippet=task.original_thought_snippet,
                estimated_duration_minutes=task.estimated_duration_minutes,
                priority=task.priority,
                created_at=task.created_at,
                updated_at=task.updated_at
            ))
        
        # db.commit()
        
        logger.info(f"Session created: {session.id} with {len(task_items)} tasks")
        
        return SessionResponse(
            session_id=session.id,
            needs_clarification=session.needs_clarification,
            clarity_score=session.clarity_score,
            tasks=task_items,
            follow_up_question=session.follow_up_question,
            suggested_breakdown_categories=suggested_categories,
            metadata={
                "transcript_length": len(transcript),
                "audio_filename": audio_file.filename
            }
        )
    
    finally:
        transcription_service.cleanup_audio_file(file_path)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    db: Session = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user)
):
    """
    List all sessions with pagination.
    Person 2: Data Specialist endpoint.
    """
    offset = (page - 1) * limit
    
    statement = select(SessionDB).where(SessionDB.user_id == current_user.id)
    if order == "desc":
        statement = statement.order_by(SessionDB.created_at.desc())
    else:
        statement = statement.order_by(SessionDB.created_at.asc())
    
    total_count = len(
        db.exec(select(SessionDB).where(SessionDB.user_id == current_user.id)).all()
    )
    
    sessions = db.exec(statement.offset(offset).limit(limit)).all()
    
    session_summaries = []
    for session in sessions:
        tasks = db.exec(select(TaskDB).where(TaskDB.session_id == session.id)).all()
        completed_count = sum(1 for task in tasks if task.is_completed)
        
        session_summaries.append(SessionSummary(
            session_id=session.id,
            clarity_score=session.clarity_score,
            task_count=len(tasks),
            completed_task_count=completed_count,
            created_at=session.created_at
        ))
    
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
    
    return SessionListResponse(
        sessions=session_summaries,
        pagination=PaginationInfo(
            page=page,
            limit=limit,
            total_pages=total_pages,
            total_count=total_count
        )
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Get specific session with all tasks.
    Person 2: Data Specialist endpoint.
    """
    statement = select(SessionDB).where(
        SessionDB.id == session_id,
        SessionDB.user_id == current_user.id
    )
    session = db.exec(statement).first()
    
    if not session:
        raise Exception("SESSION_NOT_FOUND")
    
    tasks_statement = select(TaskDB).where(TaskDB.session_id == session_id)
    tasks = db.exec(tasks_statement).all()
    
    task_items = [
        TaskItem(
            id=task.id,
            text=task.text,
            is_completed=task.is_completed,
            original_thought_snippet=task.original_thought_snippet,
            estimated_duration_minutes=task.estimated_duration_minutes,
            priority=task.priority,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        for task in tasks
    ]
    
    return SessionResponse(
        session_id=session.id,
        needs_clarification=session.needs_clarification,
        clarity_score=session.clarity_score or 0,
        tasks=task_items,
        follow_up_question=session.follow_up_question,
        suggested_breakdown_categories=session.suggested_breakdown_categories.split(",") if session.suggested_breakdown_categories else None
    )


@router.post("/tasks/guided-breakdown", response_model=GuidedBreakdownResponse)
async def guided_breakdown(
    request: GuidedBreakdownRequest,
    db: Session = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Extract tasks from guided category breakdown.
    This endpoint is used when the user accepts structured breakdown and provides category-specific responses.
    """
    statement = select(SessionDB).where(
        SessionDB.id == request.session_id,
        SessionDB.user_id == current_user.id
    )
    session = db.exec(statement).first()
    
    if not session:
        raise Exception("SESSION_NOT_FOUND")
    
    breakdown_result = task_extraction_service.guided_breakdown_extraction(
        original_transcript=session.raw_transcript,
        category=request.category,
        category_response=request.category_response
    )
    
    if not session.breakdown_mode:
        session.breakdown_mode = True
        session.updated_at = datetime.utcnow()
    
    task_items = []
    for task_data in breakdown_result["tasks"]:
        task = TaskDB(
            id=str(uuid4()),
            session_id=session.id,
            text=task_data["text"],
            original_thought_snippet=task_data.get("original_thought_snippet"),
            priority=task_data.get("priority", "medium"),
            estimated_duration_minutes=task_data.get("estimated_duration_minutes")
        )
        db.add(task)
        task_items.append(TaskItem(
            id=task.id,
            text=task.text,
            is_completed=task.is_completed,
            original_thought_snippet=task.original_thought_snippet,
            estimated_duration_minutes=task.estimated_duration_minutes,
            priority=task.priority,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))
    
    db.commit()
    
    return GuidedBreakdownResponse(
        session_id=session.id,
        category=request.category,
        tasks=task_items,
        has_more_in_category=breakdown_result.get("has_more_in_category", False)
    )


@router.patch("/tasks/{task_id}", response_model=TaskItem)
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    db: Session = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Update task completion status.
    Person 2: Data Specialist endpoint.
    """
    statement = select(TaskDB).where(TaskDB.id == task_id)
    task = db.exec(statement).first()
    
    if not task:
        raise Exception("TASK_NOT_FOUND")

    session_statement = select(SessionDB).where(
        SessionDB.id == task.session_id,
        SessionDB.user_id == current_user.id
    )
    session = db.exec(session_statement).first()
    if not session:
        raise Exception("TASK_NOT_FOUND")
    
    task.is_completed = request.is_completed
    task.updated_at = datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return TaskItem(
        id=task.id,
        text=task.text,
        is_completed=task.is_completed,
        original_thought_snippet=task.original_thought_snippet,
        estimated_duration_minutes=task.estimated_duration_minutes,
        priority=task.priority,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Delete a specific task.
    Person 2: Data Specialist endpoint.
    """
    statement = select(TaskDB).where(TaskDB.id == task_id)
    task = db.exec(statement).first()
    
    if not task:
        raise Exception("TASK_NOT_FOUND")

    session_statement = select(SessionDB).where(
        SessionDB.id == task.session_id,
        SessionDB.user_id == current_user.id
    )
    session = db.exec(session_statement).first()
    if not session:
        raise Exception("TASK_NOT_FOUND")
    
    db.delete(task)
    db.commit()
    
    return {"success": True, "message": "Task deleted successfully"}
