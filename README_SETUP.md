# ClarityVoice Backend - Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- OpenAI API key

### 2. Get Your OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create new secret key**
5. Copy the key (starts with `sk-proj-...`)
6. **Important**: Add billing information in your OpenAI account (required for API usage)

### 3. Installation

```bash
# Clone or navigate to the project directory
cd /home/anoop130/Project-Important

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

**Update this line in `.env`**:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 5. Run the Server

```bash
# Start the FastAPI server
uvicorn main:app --reload

# Server will start at: http://localhost:8000
# API docs available at: http://localhost:8000/docs
```

### 6. Test the API

**Option A: Use the interactive docs**
- Open http://localhost:8000/docs
- Try the `/health` endpoint first
- Test `/api/v1/process` with an audio file

**Option B: Use curl**

```bash
# Health check
curl http://localhost:8000/health

# Test with audio file
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@path/to/your/audio.mp3"
```

---

## API Endpoints

### Main Workflow Endpoint

**POST /api/v1/process**
- Upload audio file
- Returns: Session with extracted tasks or clarification request

### Individual Component Endpoints

**POST /api/v1/audio/upload**
- Upload audio, get transcript only

**POST /api/v1/tasks/extract**
- Send transcript text, get task extraction

**POST /api/v1/tasks/refine**
- Submit clarification answer, get refined tasks

### Session Management

**GET /api/v1/sessions**
- List all sessions (paginated)

**GET /api/v1/sessions/{session_id}**
- Get specific session with all tasks

### Task Management

**PATCH /api/v1/tasks/{task_id}**
- Update task completion status

**DELETE /api/v1/tasks/{task_id}**
- Delete a task

---

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_endpoints.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Manual Testing Examples

**Test Case A - Clear Input**:
Record yourself saying: "I need to go to the grocery store for eggs and then call my mom at 5."

Expected result:
- `clarity_score >= 6`
- 2 tasks extracted
- `needs_clarification = false`

**Test Case B - Cluttered Input**:
Record yourself saying: "Ugh, I'm so overwhelmed. The house is a mess, and I keep thinking about that project at work, but I don't know where to start."

Expected result:
- `clarity_score < 6`
- 0 tasks (empty array)
- `needs_clarification = true`
- `follow_up_question` provided

---

## Project Structure

```
.
├── main.py                      # FastAPI application entry point
├── config.py                    # Configuration & settings
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .env                         # Your API keys (DO NOT COMMIT)
├── .gitignore                   # Git ignore patterns
├── api/
│   ├── endpoints.py             # All API routes
│   └── dependencies.py          # Global error handlers
├── services/
│   ├── transcription.py         # Whisper integration (Person 3)
│   ├── task_extraction.py       # GPT-4o integration (Person 1)
│   └── prompts.py               # System prompts
├── models/
│   ├── database.py              # SQLModel ORM (Person 2)
│   └── schemas.py               # Pydantic models
├── tests/
│   ├── test_transcription.py    # Transcription tests
│   ├── test_extraction.py       # Extraction tests
│   └── test_endpoints.py        # API endpoint tests
├── temp/                        # Temporary audio storage
└── logs/                        # Application logs
```

---

## Team Member Focus Areas

### Person 1: The Architect (Integration & LLM Logic)
**Files to focus on**:
- `services/task_extraction.py` - GPT-4o integration
- `services/prompts.py` - Prompt engineering
- `main.py` - Overall orchestration

### Person 2: The Data Specialist (Storage & Schemas)
**Files to focus on**:
- `models/database.py` - Database tables
- `models/schemas.py` - API request/response models
- Session and task CRUD operations in `api/endpoints.py`

### Person 3: The Audio Lead (Ingestion & Transcription)
**Files to focus on**:
- `services/transcription.py` - Whisper integration
- Audio upload handling in `api/endpoints.py`
- File validation and cleanup logic

---

## Common Issues & Solutions

### Issue: "OPENAI_API_KEY must be set"
**Solution**: Update your `.env` file with a valid OpenAI API key

### Issue: "Rate limit exceeded"
**Solution**: You've hit OpenAI's rate limit. Wait a minute and try again. Consider upgrading your OpenAI tier.

### Issue: "Module not found"
**Solution**: Ensure you've installed dependencies: `pip install -r requirements.txt`

### Issue: "Permission denied" on temp/ or logs/
**Solution**: These directories are auto-created, but ensure write permissions

---

## Database

The SQLite database (`clarityvoice.db`) is created automatically on first run.

**To reset the database**:
```bash
rm clarityvoice.db
# Restart the server to recreate tables
```

**To view database contents**:
```bash
sqlite3 clarityvoice.db
# Inside sqlite:
.tables
SELECT * FROM sessions;
SELECT * FROM tasks;
.quit
```

---

## Cost Monitoring

Monitor your OpenAI usage at: https://platform.openai.com/usage

**Estimated costs**:
- Whisper: ~$0.006 per minute of audio
- GPT-4o: ~$0.01-0.02 per transcript processing

For 100 test sessions: ~$2-3 total

---

## Next Steps

1. **Add your OpenAI API key** to `.env`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run the server**: `uvicorn main:app --reload`
4. **Test with the docs**: http://localhost:8000/docs
5. **Upload a test audio file** via `/api/v1/process`

---

## API Documentation

Once the server is running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

---

## Troubleshooting

If you encounter issues:
1. Check `logs/app.log` for detailed error messages
2. Verify your OpenAI API key is valid
3. Ensure billing is set up on your OpenAI account
4. Check that all dependencies are installed correctly

For questions or issues, check the implementation files for inline documentation.
