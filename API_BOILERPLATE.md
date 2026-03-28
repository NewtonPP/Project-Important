# ClarityVoice API Boilerplate

## Table of Contents
1. [API Keys & Environment Variables](#api-keys--environment-variables)
2. [External APIs Used](#external-apis-used)
3. [API Endpoints Structure](#api-endpoints-structure)
4. [Request/Response Schemas](#requestresponse-schemas)
5. [Phase Breakdown](#phase-breakdown)

---

## API Keys & Environment Variables

### Required Environment Variables (.env file)

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-...                    # Required for Phase 1 & 2
OPENAI_MODEL_TRANSCRIPTION=whisper-1          # Default model for audio transcription
OPENAI_MODEL_COMPLETION=gpt-4o                # Default model for task extraction

# Application Configuration
APP_SECRET_KEY=your-secret-key-here           # For session management/JWT
DATABASE_URL=sqlite:///./clarityvoice.db      # SQLite for MVP
ENVIRONMENT=development                        # development/staging/production

# File Upload Configuration
MAX_UPLOAD_SIZE_MB=25                         # Max audio file size
TEMP_AUDIO_DIR=./temp/audio                   # Temporary storage for audio files

# API Rate Limiting (Optional for MVP)
RATE_LIMIT_PER_MINUTE=10                      # Requests per minute per user
```

---

## External APIs Used

### 1. OpenAI API
**Purpose**: Audio transcription (Whisper) and task extraction (GPT-4o)

**Required for**: Phase 1 (Transcription) & Phase 2 (Task Extraction)

**API Documentation**: https://platform.openai.com/docs/api-reference

**Endpoints Used**:
- `POST https://api.openai.com/v1/audio/transcriptions` - Whisper transcription
- `POST https://api.openai.com/v1/chat/completions` - GPT-4o task extraction

**Authentication**: Bearer token in Authorization header

**Cost Considerations**:
- Whisper: ~$0.006 per minute of audio
- GPT-4o: Input ~$5.00/1M tokens, Output ~$15.00/1M tokens

**How to Get API Key**:
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create new secret key
4. Add billing information (required for usage)

---

## API Endpoints Structure

### Phase 1: Audio Transcription (Person 3)

#### `POST /api/v1/audio/upload`
**Purpose**: Upload audio file and receive transcription

**Request**:
```
Content-Type: multipart/form-data

{
  audio_file: File (m4a, mp3, wav, webm, ogg)
}
```

**Response**:
```json
{
  "transcript_id": "uuid-v4",
  "raw_transcript": "I need to go to the grocery store...",
  "audio_duration_seconds": 45.3,
  "created_at": "2026-03-28T10:30:00Z"
}
```

**External API Called**: OpenAI Whisper API

---

### Phase 2: Task Extraction (Person 1)

#### `POST /api/v1/tasks/extract`
**Purpose**: Process transcript and extract actionable tasks

**Request**:
```json
{
  "transcript": "I need to go to the grocery store for eggs and then call my mom at 5.",
  "user_context": {
    "timezone": "America/New_York",
    "previous_session_id": "optional-uuid"
  }
}
```

**Response** (High Clarity):
```json
{
  "session_id": "uuid-v4",
  "needs_clarification": false,
  "clarity_score": 8,
  "tasks": [
    {
      "id": "task-uuid-1",
      "text": "Go to grocery store for eggs",
      "is_completed": false,
      "original_thought_snippet": "go to the grocery store for eggs",
      "estimated_duration_minutes": null,
      "priority": "medium"
    },
    {
      "id": "task-uuid-2",
      "text": "Call mom at 5 PM",
      "is_completed": false,
      "original_thought_snippet": "call my mom at 5",
      "estimated_duration_minutes": 10,
      "priority": "medium"
    }
  ],
  "follow_up_question": null,
  "metadata": {
    "transcript_length": 75,
    "processing_time_ms": 1250
  }
}
```

**Response** (Low Clarity - Needs Clarification):
```json
{
  "session_id": "uuid-v4",
  "needs_clarification": true,
  "clarity_score": 4,
  "tasks": [],
  "follow_up_question": "I hear you're feeling overwhelmed about cleaning and a work project. Which one would you like to tackle first, or is there a specific part of either that's bothering you most?",
  "metadata": {
    "transcript_length": 180,
    "processing_time_ms": 1100
  }
}
```

**External API Called**: OpenAI GPT-4o Chat Completions API

---

#### `POST /api/v1/tasks/refine`
**Purpose**: Submit clarification answer and get refined tasks

**Request**:
```json
{
  "session_id": "uuid-v4",
  "clarification_answer": "I want to start with the work project, specifically planning the presentation."
}
```

**Response**:
```json
{
  "session_id": "uuid-v4",
  "needs_clarification": false,
  "clarity_score": 7,
  "tasks": [
    {
      "id": "task-uuid-1",
      "text": "Plan work presentation outline",
      "is_completed": false,
      "original_thought_snippet": "that project at work",
      "priority": "high"
    }
  ],
  "follow_up_question": null
}
```

**External API Called**: OpenAI GPT-4o Chat Completions API

---

### Phase 3: Data Persistence (Person 2)

#### `GET /api/v1/sessions/{session_id}`
**Purpose**: Retrieve a session with all its tasks

**Response**:
```json
{
  "session_id": "uuid-v4",
  "raw_transcript": "I need to...",
  "clarity_score": 8,
  "tasks": [...],
  "created_at": "2026-03-28T10:30:00Z",
  "updated_at": "2026-03-28T10:35:00Z"
}
```

**External API Called**: None (Database query)

---

#### `GET /api/v1/sessions`
**Purpose**: List all user sessions (paginated)

**Query Parameters**:
- `page`: int (default: 1)
- `limit`: int (default: 20, max: 100)
- `sort_by`: "created_at" | "updated_at" (default: "created_at")
- `order`: "asc" | "desc" (default: "desc")

**Response**:
```json
{
  "sessions": [
    {
      "session_id": "uuid-v4",
      "clarity_score": 8,
      "task_count": 3,
      "completed_task_count": 1,
      "created_at": "2026-03-28T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_pages": 5,
    "total_count": 95
  }
}
```

**External API Called**: None (Database query)

---

#### `PATCH /api/v1/tasks/{task_id}`
**Purpose**: Update task status (mark complete/incomplete)

**Request**:
```json
{
  "is_completed": true
}
```

**Response**:
```json
{
  "task_id": "task-uuid-1",
  "text": "Go to grocery store for eggs",
  "is_completed": true,
  "updated_at": "2026-03-28T11:00:00Z"
}
```

**External API Called**: None (Database update)

---

#### `DELETE /api/v1/tasks/{task_id}`
**Purpose**: Delete a specific task

**Response**:
```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

**External API Called**: None (Database deletion)

---

### Phase 4: Combined Workflow

#### `POST /api/v1/process` (Main Entry Point)
**Purpose**: Single endpoint that handles audio upload → transcription → task extraction

**Request**:
```
Content-Type: multipart/form-data

{
  audio_file: File,
  user_context: {
    "timezone": "America/New_York"
  }
}
```

**Response**: Same as `/api/v1/tasks/extract` response (with session_id, tasks, etc.)

**External APIs Called**: 
1. OpenAI Whisper API (transcription)
2. OpenAI GPT-4o API (task extraction)

---

## Request/Response Schemas

### Core Data Models

```python
# Pydantic Models

class TaskItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    is_completed: bool = False
    original_thought_snippet: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    priority: Literal["low", "medium", "high"] = "medium"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SessionResponse(BaseModel):
    session_id: str
    needs_clarification: bool
    clarity_score: int = Field(ge=1, le=10)
    tasks: List[TaskItem]
    follow_up_question: Optional[str] = None
    metadata: Dict[str, Any] = {}

class TranscriptionResponse(BaseModel):
    transcript_id: str
    raw_transcript: str
    audio_duration_seconds: float
    created_at: datetime

class TaskUpdateRequest(BaseModel):
    is_completed: bool

class ClarificationRequest(BaseModel):
    session_id: str
    clarification_answer: str
```

---

## Phase Breakdown

### Phase 1: Audio Transcription Setup
**Team Member**: Person 3 (Audio Lead)

**APIs Needed**:
-  OpenAI Whisper API
  - Endpoint: `https://api.openai.com/v1/audio/transcriptions`
  - Method: POST
  - Authentication: Bearer token (OPENAI_API_KEY)
  - Input: Audio file (multipart/form-data)
  - Output: JSON with transcribed text

**API Key Required**:
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys

**Additional Libraries**:
- `openai` (Python SDK) - pip install openai
- `python-multipart` - For file uploads
- `pydub` (optional) - For audio preprocessing
- `ffmpeg` (optional) - For audio format conversion

**Configuration**:
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Whisper API Call
with open(audio_file_path, "rb") as audio_file:
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
```

---

### Phase 2: Task Extraction & LLM Orchestration
**Team Member**: Person 1 (Architect)

**APIs Needed**:
-  OpenAI GPT-4o Chat Completions API
  - Endpoint: `https://api.openai.com/v1/chat/completions`
  - Method: POST
  - Authentication: Bearer token (OPENAI_API_KEY)
  - Input: Messages array with system prompt + user transcript
  - Output: Structured JSON (using JSON mode or Function Calling)

**API Key Required**:
- `OPENAI_API_KEY` - Same as Phase 1

**System Prompt Template**:
```python
SYSTEM_PROMPT = """
You are a Task Architect for ClarityVoice, a cognitive offloading tool for users experiencing executive dysfunction.

Your job:
1. Analyze the user's voice transcript (often cluttered with emotions, worries, and venting)
2. Extract ONLY actionable tasks
3. Filter out emotional noise, anxiety, and non-actionable thoughts
4. Assess clarity of the input (1-10 scale)

Output JSON with this schema:
{
  "clarity_score": 1-10,
  "tasks": [
    {
      "text": "Clear, actionable task",
      "original_thought_snippet": "relevant part from transcript",
      "priority": "low/medium/high"
    }
  ],
  "needs_clarification": boolean,
  "follow_up_question": "Only if clarity_score < 6"
}

Rules:
- If clarity_score < 6: Set needs_clarification=true and provide ONE focused question
- Tasks must be specific and actionable
- Don't create vague tasks like "deal with anxiety"
- Preserve important context (times, people, places) in task text
"""
```

**Configuration**:
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": transcript}
    ],
    response_format={"type": "json_object"},  # Force JSON output
    temperature=0.3  # Lower for more consistent extraction
)
```

---

### Phase 3: Database & Persistence
**Team Member**: Person 2 (Data Specialist)

**APIs Needed**:
-  No external APIs required (local database)

**Database**: SQLite (for MVP)

**API Key Required**: None

**Database Schema**:

```sql
-- Sessions Table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,  -- UUID
    raw_transcript TEXT NOT NULL,
    clarity_score INTEGER CHECK(clarity_score >= 1 AND clarity_score <= 10),
    needs_clarification BOOLEAN DEFAULT FALSE,
    follow_up_question TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks Table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,  -- UUID
    session_id TEXT NOT NULL,
    text TEXT NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    original_thought_snippet TEXT,
    estimated_duration_minutes INTEGER,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Index for faster queries
CREATE INDEX idx_tasks_session_id ON tasks(session_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
```

**ORM Configuration** (SQLAlchemy/SQLModel):
```python
from sqlmodel import SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clarityvoice.db")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)
```

---

### Phase 4: Integration & Complete Workflow

**APIs Needed**:
-  OpenAI Whisper API (from Phase 1)
-  OpenAI GPT-4o API (from Phase 2)
-  Internal Database (from Phase 3)

**API Key Required**:
- `OPENAI_API_KEY` - Same key for both Whisper and GPT-4o

**Flow**:
1. Receive audio file
2. Call Whisper API → Get transcript
3. Call GPT-4o API → Get tasks/clarification
4. Save to database
5. Return structured response

---

## Detailed API Specifications

### OpenAI Whisper API

**Endpoint**: `POST https://api.openai.com/v1/audio/transcriptions`

**Headers**:
```
Authorization: Bearer {OPENAI_API_KEY}
Content-Type: multipart/form-data
```

**Request Body**:
```
file: (binary) - Audio file
model: "whisper-1"
response_format: "text" | "json" | "srt" | "verbose_json" | "vtt"
language: "en" (optional, improves accuracy)
prompt: "" (optional, context for better transcription)
```

**Response**:
```json
{
  "text": "Transcribed text here..."
}
```

**Error Handling**:
- 400: Invalid file format
- 401: Invalid API key
- 413: File too large (>25MB)
- 429: Rate limit exceeded
- 500: OpenAI service error

**Retry Strategy**:
```python
# Exponential backoff for transient errors
max_retries = 3
backoff_factor = 2  # 1s, 2s, 4s
```

---

### OpenAI GPT-4o Chat Completions API

**Endpoint**: `POST https://api.openai.com/v1/chat/completions`

**Headers**:
```
Authorization: Bearer {OPENAI_API_KEY}
Content-Type: application/json
```

**Request Body** (Task Extraction):
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "{SYSTEM_PROMPT}"
    },
    {
      "role": "user",
      "content": "User transcript here..."
    }
  ],
  "response_format": {
    "type": "json_object"
  },
  "temperature": 0.3,
  "max_tokens": 1000
}
```

**Response**:
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1711234567,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{JSON structured task data}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  }
}
```

**Error Handling**:
- 400: Invalid request format
- 401: Invalid API key
- 429: Rate limit exceeded
- 500: OpenAI service error
- 503: Service temporarily unavailable

---

### Alternative OpenAI API Method: Function Calling

**Request Body** (Using Function Calling for structured output):
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "You are a task extraction assistant..."
    },
    {
      "role": "user",
      "content": "User transcript"
    }
  ],
  "functions": [
    {
      "name": "extract_tasks",
      "description": "Extract actionable tasks from transcript",
      "parameters": {
        "type": "object",
        "properties": {
          "clarity_score": {
            "type": "integer",
            "description": "Clarity of input (1-10)"
          },
          "tasks": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "text": {"type": "string"},
                "original_thought_snippet": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
              }
            }
          },
          "needs_clarification": {"type": "boolean"},
          "follow_up_question": {"type": "string"}
        },
        "required": ["clarity_score", "tasks", "needs_clarification"]
      }
    }
  ],
  "function_call": {"name": "extract_tasks"}
}
```

---

## API Key Management Best Practices

### Security
1.  Never commit `.env` to git (add to `.gitignore`)
2.  Use environment variables, never hardcode keys
3.  Rotate API keys regularly
4.  Use read-only keys when possible (not applicable for OpenAI)
5.  Monitor API usage for anomalies

### Rate Limiting
OpenAI Rate Limits (as of 2026):
- **Whisper**: 50 requests/minute
- **GPT-4o**: 5,000 requests/minute (varies by tier)
- **Token limits**: Varies by payment tier

### Cost Monitoring
Implement tracking for:
- Total API calls per day
- Token usage per request
- Cost estimation per session

---

## Testing Endpoints

### Test Case A: Clear Input
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@test_clear.m4a" \
  -H "Content-Type: multipart/form-data"
```

**Expected**: 
- `clarity_score >= 6`
- `needs_clarification = false`
- 2+ tasks extracted

---

### Test Case B: Cluttered Input
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@test_cluttered.m4a" \
  -H "Content-Type: multipart/form-data"
```

**Expected**:
- `clarity_score < 6`
- `needs_clarification = true`
- `follow_up_question` is present
- `tasks` array is empty

---

## Error Response Format (All Endpoints)

```json
{
  "error": {
    "code": "TRANSCRIPTION_FAILED",
    "message": "Failed to transcribe audio file",
    "details": "OpenAI API returned 429: Rate limit exceeded",
    "timestamp": "2026-03-28T10:30:00Z"
  }
}
```

**Standard Error Codes**:
- `INVALID_FILE_FORMAT`: Unsupported audio format
- `FILE_TOO_LARGE`: Audio file exceeds size limit
- `TRANSCRIPTION_FAILED`: Whisper API error
- `TASK_EXTRACTION_FAILED`: GPT-4o API error
- `SESSION_NOT_FOUND`: Invalid session_id
- `TASK_NOT_FOUND`: Invalid task_id
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_SERVER_ERROR`: Unexpected error

---

## Optional Enhancements (Future Phases)

### User Authentication (Optional)
**API**: Custom JWT or OAuth2

**Additional Environment Variables**:
```env
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Email/SMS Notifications (Optional)
**APIs**: SendGrid, Twilio, or similar

**Additional API Keys**:
```env
SENDGRID_API_KEY=SG.xxx           # For email reminders
TWILIO_ACCOUNT_SID=ACxxx          # For SMS reminders
TWILIO_AUTH_TOKEN=xxx
```

### Calendar Integration (Optional)
**APIs**: Google Calendar API, Microsoft Graph API

**Additional API Keys**:
```env
GOOGLE_CALENDAR_CLIENT_ID=xxx
GOOGLE_CALENDAR_CLIENT_SECRET=xxx
```

---

## Quick Start Checklist

### Step 1: Get API Keys
- [ ] Create OpenAI account at https://platform.openai.com/
- [ ] Generate API key (starts with `sk-proj-...`)
- [ ] Add billing information (required for API usage)
- [ ] Copy API key to `.env` file

### Step 2: Set Up Environment
- [ ] Create `.env` file with `OPENAI_API_KEY`
- [ ] Add `.env` to `.gitignore`
- [ ] Install Python dependencies: `pip install openai fastapi python-multipart sqlmodel`

### Step 3: Test API Access
```python
# test_openai.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test Whisper
with open("test.mp3", "rb") as f:
    result = client.audio.transcriptions.create(model="whisper-1", file=f)
    print("Whisper works:", result.text[:50])

# Test GPT-4o
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Say hello"}]
)
print("GPT-4o works:", completion.choices[0].message.content)
```

### Step 4: Monitor Usage
- Visit https://platform.openai.com/usage
- Set up usage alerts
- Monitor costs daily during development

---

## Cost Estimation (MVP Testing)

Assuming 100 test sessions during development:

**Whisper** (100 sessions × 1 minute average):
- 100 minutes × $0.006/min = **$0.60**

**GPT-4o** (100 sessions × 2 API calls average):
- Input: 200 calls × 200 tokens × $5/1M = **$0.20**
- Output: 200 calls × 150 tokens × $15/1M = **$0.45**

**Total MVP Development Cost**: ~**$1.25**

**Production Estimate** (1000 users/month, 5 sessions each):
- Whisper: 5000 sessions × 1 min × $0.006 = **$30**
- GPT-4o: 10,000 calls × (input $5 + output $2.25) = **$72.50**

**Total Monthly Production Cost**: ~**$102.50** for 5,000 sessions

---

## Summary

### Required API Keys by Phase

| Phase | Team Member | API Key Needed | Where to Get It |
|-------|-------------|----------------|-----------------|
| Phase 1 | Person 3 (Audio) | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Phase 2 | Person 1 (Architect) | `OPENAI_API_KEY` | (Same as above) |
| Phase 3 | Person 2 (Data) | None | Local SQLite database |
| Phase 4 | All | `OPENAI_API_KEY` | (Same as above) |

### Total Unique API Keys Required: **1** (OpenAI)

### Next Steps
1. Create OpenAI account and get API key
2. Set up `.env` file with the key
3. Install dependencies: `pip install openai fastapi python-multipart sqlmodel uvicorn`
4. Create project structure:
   ```
   clarityvoice/
   ├── main.py                 # FastAPI app entry point
   ├── .env                    # API keys (DO NOT COMMIT)
   ├── .env.example            # Template for .env
   ├── requirements.txt        # Python dependencies
   ├── services/
   │   ├── transcription.py    # Person 3: Whisper integration
   │   ├── task_extraction.py  # Person 1: GPT-4o integration
   │   └── prompts.py          # System prompts
   ├── models/
   │   ├── schemas.py          # Pydantic models
   │   └── database.py         # SQLModel tables
   ├── api/
   │   ├── endpoints.py        # FastAPI routes
   │   └── dependencies.py     # Shared dependencies
   ├── tests/
   │   ├── test_transcription.py
   │   ├── test_extraction.py
   │   └── test_audio/         # Sample audio files
   └── temp/                   # Temporary audio storage
   ```
5. Begin implementation with Person 3 (audio upload/transcription)
