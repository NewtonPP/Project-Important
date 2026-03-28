import logging
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from models.schemas import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


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
