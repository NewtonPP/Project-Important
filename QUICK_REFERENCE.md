# ClarityVoice - Quick Reference Card

## Start Server
```bash
./start.sh
# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Main API Call
```bash
# Upload audio, get tasks
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@myaudio.mp3" | jq .
```

## Response Types

### Clear Input (score >= 6)
```json
{
  "clarity_score": 8,
  "needs_clarification": false,
  "tasks": [{"text": "Buy eggs", ...}]
}
```

### Unclear Input (score < 6)
```json
{
  "clarity_score": 4,
  "needs_clarification": true,
  "tasks": [],
  "follow_up_question": "What would you like to focus on?"
}
```

## Key Files

| File | Purpose |
|------|---------|
| main.py | FastAPI app |
| config.py | Settings |
| services/transcription.py | Whisper |
| services/task_extraction.py | GPT-4o |
| api/endpoints.py | Routes |
| models/database.py | DB tables |

## Test Commands
```bash
# Run tests
pytest tests/ -v

# Check health
curl http://localhost:8000/health

# List sessions
curl http://localhost:8000/api/v1/sessions | jq .

# Update task
curl -X PATCH http://localhost:8000/api/v1/tasks/{id} \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true}'
```

## Environment Setup
```bash
# .env file
OPENAI_API_KEY=sk-proj-your-actual-key-here
DATABASE_URL=sqlite:///./clarityvoice.db
MAX_UPLOAD_SIZE_MB=25
```

## Troubleshooting

**Server won't start?**
→ Check `.env` has valid API key

**"Module not found"?**
→ Run `pip install -r requirements.txt`

**API errors?**
→ Check OpenAI billing configured

**Tests failing?**
→ Run with verbose: `pytest tests/ -v -s`

## Cost
~$0.01 per session (Whisper + GPT-4o)

## Team Assignments

**Person 1**: services/task_extraction.py, services/prompts.py  
**Person 2**: models/database.py, models/schemas.py  
**Person 3**: services/transcription.py, audio upload logic  

---

**Ready to use!** Just add your OpenAI API key and run `./start.sh`
