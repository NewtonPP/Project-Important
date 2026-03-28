import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from main import app
from models.database import init_db, SessionDB, TaskDB
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    """Create test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "ClarityVoice API" in response.json()["message"]


@patch("services.transcription.TranscriptionService.transcribe_audio")
@patch("services.task_extraction.TaskExtractionService.extract_tasks")
def test_process_endpoint_high_clarity(mock_extract, mock_transcribe, client):
    """Test main /process endpoint with clear input."""
    mock_transcribe.return_value = "I need to buy eggs and call mom"
    mock_extract.return_value = {
        "clarity_score": 8,
        "tasks": [
            {
                "text": "Buy eggs",
                "original_thought_snippet": "buy eggs",
                "priority": "medium",
                "estimated_duration_minutes": 15
            },
            {
                "text": "Call mom",
                "original_thought_snippet": "call mom",
                "priority": "medium",
                "estimated_duration_minutes": 10
            }
        ],
        "needs_clarification": False,
        "follow_up_question": None
    }
    
    audio_content = b"fake audio data"
    
    response = client.post(
        "/api/v1/process",
        files={"audio_file": ("test.mp3", audio_content, "audio/mpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["clarity_score"] == 8
    assert len(data["tasks"]) == 2
    assert data["needs_clarification"] is False


@patch("services.transcription.TranscriptionService.transcribe_audio")
@patch("services.task_extraction.TaskExtractionService.extract_tasks")
def test_process_endpoint_needs_clarification(mock_extract, mock_transcribe, client):
    """Test /process endpoint with unclear input."""
    mock_transcribe.return_value = "Everything is overwhelming"
    mock_extract.return_value = {
        "clarity_score": 3,
        "tasks": [],
        "needs_clarification": True,
        "follow_up_question": "What's bothering you most right now?"
    }
    
    audio_content = b"fake audio data"
    
    response = client.post(
        "/api/v1/process",
        files={"audio_file": ("test.mp3", audio_content, "audio/mpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["clarity_score"] == 3
    assert len(data["tasks"]) == 0
    assert data["needs_clarification"] is True
    assert data["follow_up_question"] is not None


def test_process_endpoint_invalid_file_format(client):
    """Test /process with invalid file format."""
    response = client.post(
        "/api/v1/process",
        files={"audio_file": ("test.txt", b"text content", "text/plain")}
    )
    
    assert response.status_code == 400
    assert "INVALID_FILE_FORMAT" in response.json()["error"]["code"]


def test_extract_tasks_endpoint(client):
    """Test /tasks/extract endpoint."""
    with patch("services.task_extraction.TaskExtractionService.extract_tasks") as mock_extract:
        mock_extract.return_value = {
            "clarity_score": 7,
            "tasks": [{"text": "Test task", "priority": "medium"}],
            "needs_clarification": False,
            "follow_up_question": None
        }
        
        response = client.post(
            "/api/v1/tasks/extract",
            json={"transcript": "I need to test something"}
        )
        
        assert response.status_code == 200
        assert response.json()["clarity_score"] == 7
