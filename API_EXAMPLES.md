# ClarityVoice API - Example Requests & Responses

## Example 1: Main Workflow (Happy Path - Clear Input)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@clear_input.mp3" \
  -H "accept: application/json"
```

### Response (200 OK)
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "needs_clarification": false,
  "clarity_score": 8,
  "tasks": [
    {
      "id": "task-uuid-1",
      "text": "Go to grocery store for eggs and milk",
      "is_completed": false,
      "original_thought_snippet": "go to the grocery store for eggs and milk",
      "estimated_duration_minutes": 20,
      "priority": "medium",
      "created_at": "2026-03-28T12:00:00",
      "updated_at": "2026-03-28T12:00:00"
    },
    {
      "id": "task-uuid-2",
      "text": "Call mom at 5pm",
      "is_completed": false,
      "original_thought_snippet": "call my mom at 5pm",
      "estimated_duration_minutes": 10,
      "priority": "medium",
      "created_at": "2026-03-28T12:00:00",
      "updated_at": "2026-03-28T12:00:00"
    }
  ],
  "follow_up_question": null,
  "metadata": {
    "transcript_length": 75,
    "audio_filename": "clear_input.mp3"
  }
}
```

---

## Example 2: Cluttered Input (Needs Clarification)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@cluttered_input.mp3"
```

### Response (200 OK)
```json
{
  "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "needs_clarification": true,
  "clarity_score": 4,
  "tasks": [],
  "follow_up_question": "I hear you're feeling overwhelmed about cleaning and a work project. Which one would you like to tackle first, or is there a specific part of either that's bothering you most?",
  "metadata": {
    "transcript_length": 156,
    "audio_filename": "cluttered_input.mp3"
  }
}
```

---

## Example 3: Refinement After Clarification

### Request
```bash
curl -X POST http://localhost:8000/api/v1/tasks/refine \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "clarification_answer": "I want to start with the work project, specifically planning the presentation."
  }'
```

### Response (200 OK)
```json
{
  "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "needs_clarification": false,
  "clarity_score": 7,
  "tasks": [
    {
      "id": "task-uuid-3",
      "text": "Plan work presentation outline",
      "is_completed": false,
      "original_thought_snippet": "that project at work",
      "estimated_duration_minutes": 30,
      "priority": "high",
      "created_at": "2026-03-28T12:05:00",
      "updated_at": "2026-03-28T12:05:00"
    },
    {
      "id": "task-uuid-4",
      "text": "Create presentation slides",
      "is_completed": false,
      "original_thought_snippet": "planning the presentation",
      "estimated_duration_minutes": 60,
      "priority": "high",
      "created_at": "2026-03-28T12:05:00",
      "updated_at": "2026-03-28T12:05:00"
    }
  ],
  "follow_up_question": null
}
```

---

## Example 4: List Sessions

### Request
```bash
curl "http://localhost:8000/api/v1/sessions?page=1&limit=10"
```

### Response (200 OK)
```json
{
  "sessions": [
    {
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "clarity_score": 8,
      "task_count": 2,
      "completed_task_count": 1,
      "created_at": "2026-03-28T12:00:00"
    },
    {
      "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "clarity_score": 7,
      "task_count": 2,
      "completed_task_count": 0,
      "created_at": "2026-03-28T12:05:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total_pages": 1,
    "total_count": 2
  }
}
```

---

## Example 5: Get Specific Session

### Request
```bash
curl http://localhost:8000/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Response (200 OK)
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "needs_clarification": false,
  "clarity_score": 8,
  "tasks": [
    {
      "id": "task-uuid-1",
      "text": "Go to grocery store for eggs and milk",
      "is_completed": true,
      "original_thought_snippet": "go to the grocery store for eggs and milk",
      "estimated_duration_minutes": 20,
      "priority": "medium",
      "created_at": "2026-03-28T12:00:00",
      "updated_at": "2026-03-28T12:10:00"
    },
    {
      "id": "task-uuid-2",
      "text": "Call mom at 5pm",
      "is_completed": false,
      "original_thought_snippet": "call my mom at 5pm",
      "estimated_duration_minutes": 10,
      "priority": "medium",
      "created_at": "2026-03-28T12:00:00",
      "updated_at": "2026-03-28T12:00:00"
    }
  ],
  "follow_up_question": null
}
```

---

## Example 6: Update Task Status

### Request
```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/task-uuid-2 \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true}'
```

### Response (200 OK)
```json
{
  "id": "task-uuid-2",
  "text": "Call mom at 5pm",
  "is_completed": true,
  "original_thought_snippet": "call my mom at 5pm",
  "estimated_duration_minutes": 10,
  "priority": "medium",
  "created_at": "2026-03-28T12:00:00",
  "updated_at": "2026-03-28T12:15:00"
}
```

---

## Example 7: Delete Task

### Request
```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/task-uuid-2
```

### Response (200 OK)
```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

---

## Example 8: Error Response (Invalid File Format)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@document.pdf"
```

### Response (400 Bad Request)
```json
{
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "Unsupported audio file format",
    "details": "INVALID_FILE_FORMAT: Allowed formats are .mp3, .m4a, .wav, .webm, .ogg",
    "timestamp": "2026-03-28T12:20:00"
  }
}
```

---

## Example 9: Error Response (Session Not Found)

### Request
```bash
curl http://localhost:8000/api/v1/sessions/nonexistent-id
```

### Response (404 Not Found)
```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session not found",
    "details": "SESSION_NOT_FOUND",
    "timestamp": "2026-03-28T12:25:00"
  }
}
```

---

## Example 10: Text-Only Extraction (No Audio)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/tasks/extract \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "I need to buy eggs, call mom, and finish the report by Friday",
    "user_context": {
      "timezone": "America/New_York"
    }
  }'
```

### Response (200 OK)
```json
{
  "session_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "needs_clarification": false,
  "clarity_score": 9,
  "tasks": [
    {
      "id": "task-uuid-5",
      "text": "Buy eggs",
      "is_completed": false,
      "original_thought_snippet": "buy eggs",
      "estimated_duration_minutes": 10,
      "priority": "medium",
      "created_at": "2026-03-28T12:30:00",
      "updated_at": "2026-03-28T12:30:00"
    },
    {
      "id": "task-uuid-6",
      "text": "Call mom",
      "is_completed": false,
      "original_thought_snippet": "call mom",
      "estimated_duration_minutes": 15,
      "priority": "medium",
      "created_at": "2026-03-28T12:30:00",
      "updated_at": "2026-03-28T12:30:00"
    },
    {
      "id": "task-uuid-7",
      "text": "Finish report by Friday",
      "is_completed": false,
      "original_thought_snippet": "finish the report by Friday",
      "estimated_duration_minutes": 120,
      "priority": "high",
      "created_at": "2026-03-28T12:30:00",
      "updated_at": "2026-03-28T12:30:00"
    }
  ],
  "follow_up_question": null,
  "metadata": {
    "transcript_length": 67
  }
}
```

---

## Testing with Python

```python
import requests

# Process audio
with open("test.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/process",
        files={"audio_file": f}
    )
    
result = response.json()
print(f"Clarity Score: {result['clarity_score']}")
print(f"Tasks: {len(result['tasks'])}")

# Mark first task complete
if result['tasks']:
    task_id = result['tasks'][0]['id']
    requests.patch(
        f"http://localhost:8000/api/v1/tasks/{task_id}",
        json={"is_completed": True}
    )
```

---

## Interactive API Documentation

Once the server is running, visit:

**Swagger UI**: http://localhost:8000/docs
- Try out endpoints directly in browser
- See request/response schemas
- Test with your audio files

**ReDoc**: http://localhost:8000/redoc
- Alternative documentation view
- Better for reading/reference

---

## Postman Collection (Import JSON)

```json
{
  "info": {
    "name": "ClarityVoice API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Process Audio",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "audio_file",
              "type": "file",
              "src": "test.mp3"
            }
          ]
        },
        "url": {
          "raw": "http://localhost:8000/api/v1/process",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "process"]
        }
      }
    },
    {
      "name": "List Sessions",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/v1/sessions?page=1&limit=20"
      }
    },
    {
      "name": "Update Task",
      "request": {
        "method": "PATCH",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"is_completed\": true}"
        },
        "url": "http://localhost:8000/api/v1/tasks/{task_id}"
      }
    }
  ]
}
```

Save as `ClarityVoice.postman_collection.json` and import into Postman.
