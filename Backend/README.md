# ClarityVoice Backend

Transform messy voice brain dumps into clear, actionable task lists.

## What It Does

**Input**: Overwhelming voice recording ("Everything is too much...")
**Output**: Organized, prioritized task list

Built for people experiencing executive dysfunction.

---

## Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt


# Add your OpenAI API key
echo "OPENAI_API_KEY=sk-proj-your-key-here" > .env

# Start server
uvicorn main:app --port 8002
```

### 2. Test

Open http://localhost:8002/docs and try uploading an audio file.

### 3. Environment Variables

```
OPENAI_API_KEY=test-key-change-me
DATABASE_URL=sqlite:///./clarityvoice.db
MAX_UPLOAD_SIZE_MB=25
TEMP_AUDIO_DIR=./temp
ENVIRONMENT=development
LOG_LEVEL=INFO
GOOGLE_CLIENT_ID=test-google-client-id.apps.googleusercontent.com
JWT_SECRET=local-dev-super-secret-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60
```

---

## Documentation

- **FRONTEND_GUIDE.md** - Complete integration guide for frontend engineers
- **API.md** - API endpoint reference with examples
- **ARCHITECTURE.md** - System design and data flow diagrams

---

## Features

- Audio transcription (OpenAI Whisper)
- Smart task extraction (GPT-4o)
- Clarity scoring (1-10 scale)
- Adaptive clarification flow
- Guided category breakdown for very vague inputs
- Task management (complete, delete)
- Session persistence (SQLite)

---

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite + SQLModel
- **AI**: OpenAI (Whisper + GPT-4o)
- **Testing**: pytest

---

## API Endpoints

- `POST /api/v1/process` - Main endpoint (audio → tasks)
- `POST /api/v1/tasks/refine` - Clarification refinement
- `POST /api/v1/tasks/guided-breakdown` - Category-specific extraction
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{id}` - Get session with tasks
- `PATCH /api/v1/tasks/{id}` - Update task status
- `DELETE /api/v1/tasks/{id}` - Delete task

See `API.md` for detailed specs.

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test with edge cases
python3 comprehensive_test.py
```

---

## Cost Estimates

- Clear input: ~$0.016 per request
- With clarification: ~$0.026 per request
- Full breakdown: ~$0.056 per request
- Average: ~$0.020 per request

---

## Frontend Integration

Read `FRONTEND_GUIDE.md` for:

- Complete implementation flow
- UI/UX requirements
- Sample React code
- TypeScript types
- Error handling

---

## License

MIT
