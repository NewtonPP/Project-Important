import os
import time
import logging
from pathlib import Path
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio files using OpenAI Whisper."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model_transcription
        self.max_retries = settings.max_retries
        self.backoff_factor = settings.retry_backoff_factor
    
    def transcribe_audio(self, file_path: str) -> str:
        """
        Transcribe audio file to text using OpenAI Whisper.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text
            
        Raises:
            Exception: If transcription fails after retries
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        logger.info(f"Starting transcription for file: {file_path}")
        
        for attempt in range(self.max_retries):
            try:
                with open(file_path, "rb") as audio_file:
                    transcription = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        response_format="text",
                        language="en"
                    )
                
                logger.info(f"Transcription successful: {len(transcription)} characters")
                return transcription
            
            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error("Rate limit exceeded after all retries")
                    raise Exception("RATE_LIMIT_EXCEEDED") from e
            
            except APITimeoutError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"API timeout, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error("API timeout after all retries")
                    raise Exception("TRANSCRIPTION_FAILED") from e
            
            except APIError as e:
                if e.status_code in [500, 503] and attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"API error {e.status_code}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error: {e.status_code} - {str(e)}")
                    raise Exception("TRANSCRIPTION_FAILED") from e
            
            except Exception as e:
                logger.error(f"Unexpected error during transcription: {str(e)}")
                raise Exception("TRANSCRIPTION_FAILED") from e
        
        raise Exception("TRANSCRIPTION_FAILED")
    
    def cleanup_audio_file(self, file_path: str):
        """Delete temporary audio file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up audio file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup audio file {file_path}: {str(e)}")
