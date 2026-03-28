ClarityVoice Backend MVP: 3-Person Team Sprint

Project Onboarding Summary

ClarityVoice is a mental health-focused "Cognitive Offloading" tool. Users often struggle with "Executive Dysfunction"a state where mental clutter makes it impossible to start tasks.

The Mission: Turn a messy, emotional voice "brain dump" into a structured, low-friction task list.
How it works: 1. The user speaks freely (venting, worrying, listing).
2. The backend transcribes this via Whisper.
3. GPT-4o acts as a "Task Architect," stripping away the emotional noise and anxiety to find actionable items.
4. If the input is too vague, the AI asks a single clarifying question instead of overwhelming the user with a bad list.

Person 1: The Architect (Integration & LLM Logic)

Focus: OpenAI SDK orchestration and the "Clutter-to-Task" reasoning engine.

Tasks:

Initialize Project Environment:

Set up main.py with FastAPI boilerplate.

Configure .env management (OpenAI API Key, App Secret).

Implement a global error handler for API failures.

The "Task Architect" Service:

Create a service that takes a raw string (transcript) and sends it to gpt-4o.

Prompt Engineering: Craft the "System Prompt" that:

Filters "Emotional Noise" vs. "Actionable Items."

Forces the output into a specific JSON schema (using OpenAI Function Calling or JSON Mode).

Calculates a clarity_score (1-10) based on how vague the input is.

Refinement Loop Logic:

Write logic that checks: if clarity_score < 6, trigger a generate_clarification_question prompt instead of returning tasks.

Final Endpoint Assembly:

Connect the Transcriber (Person 3) output to the Architect Service.

Person 2: The Data Specialist (Storage & Schemas)

Focus: Database persistence and Pydantic models for the API.

Tasks:

Define Pydantic Models:

TaskItem: (id, text, is_completed, original_thought_snippet).

SessionResponse: (session_id, tasks: List[TaskItem], needs_clarification: bool, follow_up_question: str, clarity_score: int).

Database Setup (SQLite for MVP):

Set up SQLAlchemy or SQLModel.

Table Sessions: Store the raw transcript and the generated JSON output.

Table Tasks: Store individual task states so they can be "checked off" later.

CRUD Operations:

create_session(transcript, result_json)

get_session_tasks(session_id)

update_task_status(task_id, status)

Mock Data Injection:

Create a script to populate the DB with 3 "cluttered" examples for testing Person 1's prompts.

Person 3: The Audio Lead (Ingestion & Transcription)

Focus: Handling the physical audio file and OpenAI Whisper integration.

Tasks:

Audio Upload Endpoint:

Create POST /upload-audio.

Handle UploadFile objects and save them temporarily to a temp/ directory.

Validate file types (m4a, mp3, wav, webm).

OpenAI Whisper Integration:

Implement the transcribe_audio(file_path) function using client.audio.transcriptions.create.

Add a simple retry mechanism (exponential backoff) for OpenAI API timeouts.

Preprocessing (Optional):

Use pydub or ffmpeg to ensure audio is converted to a standard format if needed.

Cleanup Logic:

Ensure temporary audio files are deleted from the server immediately after transcription to save space.

Shared MVP Workflow (The "Happy Path")

Audio Lead receives file -> Returns raw text transcript.

Architect receives transcript -> Asks GPT-4o for JSON tasks + Score.

Data Specialist saves the transcript + Resulting JSON -> Returns SessionResponse.

Testing Protocol

Test Case A (Clear): "I need to go to the grocery store for eggs and then call my mom at 5." -> Expect 2 tasks.

Test Case B (Cluttered): "Ugh, I'm so overwhelmed. The house is a mess, and I keep thinking about that project at work, but I don't know where to start. Maybe I should just clean something?" -> Expect Clarity Score < 5 and a follow-up question.
