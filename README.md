# ClarityVoice Backend

Transform emotional voice brain dumps into actionable task lists using AI.

## Quick Start

```bash
# 1. Add your OpenAI API key to .env
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-proj-your-key

# 2. Run the backend
./start.sh
```

API docs: http://localhost:8000/docs

## What It Does

1. Upload audio (voice recording of your thoughts)
2. Transcribe using OpenAI Whisper
3. Extract tasks using GPT-4o with clarity scoring
4. Get results: Clean task list or clarification question

## API Endpoints

- `POST /api/v1/process` - Main endpoint (audio to tasks)
- `GET /api/v1/sessions` - List sessions
- `PATCH /api/v1/tasks/{id}` - Update task status
- More endpoints in [API_BOILERPLATE.md](API_BOILERPLATE.md)

## Requirements

- Python 3.10+
- OpenAI API key (get from https://platform.openai.com/api-keys)

## Documentation

- [Setup Guide](README_SETUP.md) - Detailed installation
- [API Boilerplate](API_BOILERPLATE.md) - Complete API specs
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Architecture overview

## Testing

```bash
./run_tests.sh
```

## Cost

Approximately $0.01 per audio session (Whisper + GPT-4o)

---

Built for mental health support and executive dysfunction management.
