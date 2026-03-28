import pytest
from unittest.mock import Mock, patch, MagicMock
from services.transcription import TranscriptionService


@pytest.fixture
def transcription_service():
    """Create TranscriptionService instance."""
    return TranscriptionService()


@pytest.fixture
def mock_audio_file(tmp_path):
    """Create a temporary mock audio file."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio content")
    return str(audio_file)


def test_transcribe_audio_success(transcription_service, mock_audio_file):
    """Test successful audio transcription."""
    with patch.object(transcription_service.client.audio.transcriptions, 'create') as mock_create:
        mock_create.return_value = "This is a test transcription"
        
        result = transcription_service.transcribe_audio(mock_audio_file)
        
        assert result == "This is a test transcription"
        mock_create.assert_called_once()


def test_transcribe_audio_file_not_found(transcription_service):
    """Test transcription with non-existent file."""
    with pytest.raises(FileNotFoundError):
        transcription_service.transcribe_audio("/nonexistent/file.mp3")


def test_transcribe_audio_retry_on_rate_limit(transcription_service, mock_audio_file):
    """Test retry logic on rate limit error."""
    from openai import RateLimitError
    
    with patch.object(transcription_service.client.audio.transcriptions, 'create') as mock_create:
        mock_create.side_effect = [
            RateLimitError("Rate limit exceeded", response=Mock(status_code=429), body=None),
            "Success after retry"
        ]
        
        with patch('time.sleep'):
            result = transcription_service.transcribe_audio(mock_audio_file)
        
        assert result == "Success after retry"
        assert mock_create.call_count == 2


def test_cleanup_audio_file(transcription_service, tmp_path):
    """Test audio file cleanup."""
    test_file = tmp_path / "cleanup_test.mp3"
    test_file.write_text("test")
    
    transcription_service.cleanup_audio_file(str(test_file))
    
    assert not test_file.exists()
