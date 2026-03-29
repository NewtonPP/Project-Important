import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    database_url: str = Field(default="sqlite:///./clarityvoice.db", env="DATABASE_URL")
    max_upload_size_mb: int = Field(default=25, env="MAX_UPLOAD_SIZE_MB")
    temp_audio_dir: str = Field(default="./temp", env="TEMP_AUDIO_DIR")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    openai_model_transcription: str = "whisper-1"
    openai_model_completion: str = "gpt-4o"

    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    api_timeout_seconds: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        if not v or v == "sk-proj-your-key-here":
            raise ValueError(
                "OPENAI_API_KEY must be set in .env file. "
                "Get your key from https://platform.openai.com/api-keys"
            )
        return v
    
    @validator("temp_audio_dir")
    def ensure_temp_dir_exists(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


settings = get_settings()
