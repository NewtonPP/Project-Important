import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from models.database import init_db


@pytest.fixture
def client():
    """Create test client."""
    init_db()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


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

    response = client.post(
        "/api/v1/process",
        files={"audio_file": ("test.mp3", b"fake audio data", "audio/mpeg")}
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

    response = client.post(
        "/api/v1/process",
        files={"audio_file": ("test.mp3", b"fake audio data", "audio/mpeg")}
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
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "INVALID_FILE_FORMAT"


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


@patch("services.task_extraction.TaskExtractionService.extract_tasks")
def test_process_with_breakdown_suggestion(mock_extract, client):
    """Test /process endpoint when AI suggests breakdown categories."""
    mock_extract.return_value = {
        "clarity_score": 4,
        "tasks": [],
        "needs_clarification": True,
        "follow_up_question": "I hear you're overwhelmed. Which area feels most urgent?",
        "suggested_breakdown_categories": ["work", "home", "errands"]
    }

    with patch("services.transcription.TranscriptionService.transcribe_audio") as mock_transcribe:
        mock_transcribe.return_value = "Too much to do everywhere"

        response = client.post(
            "/api/v1/process",
            files={"audio_file": ("test.mp3", b"audio data", "audio/mpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clarity_score"] == 4
        assert data["needs_clarification"] is True
        assert data["suggested_breakdown_categories"] == ["work", "home", "errands"]


@patch("services.task_extraction.TaskExtractionService.guided_breakdown_extraction")
def test_guided_breakdown_endpoint(mock_breakdown, client):
    """Test /tasks/guided-breakdown endpoint."""
    mock_breakdown.return_value = {
        "tasks": [
            {
                "text": "Finish quarterly report",
                "original_thought_snippet": "report due",
                "priority": "high",
                "estimated_duration_minutes": 90
            }
        ],
        "has_more_in_category": False
    }

    with patch("services.task_extraction.TaskExtractionService.extract_tasks") as mock_extract:
        mock_extract.return_value = {
            "clarity_score": 4,
            "tasks": [],
            "needs_clarification": True,
            "follow_up_question": "What area is urgent?",
            "suggested_breakdown_categories": ["work", "home"]
        }

        create_response = client.post(
            "/api/v1/tasks/extract",
            json={"transcript": "Too much to handle"}
        )
        session_id = create_response.json()["session_id"]

        breakdown_response = client.post(
            "/api/v1/tasks/guided-breakdown",
            json={
                "session_id": session_id,
                "category": "work",
                "category_response": "I have a quarterly report due and need to respond to client emails"
            }
        )

        assert breakdown_response.status_code == 200
        data = breakdown_response.json()
        assert data["category"] == "work"
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["text"] == "Finish quarterly report"
        assert "has_more_in_category" in data


