import pytest
import json
from unittest.mock import Mock, patch
from services.task_extraction import TaskExtractionService


@pytest.fixture
def extraction_service():
    """Create TaskExtractionService instance."""
    return TaskExtractionService()


def test_extract_tasks_high_clarity(extraction_service):
    """Test task extraction with high clarity input."""
    transcript = "I need to buy eggs and call mom at 5pm"
    
    mock_response = {
        "clarity_score": 8,
        "tasks": [
            {
                "text": "Buy eggs",
                "original_thought_snippet": "buy eggs",
                "priority": "medium",
                "estimated_duration_minutes": 15
            },
            {
                "text": "Call mom at 5pm",
                "original_thought_snippet": "call mom at 5pm",
                "priority": "medium",
                "estimated_duration_minutes": 10
            }
        ],
        "needs_clarification": False,
        "follow_up_question": None
    }
    
    with patch.object(extraction_service, '_call_gpt4o', return_value=mock_response):
        result = extraction_service.extract_tasks(transcript)
        
        assert result["clarity_score"] == 8
        assert len(result["tasks"]) == 2
        assert result["needs_clarification"] is False
        assert result["follow_up_question"] is None


def test_extract_tasks_low_clarity(extraction_service):
    """Test task extraction with low clarity input requiring clarification."""
    transcript = "Everything is overwhelming. I don't know what to do."
    
    mock_response = {
        "clarity_score": 3,
        "tasks": [],
        "needs_clarification": True,
        "follow_up_question": "What's one thing that's bothering you most right now?"
    }
    
    with patch.object(extraction_service, '_call_gpt4o', return_value=mock_response):
        result = extraction_service.extract_tasks(transcript)
        
        assert result["clarity_score"] == 3
        assert len(result["tasks"]) == 0
        assert result["needs_clarification"] is True
        assert result["follow_up_question"] is not None


def test_refine_with_clarification(extraction_service):
    """Test task refinement after clarification."""
    original = "Everything is too much"
    question = "What would you like to focus on?"
    answer = "I want to clean my desk"
    
    mock_response = {
        "clarity_score": 7,
        "tasks": [
            {
                "text": "Clean desk",
                "original_thought_snippet": "clean my desk",
                "priority": "medium",
                "estimated_duration_minutes": 20
            }
        ],
        "needs_clarification": False,
        "follow_up_question": None
    }
    
    with patch.object(extraction_service, '_call_gpt4o', return_value=mock_response):
        result = extraction_service.refine_with_clarification(original, question, answer)
        
        assert result["clarity_score"] == 7
        assert len(result["tasks"]) == 1
        assert result["needs_clarification"] is False


def test_validate_extraction_result_missing_field(extraction_service):
    """Test validation fails with missing required fields."""
    invalid_result = {"clarity_score": 5}
    
    with pytest.raises(ValueError, match="Missing required field"):
        extraction_service._validate_extraction_result(invalid_result)


def test_validate_extraction_result_invalid_score(extraction_service):
    """Test validation fails with invalid clarity score."""
    invalid_result = {
        "clarity_score": 15,
        "tasks": [],
        "needs_clarification": False
    }
    
    with pytest.raises(ValueError, match="clarity_score must be integer between 1-10"):
        extraction_service._validate_extraction_result(invalid_result)
