# ClarityVoice Architecture

## System Overview

```mermaid
graph TB
    subgraph Client[Client Layer]
        User[User/Frontend]
    end
    
    subgraph API[API Layer - FastAPI]
        Health[GET /health]
        Process[POST /api/v1/process]
        Extract[POST /api/v1/tasks/extract]
        Refine[POST /api/v1/tasks/refine]
        Sessions[GET /api/v1/sessions]
        GetSession[GET /api/v1/sessions/:id]
        UpdateTask[PATCH /api/v1/tasks/:id]
        DeleteTask[DELETE /api/v1/tasks/:id]
    end
    
    subgraph Services[Service Layer]
        TranscriptionSvc[Transcription Service]
        ExtractionSvc[Task Extraction Service]
        PromptEngine[Prompt Engine]
    end
    
    subgraph External[External APIs]
        Whisper[OpenAI Whisper API]
        GPT4o[OpenAI GPT-4o API]
    end
    
    subgraph Data[Data Layer]
        DB[(SQLite Database)]
        TempStorage[Temp File Storage]
    end
    
    User --> Process
    Process --> TranscriptionSvc
    Process --> ExtractionSvc
    
    TranscriptionSvc --> Whisper
    TranscriptionSvc --> TempStorage
    
    ExtractionSvc --> PromptEngine
    PromptEngine --> GPT4o
    
    Process --> DB
    Sessions --> DB
    UpdateTask --> DB
```

## Request Flow: Main Endpoint

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Trans as Transcription Service
    participant Extract as Extraction Service
    participant Whisper as OpenAI Whisper
    participant GPT as OpenAI GPT-4o
    participant DB as Database
    
    Client->>API: POST /process (audio file)
    API->>API: Validate file format & size
    API->>Trans: transcribe_audio(file_path)
    Trans->>Whisper: POST /transcriptions
    Whisper-->>Trans: transcript text
    Trans-->>API: transcript
    
    API->>Extract: extract_tasks(transcript)
    Extract->>GPT: POST /chat/completions
    Note over Extract,GPT: System: Task Architect Prompt<br/>User: transcript
    GPT-->>Extract: JSON (score, tasks, clarification)
    Extract-->>API: extraction_result
    
    API->>DB: Save session + tasks
    DB-->>API: Success
    
    API-->>Client: SessionResponse
    
    Note over Client: If needs_clarification:<br/>tasks=[], follow_up_question present<br/><br/>Else:<br/>tasks=[...], ready to use
```

## Clarification Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Extract as Extraction Service
    participant GPT as OpenAI GPT-4o
    participant DB as Database
    
    Note over Client: First request had<br/>clarity_score < 6
    
    Client->>API: POST /tasks/refine<br/>(session_id, answer)
    API->>DB: Fetch original session
    DB-->>API: session (with transcript)
    
    API->>Extract: refine_with_clarification()<br/>(transcript, question, answer)
    Extract->>GPT: POST /chat/completions
    Note over Extract,GPT: Context: original + clarification<br/>Extract tasks focusing on user's priority
    GPT-->>Extract: Refined JSON with tasks
    Extract-->>API: refinement_result
    
    API->>DB: Update session + add new tasks
    DB-->>API: Success
    
    API-->>Client: SessionResponse with tasks
```

## Data Model

```mermaid
erDiagram
    SESSIONS ||--o{ TASKS : contains
    
    SESSIONS {
        string id PK
        string raw_transcript
        int clarity_score
        bool needs_clarification
        string follow_up_question
        datetime created_at
        datetime updated_at
    }
    
    TASKS {
        string id PK
        string session_id FK
        string text
        bool is_completed
        string original_thought_snippet
        int estimated_duration_minutes
        string priority
        datetime created_at
        datetime updated_at
    }
```

## Service Architecture

```mermaid
graph LR
    subgraph TranscriptionService[Transcription Service]
        TS1[transcribe_audio]
        TS2[Retry Logic]
        TS3[cleanup_audio_file]
    end
    
    subgraph ExtractionService[Task Extraction Service]
        ES1[extract_tasks]
        ES2[refine_with_clarification]
        ES3[_call_gpt4o]
        ES4[_validate_result]
    end
    
    subgraph PromptEngine[Prompt Engine]
        P1[TASK_ARCHITECT_PROMPT]
        P2[CLARIFICATION_REFINEMENT_PROMPT]
    end
    
    TS1 --> TS2
    TS2 --> Whisper[Whisper API]
    TS1 --> TS3
    
    ES1 --> ES3
    ES2 --> ES3
    ES3 --> P1
    ES3 --> P2
    ES3 --> GPT[GPT-4o API]
    ES3 --> ES4
```

## Error Handling Flow

```mermaid
flowchart TD
    Start[Request Received]
    Start --> Validate{Validate Input}
    
    Validate -->|Invalid| Error400[400 Bad Request]
    Validate -->|Valid| Process[Process Request]
    
    Process --> External{Call External API}
    External -->|Rate Limit| Retry{Retry Count < 3?}
    External -->|Timeout| Retry
    External -->|500/503| Retry
    External -->|Success| Save[Save to DB]
    External -->|4xx Error| Error500[500 Internal Error]
    
    Retry -->|Yes| Wait[Exponential Backoff]
    Wait --> External
    Retry -->|No| Error429[429 Rate Limit]
    
    Save --> Return[Return Success Response]
    
    Error400 --> Log[Log Error]
    Error429 --> Log
    Error500 --> Log
    
    Log --> ErrorResponse[Return ErrorResponse]
```

## File Organization

```
Project-Important/
│
├── main.py                 ← FastAPI app, startup logic
├── config.py              ← Settings, env vars, validation
│
├── api/                   ← HTTP layer
│   ├── endpoints.py       ← Route handlers (8 endpoints)
│   └── dependencies.py    ← Global error handling
│
├── services/              ← Business logic
│   ├── transcription.py   ← Whisper integration + retry
│   ├── task_extraction.py ← GPT-4o integration + validation
│   └── prompts.py         ← System prompts for LLM
│
├── models/                ← Data models
│   ├── database.py        ← SQLModel ORM (sessions, tasks)
│   └── schemas.py         ← Pydantic request/response
│
└── tests/                 ← Test suite
    ├── test_transcription.py
    ├── test_extraction.py
    └── test_endpoints.py
```

## Component Responsibilities

### API Layer (api/)
- Route definitions
- Request/response handling
- Input validation
- Exception handling
- HTTP status mapping

### Service Layer (services/)
- External API integration
- Business logic
- Retry mechanisms
- Data transformation
- Prompt management

### Model Layer (models/)
- Database schema
- ORM mappings
- Request/response contracts
- Data validation

### Test Layer (tests/)
- Unit tests for services
- Integration tests for endpoints
- Mock external APIs
- Test fixtures

## Configuration Management

```mermaid
flowchart LR
    EnvFile[.env file] --> Settings[Settings Class]
    Settings --> Validation{Validate}
    Validation -->|Valid| App[Application]
    Validation -->|Invalid| Error[Startup Error]
    
    Settings --> OpenAIClient[OpenAI Client]
    Settings --> Database[Database Engine]
    Settings --> FileSystem[Temp Directory]
```

## Deployment Considerations

### Current State (MVP)
- Single-server deployment
- SQLite database (file-based)
- Local file storage for audio
- No horizontal scaling

### Future Enhancements
- PostgreSQL for multi-server
- S3/Cloud Storage for audio
- Redis for caching
- Load balancer support
- Background job queue

## Security Model

### Current (MVP)
- No authentication
- Local development only
- CORS enabled for localhost

### Future
- JWT authentication
- User-specific sessions
- Rate limiting per user
- API key rotation
- Audit logging
