import logging
from datetime import datetime
from fastapi import Request, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select
from models.schemas import ErrorResponse, ErrorDetail
from models.database import UserDB, get_db_session
from services.auth import decode_access_token, AuthError

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db_session)
) -> UserDB:
    """Resolve current user from Bearer JWT."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH_REQUIRED")

    try:
        payload = decode_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.args[0]) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_AUTH_TOKEN")

    statement = select(UserDB).where(UserDB.id == user_id)
    user = db.exec(statement).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER_NOT_FOUND")

    return user


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for all uncaught exceptions."""
    
    error_code = "INTERNAL_SERVER_ERROR"
    message = "An unexpected error occurred"
    details = str(exc)
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if isinstance(exc, RequestValidationError):
        error_code = "INVALID_REQUEST"
        message = "Request validation failed"
        details = str(exc)
        status_code = status.HTTP_400_BAD_REQUEST
    
    elif hasattr(exc, 'args') and exc.args:
        error_msg = exc.args[0] if exc.args else str(exc)
        
        if "INVALID_FILE_FORMAT" in error_msg:
            error_code = "INVALID_FILE_FORMAT"
            message = "Unsupported audio file format"
            status_code = status.HTTP_400_BAD_REQUEST
        
        elif "FILE_TOO_LARGE" in error_msg:
            error_code = "FILE_TOO_LARGE"
            message = "Audio file exceeds size limit"
            status_code = status.HTTP_400_BAD_REQUEST
        
        elif "TRANSCRIPTION_FAILED" in error_msg:
            error_code = "TRANSCRIPTION_FAILED"
            message = "Failed to transcribe audio file"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        elif "TASK_EXTRACTION_FAILED" in error_msg:
            error_code = "TASK_EXTRACTION_FAILED"
            message = "Failed to extract tasks from transcript"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        elif "SESSION_NOT_FOUND" in error_msg:
            error_code = "SESSION_NOT_FOUND"
            message = "Session not found"
            status_code = status.HTTP_404_NOT_FOUND
        
        elif "TASK_NOT_FOUND" in error_msg:
            error_code = "TASK_NOT_FOUND"
            message = "Task not found"
            status_code = status.HTTP_404_NOT_FOUND
        
        elif "RATE_LIMIT_EXCEEDED" in error_msg:
            error_code = "RATE_LIMIT_EXCEEDED"
            message = "Too many requests to external API"
            status_code = status.HTTP_429_TOO_MANY_REQUESTS

        elif "AUTH_REQUIRED" in error_msg:
            error_code = "AUTH_REQUIRED"
            message = "Authentication required"
            status_code = status.HTTP_401_UNAUTHORIZED

        elif "INVALID_AUTH_TOKEN" in error_msg:
            error_code = "INVALID_AUTH_TOKEN"
            message = "Invalid or expired authentication token"
            status_code = status.HTTP_401_UNAUTHORIZED

        elif "USER_NOT_FOUND" in error_msg:
            error_code = "USER_NOT_FOUND"
            message = "Authenticated user not found"
            status_code = status.HTTP_401_UNAUTHORIZED

        elif "INVALID_GOOGLE_TOKEN" in error_msg:
            error_code = "INVALID_GOOGLE_TOKEN"
            message = "Google token could not be verified"
            status_code = status.HTTP_401_UNAUTHORIZED

        elif "EMAIL_NOT_VERIFIED" in error_msg:
            error_code = "EMAIL_NOT_VERIFIED"
            message = "Google account email is not verified"
            status_code = status.HTTP_400_BAD_REQUEST

        elif "GOOGLE_OAUTH_NOT_CONFIGURED" in error_msg:
            error_code = "GOOGLE_OAUTH_NOT_CONFIGURED"
            message = "Google OAuth is not configured on the server"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, HTTPException):
        error_msg = str(exc.detail)
        if error_msg in {"AUTH_REQUIRED", "INVALID_AUTH_TOKEN", "USER_NOT_FOUND"}:
            error_code = error_msg
            message_map = {
                "AUTH_REQUIRED": "Authentication required",
                "INVALID_AUTH_TOKEN": "Invalid or expired authentication token",
                "USER_NOT_FOUND": "Authenticated user not found"
            }
            message = message_map[error_msg]
            status_code = exc.status_code
    
    logger.error(f"Error [{error_code}]: {message} - {details}")
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=error_code,
            message=message,
            details=details,
            timestamp=datetime.utcnow()
        )
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode='json')
    )
