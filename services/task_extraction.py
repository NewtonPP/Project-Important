import json
import logging
import time
from typing import Dict, Any
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from config import settings
from services.prompts import TASK_ARCHITECT_PROMPT, CLARIFICATION_REFINEMENT_PROMPT

logger = logging.getLogger(__name__)


class TaskExtractionService:
    """Service for extracting tasks from transcripts using GPT-4o."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model_completion
        self.max_retries = settings.max_retries
        self.backoff_factor = settings.retry_backoff_factor
    
    def extract_tasks(self, transcript: str) -> Dict[str, Any]:
        """
        Extract actionable tasks from transcript using GPT-4o.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            Dict with clarity_score, tasks, needs_clarification, follow_up_question
            
        Raises:
            Exception: If task extraction fails after retries
        """
        logger.info(f"Extracting tasks from transcript ({len(transcript)} chars)")
        
        messages = [
            {"role": "system", "content": TASK_ARCHITECT_PROMPT},
            {"role": "user", "content": transcript}
        ]
        
        result = self._call_gpt4o(messages)
        logger.info(f"Task extraction complete: clarity_score={result.get('clarity_score')}")
        return result
    
    def refine_with_clarification(
        self, 
        original_transcript: str, 
        follow_up_question: str,
        clarification_answer: str
    ) -> Dict[str, Any]:
        """
        Refine task extraction with user's clarification answer.
        
        Args:
            original_transcript: Original user transcript
            follow_up_question: The question we asked for clarification
            clarification_answer: User's answer to the question
            
        Returns:
            Dict with refined tasks
        """
        logger.info("Refining tasks with clarification")
        
        system_prompt = CLARIFICATION_REFINEMENT_PROMPT.format(
            original_transcript=original_transcript,
            follow_up_question=follow_up_question,
            clarification_answer=clarification_answer
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": clarification_answer}
        ]
        
        result = self._call_gpt4o(messages)
        logger.info(f"Refinement complete: clarity_score={result.get('clarity_score')}")
        return result
    
    def _call_gpt4o(self, messages: list) -> Dict[str, Any]:
        """
        Call GPT-4o API with retry logic.
        
        Args:
            messages: List of message dicts for chat completion
            
        Returns:
            Parsed JSON response
            
        Raises:
            Exception: If API call fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=1500,
                    timeout=settings.api_timeout_seconds
                )
                
                content = response.choices[0].message.content
                result = json.loads(content)
                
                self._validate_extraction_result(result)
                return result
            
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from GPT-4o: {str(e)}")
                raise Exception("TASK_EXTRACTION_FAILED") from e
            
            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error("Rate limit exceeded after all retries")
                    raise Exception("RATE_LIMIT_EXCEEDED") from e
            
            except APITimeoutError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"API timeout, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error("API timeout after all retries")
                    raise Exception("TASK_EXTRACTION_FAILED") from e
            
            except APIError as e:
                if e.status_code in [500, 503] and attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"API error {e.status_code}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error: {e.status_code} - {str(e)}")
                    raise Exception("TASK_EXTRACTION_FAILED") from e
            
            except Exception as e:
                logger.error(f"Unexpected error during task extraction: {str(e)}")
                raise Exception("TASK_EXTRACTION_FAILED") from e
        
        raise Exception("TASK_EXTRACTION_FAILED")
    
    def _validate_extraction_result(self, result: Dict[str, Any]):
        """Validate that extraction result has required fields."""
        required_fields = ["clarity_score", "tasks", "needs_clarification"]
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field in GPT-4o response: {field}")
        
        if not isinstance(result["clarity_score"], int) or not (1 <= result["clarity_score"] <= 10):
            raise ValueError("clarity_score must be integer between 1-10")
        
        if not isinstance(result["tasks"], list):
            raise ValueError("tasks must be a list")
        
        if result["needs_clarification"] and not result.get("follow_up_question"):
            raise ValueError("follow_up_question required when needs_clarification is true")
