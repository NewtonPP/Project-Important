# ClarityVoice API Reference

Base URL: `http://localhost:8002/api/v1`

## Quick Start

### Main Endpoint (All-in-One)
```bash
POST /api/v1/process
```
Upload audio, get transcription + task extraction in one call.

---

## Core Endpoints

### 1. Process Audio (Main Workflow)

**POST /api/v1/process**

Upload audio file, returns transcription and extracted tasks.

**Request:**
```bash
Content-Type: multipart/form-data

audio_file: File (required)
  - Formats: .mp3, .m4a, .wav, .webm, .ogg
  - Max size: 25MB
```

**Response (200 OK):**
```json
{
  "session_id": "uuid",
  "needs_clarification": false,
  "clarity_score": 8,
  "tasks": [
    {
      "id": "uuid",
      "text": "Buy eggs at the store",
      "is_completed": false,
      "original_thought_snippet": "buy eggs",
      "estimated_duration_minutes": 20,
      "priority": "medium",
      "created_at": "2026-03-28T12:00:00",
      "updated_at": "2026-03-28T12:00:00"
    }
  ],
  "follow_up_question": null,
  "suggested_breakdown_categories": null,
  "metadata": {
    "transcript_length": 75,
    "audio_filename": "audio.mp3"
  }
}
```

**Clarity Score Interpretation:**
- **7-10**: Clear, actionable (tasks extracted immediately)
- **5-6**: Somewhat clear (tasks extracted, may be vague)
- **1-4**: Too vague (needs clarification, tasks = [])

**Response States:**

| needs_clarification | suggested_breakdown_categories | What to do |
|---------------------|-------------------------------|------------|
| false | null | Display tasks |
| true | null | Show follow_up_question, collect answer, call /tasks/refine |
| true | ["work", "home", ...] | Offer breakdown mode, call /tasks/guided-breakdown per category |

---

### 2. Refine with Clarification

**POST /api/v1/tasks/refine**

Submit clarification answer to get refined tasks.

**Request:**
```json
{
  "session_id": "uuid",
  "clarification_answer": "I want to focus on cleaning my desk"
}
```

**Response (200 OK):**
```json
{
  "session_id": "uuid",
  "needs_clarification": false,
  "clarity_score": 7,
  "tasks": [
    {
      "id": "uuid",
      "text": "Clean desk surface",
      "priority": "medium",
      "estimated_duration_minutes": 30
    }
  ],
  "follow_up_question": null,
  "suggested_breakdown_categories": null
}
```

**Note**: If clarification is still vague, `suggested_breakdown_categories` will be populated.

---

### 3. Guided Breakdown (Category-Specific)

**POST /api/v1/tasks/guided-breakdown**

Extract tasks for a specific category during breakdown mode.

**Request:**
```json
{
  "session_id": "uuid",
  "category": "work",
  "category_response": "I have client emails and a report due"
}
```

**Response (200 OK):**
```json
{
  "session_id": "uuid",
  "category": "work",
  "tasks": [
    {
      "id": "uuid",
      "text": "Respond to client emails",
      "priority": "high",
      "estimated_duration_minutes": 60
    },
    {
      "id": "uuid",
      "text": "Complete report",
      "priority": "high",
      "estimated_duration_minutes": 120
    }
  ],
  "has_more_in_category": false
}
```

**Usage**: Call this once per category in `suggested_breakdown_categories`. Tasks automatically accumulate in the session.

---

### 4. Get Session

**GET /api/v1/sessions/{session_id}**

Retrieve a specific session with all tasks (including from breakdown).

**Response (200 OK):**
```json
{
  "session_id": "uuid",
  "needs_clarification": false,
  "clarity_score": 4,
  "tasks": [
    {
      "id": "uuid",
      "text": "Task from work category",
      "is_completed": false,
      "priority": "high"
    },
    {
      "id": "uuid",
      "text": "Task from home category",
      "is_completed": false,
      "priority": "medium"
    }
  ],
  "follow_up_question": null,
  "suggested_breakdown_categories": ["work", "home", "errands"]
}
```

---

### 5. List Sessions

**GET /api/v1/sessions**

List all sessions with pagination.

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `sort_by` (default: "created_at")
- `order` (default: "desc")

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "clarity_score": 8,
      "task_count": 3,
      "completed_task_count": 1,
      "created_at": "2026-03-28T12:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_pages": 5,
    "total_count": 87
  }
}
```

---

### 6. Update Task

**PATCH /api/v1/tasks/{task_id}**

Mark task as completed or incomplete.

**Request:**
```json
{
  "is_completed": true
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "text": "Buy eggs",
  "is_completed": true,
  "priority": "medium",
  "estimated_duration_minutes": 20,
  "created_at": "2026-03-28T12:00:00",
  "updated_at": "2026-03-28T12:15:00"
}
```

---

### 7. Delete Task

**DELETE /api/v1/tasks/{task_id}**

Permanently delete a task.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

---

## Error Responses

All errors follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": "Additional context",
    "timestamp": "2026-03-28T12:00:00"
  }
}
```

**Common Error Codes:**

| Code | Status | Meaning |
|------|--------|---------|
| INVALID_FILE_FORMAT | 400 | File must be .mp3, .m4a, .wav, .webm, or .ogg |
| FILE_TOO_LARGE | 400 | File exceeds 25MB limit |
| SESSION_NOT_FOUND | 404 | Invalid session_id |
| TASK_NOT_FOUND | 404 | Invalid task_id |
| RATE_LIMIT_EXCEEDED | 429 | OpenAI rate limit hit |
| TASK_EXTRACTION_FAILED | 500 | GPT-4o call failed |
| INTERNAL_SERVER_ERROR | 500 | Unexpected error |

---

## Data Models

### TaskItem
```typescript
{
  id: string;                          // UUID
  text: string;                        // Task description
  is_completed: boolean;               // Completion status
  original_thought_snippet: string | null;  // Original quote
  estimated_duration_minutes: number | null;  // Time estimate
  priority: "low" | "medium" | "high";  // Priority level
  created_at: string;                  // ISO datetime
  updated_at: string;                  // ISO datetime
}
```

### SessionResponse
```typescript
{
  session_id: string;
  needs_clarification: boolean;
  clarity_score: number;               // 1-10
  tasks: TaskItem[];
  follow_up_question: string | null;
  suggested_breakdown_categories: string[] | null;  // For breakdown mode
  metadata: object;
}
```

### GuidedBreakdownResponse
```typescript
{
  session_id: string;
  category: string;
  tasks: TaskItem[];
  has_more_in_category: boolean;
}
```

---

## Frontend Flow Logic

### Decision Tree

```
User uploads audio
    |
    v
Call POST /process
    |
    v
Check needs_clarification
    |
    +-- false --> Display tasks (DONE)
    |
    +-- true --> Display follow_up_question
                    |
                    v
                User answers
                    |
                    v
                Call POST /tasks/refine
                    |
                    v
                Check suggested_breakdown_categories
                    |
                    +-- null --> Display tasks (DONE)
                    |
                    +-- array --> Offer breakdown mode
                                     |
                                     v
                                  User accepts?
                                     |
                                     +-- No --> Display tasks if any (DONE)
                                     |
                                     +-- Yes --> For each category:
                                                    - Prompt user
                                                    - Call POST /tasks/guided-breakdown
                                                    - Display tasks
                                                 After all categories:
                                                    - Call GET /sessions/{id}
                                                    - Show complete list (DONE)
```

### Pseudocode

```javascript
async function processAudio(audioFile) {
  // Step 1: Upload and process
  const response = await POST('/api/v1/process', { audio_file: audioFile });
  
  // Step 2: Check if clarification needed
  if (!response.needs_clarification) {
    return displayTasks(response.tasks);
  }
  
  // Step 3: Ask clarification question
  const answer = await getUserAnswer(response.follow_up_question);
  const refined = await POST('/api/v1/tasks/refine', {
    session_id: response.session_id,
    clarification_answer: answer
  });
  
  // Step 4: Check if breakdown suggested
  if (!refined.suggested_breakdown_categories) {
    return displayTasks(refined.tasks);
  }
  
  // Step 5: Offer breakdown mode
  const acceptBreakdown = await askUserBreakdown(refined.suggested_breakdown_categories);
  
  if (!acceptBreakdown) {
    return displayTasks(refined.tasks);
  }
  
  // Step 6: Guided breakdown
  const allTasks = [];
  for (const category of refined.suggested_breakdown_categories) {
    const categoryAnswer = await getCategoryResponse(category);
    const categoryTasks = await POST('/api/v1/tasks/guided-breakdown', {
      session_id: refined.session_id,
      category: category,
      category_response: categoryAnswer
    });
    allTasks.push(...categoryTasks.tasks);
  }
  
  // Step 7: Show all accumulated tasks
  const finalSession = await GET(`/api/v1/sessions/${refined.session_id}`);
  return displayTasks(finalSession.tasks);
}
```

---

## Rate Limiting & Costs

### OpenAI API Costs (per request):
- Whisper transcription: ~$0.006/minute
- GPT-4o extraction: ~$0.010/call
- Full breakdown (3 categories): ~$0.056 total

### Expected Response Times:
- Clear input: ~2.5 seconds
- With clarification: ~4.5 seconds
- Full breakdown: ~10 seconds (multiple API calls)

### Recommended Rate Limiting:
- Max 10 uploads per user per minute
- Show loading states for API calls
- Implement request timeouts (60s)

---

## Testing

### Interactive Docs
http://localhost:8002/docs

### Health Check
```bash
GET /health
Response: {"status": "healthy", "service": "clarityvoice-backend", "version": "1.0.0"}
```

### Example cURL Commands

**Upload audio:**
```bash
curl -X POST http://localhost:8002/api/v1/process \
  -F "audio_file=@audio.mp3"
```

**Refine tasks:**
```bash
curl -X POST http://localhost:8002/api/v1/tasks/refine \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "clarification_answer": "Focus on work"}'
```

**Guided breakdown:**
```bash
curl -X POST http://localhost:8002/api/v1/tasks/guided-breakdown \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "category": "work", "category_response": "Emails and report"}'
```

---

## CORS Configuration

Allowed origins:
- `http://localhost:3000` (React/Next.js dev)
- `http://localhost:5173` (Vite dev)

Add your production domain in `main.py` when deploying.
