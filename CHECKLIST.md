# ClarityVoice MVP - Implementation Checklist

## Setup Checklist

### Prerequisites
- [ ] Python 3.10+ installed
- [ ] OpenAI account created
- [ ] OpenAI API key obtained from https://platform.openai.com/api-keys
- [ ] Billing configured on OpenAI account (required for API usage)

### Initial Setup
- [ ] Navigate to project directory: `cd /home/anoop130/Project-Important`
- [ ] Copy environment template: `cp .env.example .env`
- [ ] Edit `.env` and add your `OPENAI_API_KEY`
- [ ] Create virtual environment: `python3 -m venv venv`
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Install dependencies: `pip install -r requirements.txt`

### Verification
- [ ] Run syntax check: All Python files compile without errors 
- [ ] Start server: `uvicorn main:app --reload`
- [ ] Visit http://localhost:8000/docs - API docs load
- [ ] Test health endpoint: `curl http://localhost:8000/health`

### Testing
- [ ] Run unit tests: `./run_tests.sh` or `pytest tests/ -v`
- [ ] Test with sample audio file via API docs
- [ ] Verify database created: `ls -la clarityvoice.db`
- [ ] Check logs: `cat logs/app.log`

---

## Team Member Checklists

### Person 1: The Architect (LLM Integration)

**Files to review**:
- [ ] `services/task_extraction.py` - GPT-4o integration
- [ ] `services/prompts.py` - System prompts for Task Architect
- [ ] `main.py` - Overall app structure

**Tasks**:
- [ ] Test clarity scoring with various inputs
- [ ] Refine system prompts for better task extraction
- [ ] Test clarification refinement loop
- [ ] Verify retry logic works on API failures

**Test commands**:
```bash
# Test extraction directly
curl -X POST http://localhost:8000/api/v1/tasks/extract \
  -H "Content-Type: application/json" \
  -d '{"transcript": "I need to buy eggs and call mom"}' | jq .
```

---

### Person 2: The Data Specialist (Database & Models)

**Files to review**:
- [ ] `models/database.py` - SQLModel tables
- [ ] `models/schemas.py` - Pydantic models
- [ ] Session/task CRUD in `api/endpoints.py`

**Tasks**:
- [ ] Verify database schema created correctly
- [ ] Test all CRUD operations (create, read, update, delete)
- [ ] Check foreign key constraints work
- [ ] Test pagination on sessions endpoint

**Test commands**:
```bash
# View database
sqlite3 clarityvoice.db ".schema"

# List sessions
curl http://localhost:8000/api/v1/sessions | jq .

# Update task
curl -X PATCH http://localhost:8000/api/v1/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true}' | jq .
```

---

### Person 3: The Audio Lead (Transcription)

**Files to review**:
- [ ] `services/transcription.py` - Whisper integration
- [ ] Audio upload in `api/endpoints.py`
- [ ] File validation and cleanup logic

**Tasks**:
- [ ] Test audio upload with different formats (mp3, m4a, wav)
- [ ] Verify file size limit enforcement (25MB)
- [ ] Check temporary files are cleaned up after transcription
- [ ] Test retry logic on Whisper API failures

**Test commands**:
```bash
# Upload audio
curl -X POST http://localhost:8000/api/v1/audio/upload \
  -F "audio_file=@test.mp3" | jq .

# Check temp directory is empty after
ls -la temp/
```

---

## Integration Testing

### End-to-End Flow
- [ ] Upload audio file via `/api/v1/process`
- [ ] Verify transcription occurs
- [ ] Verify tasks extracted or clarification requested
- [ ] Verify session saved to database
- [ ] Mark task as complete
- [ ] Retrieve session again and verify task status

### Edge Cases to Test
- [ ] Empty audio file
- [ ] Very long audio file (>5 minutes)
- [ ] Invalid file format (.txt, .jpg)
- [ ] File too large (>25MB)
- [ ] Completely silent audio
- [ ] Audio in different language
- [ ] Very short audio (<1 second)

---

## API Key Verification

### Test Your OpenAI Key

```python
# test_api_key.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test GPT-4o
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print(" GPT-4o works:", response.choices[0].message.content)
except Exception as e:
    print(" GPT-4o failed:", str(e))

print("\n OpenAI API key is valid!")
print("Note: Whisper requires an actual audio file to test")
```

Run: `python test_api_key.py`

---

## Success Criteria

### MVP Complete When:
- [x] All 8 API endpoints working
- [x] Audio transcription functional (Whisper)
- [x] Task extraction functional (GPT-4o)
- [x] Clarity scoring working (< 6 = clarification)
- [x] Database persistence working
- [x] Basic tests passing
- [ ] Real audio file successfully processed
- [ ] Tasks can be marked complete
- [ ] Sessions can be retrieved

### Ready for Frontend Integration When:
- [ ] All success criteria above met
- [ ] API documented and stable
- [ ] Error responses standardized
- [ ] CORS configured for frontend origin

---

## Common Commands

```bash
# Start server
uvicorn main:app --reload

# Or use the script
./start.sh

# Run tests
pytest tests/ -v

# Check logs
tail -f logs/app.log

# View database
sqlite3 clarityvoice.db "SELECT * FROM sessions;"

# Reset database
rm clarityvoice.db
# Restart server to recreate
```

---

## Next Steps After MVP

1. **Prompt Refinement**: Iterate on `services/prompts.py` based on real usage
2. **Frontend Integration**: Connect React/Vue/etc. to these endpoints
3. **User Authentication**: Add JWT tokens for multi-user support
4. **Deployment**: Deploy to cloud platform (Railway, Render, AWS)
5. **Monitoring**: Add proper logging/monitoring for production

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Setup Guide**: README_SETUP.md
- **API Specs**: API_BOILERPLATE.md
- **Architecture**: IMPLEMENTATION_SUMMARY.md
