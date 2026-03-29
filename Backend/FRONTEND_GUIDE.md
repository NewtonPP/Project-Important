# Frontend Integration Guide

## Overview

ClarityVoice transforms voice recordings into actionable task lists. The system uses a smart clarification flow with three modes:
1. **Direct extraction** (clear input)
2. **Simple clarification** (somewhat vague)
3. **Guided breakdown** (very vague, step-by-step)

---

## Required Features

### 1. Audio Recording/Upload
- Support microphone recording OR file upload
- Formats: MP3, M4A, WAV, WebM, OGG
- Max size: 25MB
- Show recording duration/file size

### 2. Task Display
- List view with checkboxes for completion
- Show priority (high/medium/low) with visual indicator
- Show time estimates
- Allow task deletion

### 3. Clarification Flow
- Display follow-up questions
- Support voice OR text input for answers
- Show loading states during API calls

### 4. Guided Breakdown Mode (New)
- Detect when `suggested_breakdown_categories` is present
- Offer user choice: "Break it down" vs "Do your best"
- Guide through categories one-by-one
- Show progress indicator (e.g., "Work 1/4")
- Accumulate tasks visually as they're extracted

---

## Implementation Flow

### Step 1: Audio Input

```javascript
// Component: AudioRecorder or FileUpload
const audioFile = await recordAudio(); // or selectFile()

// Validate
if (audioFile.size > 25 * 1024 * 1024) {
  showError("File too large (max 25MB)");
  return;
}

setLoading(true);
```

### Step 2: Process Audio

```javascript
const formData = new FormData();
formData.append('audio_file', audioFile);

const response = await fetch('http://localhost:8002/api/v1/process', {
  method: 'POST',
  body: formData
});

const data = await response.json();
setSessionId(data.session_id);
setClarityScore(data.clarity_score);
```

### Step 3: Handle Response

```javascript
if (!data.needs_clarification) {
  // Direct path: show tasks immediately
  displayTasks(data.tasks);
  setLoading(false);
  return;
}

// Clarification needed
showClarificationPrompt(data.follow_up_question);
```

### Step 4: Handle Clarification

```javascript
// User provides answer (voice or text)
const clarificationAnswer = await getUserInput();

const refineResponse = await fetch('http://localhost:8002/api/v1/tasks/refine', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    clarification_answer: clarificationAnswer
  })
});

const refined = await refineResponse.json();
```

### Step 5: Check for Breakdown

```javascript
if (!refined.suggested_breakdown_categories) {
  // Clarification was good enough
  displayTasks(refined.tasks);
  return;
}

// Offer breakdown mode
const acceptBreakdown = await showBreakdownModal(
  refined.suggested_breakdown_categories
);

if (!acceptBreakdown) {
  // User declined, show what we have (may be empty)
  displayTasks(refined.tasks);
  return;
}

// Enter breakdown mode
await guidedBreakdown(sessionId, refined.suggested_breakdown_categories);
```

### Step 6: Guided Breakdown

```javascript
async function guidedBreakdown(sessionId, categories) {
  const allTasks = [];
  
  for (let i = 0; i < categories.length; i++) {
    const category = categories[i];
    
    // Show progress
    showProgress(`${category} (${i+1}/${categories.length})`);
    
    // Ask about this category
    const categoryResponse = await getCategoryInput(
      `Let's talk about ${category}. What's going on with ${category}?`
    );
    
    // Allow skipping
    if (categoryResponse.toLowerCase().includes('nothing') || 
        categoryResponse.toLowerCase().includes('skip')) {
      continue;
    }
    
    // Extract category tasks
    const result = await fetch('http://localhost:8002/api/v1/tasks/guided-breakdown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        category: category,
        category_response: categoryResponse
      })
    });
    
    const categoryData = await result.json();
    
    // Show tasks as they're extracted
    displayNewTasks(categoryData.tasks);
    allTasks.push(...categoryData.tasks);
  }
  
  // Final view: all accumulated tasks
  const finalSession = await fetch(`http://localhost:8002/api/v1/sessions/${sessionId}`);
  const sessionData = await finalSession.json();
  
  displayTasksSummary(sessionData.tasks);
}
```

### Step 7: Task Management

```javascript
// Mark task as complete
async function toggleTask(taskId, isCompleted) {
  await fetch(`http://localhost:8002/api/v1/tasks/${taskId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_completed: isCompleted })
  });
  
  // Refresh task list
  refreshTasks();
}

// Delete task
async function deleteTask(taskId) {
  await fetch(`http://localhost:8002/api/v1/tasks/${taskId}`, {
    method: 'DELETE'
  });
  
  // Remove from UI
  removeTaskFromUI(taskId);
}
```

---

## UI/UX Requirements

### Main Screen
- **Audio Input Button**: Large, prominent microphone icon
- **Recording Indicator**: Show duration while recording
- **Processing State**: Loading spinner with "Transcribing..." / "Extracting tasks..."

### Task List View
```
┌─────────────────────────────────────┐
│  Your Tasks                [Settings]│
├─────────────────────────────────────┤
│  [ ] [HIGH] Buy eggs (20 min)  [X] │
│  [ ] [MED]  Call mom (10 min)  [X] │
│  [✓] [LOW]  Water plants (5 min) [X]│
└─────────────────────────────────────┘
```

### Clarification Modal
```
┌─────────────────────────────────────┐
│  Need a bit more clarity...         │
├─────────────────────────────────────┤
│  "What's bothering you most         │
│   right now?"                        │
│                                      │
│  [Voice Answer] [Text Answer]       │
└─────────────────────────────────────┘
```

### Breakdown Mode
```
┌─────────────────────────────────────┐
│  Let's break this down              │
│  Step 1 of 4: Work                  │
├─────────────────────────────────────┤
│  What's going on with work?         │
│                                      │
│  [Voice] [Text] [Skip This]         │
│                                      │
│  Tasks from this category:          │
│  [ ] Respond to emails              │
│  [ ] Finish report                  │
└─────────────────────────────────────┘
```

---

## UI States

### State 1: Idle
- Show audio input button
- Optional: Show recent sessions

### State 2: Recording
- Animated microphone icon
- Show duration counter
- Cancel button

### State 3: Processing
- Loading spinner
- "Transcribing your audio..."
- Then "Extracting tasks..."

### State 4: Tasks Ready (clarity >= 5)
- Display task list
- Show clarity score (optional)
- Enable task management

### State 5: Clarification Needed (clarity < 5)
- Display follow-up question
- Show input options (voice/text)
- Back button to cancel

### State 6: Breakdown Mode
- Show category progress
- One category at a time
- Show accumulated tasks in background
- Allow category skip

---

## Component Suggestions

### Required Components

1. **AudioRecorder**
   - Uses Web Audio API or RecordRTC
   - Exports as MP3/WAV
   - Shows waveform (optional)

2. **TaskList**
   - Renders TaskItem array
   - Handles checkbox toggling
   - Supports delete action

3. **ClarificationModal**
   - Displays question
   - Voice/text input toggle
   - Submit button

4. **BreakdownWizard**
   - Multi-step form (one per category)
   - Progress indicator
   - Task accumulation view

5. **TaskItem**
   - Checkbox for completion
   - Priority badge (color-coded)
   - Time estimate
   - Delete icon

---

## Styling Recommendations

### Priority Colors
- **High**: Red/Orange (#EF4444)
- **Medium**: Yellow (#F59E0B)
- **Low**: Green (#10B981)

### Loading States
- Use skeleton screens for task list
- Spinner for API calls
- Progress bar for breakdown (step 1/4, 2/4, etc.)

### Clarity Score Visualization (Optional)
- 1-4: Red indicator "Very vague"
- 5-6: Yellow "Somewhat clear"
- 7-10: Green "Clear"

---

## Error Handling

### Display User-Friendly Messages

```javascript
const errorMessages = {
  'INVALID_FILE_FORMAT': 'Please upload an audio file (MP3, WAV, etc.)',
  'FILE_TOO_LARGE': 'File too large. Max 25MB.',
  'SESSION_NOT_FOUND': 'Session expired. Please start over.',
  'TASK_NOT_FOUND': 'Task not found.',
  'RATE_LIMIT_EXCEEDED': 'Too many requests. Please wait a moment.',
  'TASK_EXTRACTION_FAILED': 'Failed to process audio. Please try again.'
};

function handleError(errorCode) {
  const message = errorMessages[errorCode] || 'Something went wrong. Please try again.';
  showToast(message, 'error');
}
```

---

## Input Requirements

### Audio Recording
- **Format**: Browser-supported (WebM, MP3, WAV)
- **Sample Rate**: 16kHz+ recommended
- **Channels**: Mono or stereo
- **Duration**: No strict limit, but 25MB max file size

### Clarification Answers
- **Voice**: Same as initial recording
- **Text**: Minimum 3 characters, no max
- **Allow empty**: For category skip ("nothing here")

---

## Output Handling

### Task Object Properties

**Required Fields:**
- `id`: Use for key in React lists
- `text`: Main display text
- `is_completed`: Checkbox state

**Optional Display:**
- `priority`: Show as badge/color
- `estimated_duration_minutes`: Show as "20 min"
- `original_thought_snippet`: Tooltip or expandable

**Ignore:**
- `created_at`, `updated_at`: Backend tracking only

### Session Management

**Recommended:**
- Store `session_id` in component state
- Don't persist across page refresh (MVP)
- Show "Start New Session" button after completion

---

## Sample UI Flow (React)

```jsx
function ClarityVoice() {
  const [state, setState] = useState('idle');
  const [sessionId, setSessionId] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [clarificationQ, setClarificationQ] = useState(null);
  const [breakdownCategories, setBreakdownCategories] = useState(null);

  const handleAudioUpload = async (audioFile) => {
    setState('processing');
    const result = await uploadAudio(audioFile);
    
    if (!result.needs_clarification) {
      setTasks(result.tasks);
      setState('tasks-ready');
    } else if (result.suggested_breakdown_categories) {
      setBreakdownCategories(result.suggested_breakdown_categories);
      setState('breakdown-suggested');
    } else {
      setClarificationQ(result.follow_up_question);
      setState('clarification-needed');
    }
  };

  const handleClarification = async (answer) => {
    const result = await refineTask(sessionId, answer);
    
    if (result.suggested_breakdown_categories) {
      setBreakdownCategories(result.suggested_breakdown_categories);
      setState('breakdown-suggested');
    } else {
      setTasks(result.tasks);
      setState('tasks-ready');
    }
  };

  const handleBreakdown = async () => {
    setState('breakdown-active');
    // Guide through categories
    for (const category of breakdownCategories) {
      const response = await promptCategory(category);
      await extractCategoryTasks(sessionId, category, response);
    }
    // Fetch final accumulated tasks
    const finalSession = await getSession(sessionId);
    setTasks(finalSession.tasks);
    setState('tasks-ready');
  };

  // Render based on state
  return (
    <div>
      {state === 'idle' && <AudioInput onUpload={handleAudioUpload} />}
      {state === 'processing' && <LoadingSpinner />}
      {state === 'clarification-needed' && 
        <ClarificationPrompt 
          question={clarificationQ} 
          onSubmit={handleClarification} 
        />
      }
      {state === 'breakdown-suggested' && 
        <BreakdownOffer 
          categories={breakdownCategories}
          onAccept={handleBreakdown}
          onDecline={() => setState('tasks-ready')}
        />
      }
      {state === 'breakdown-active' && 
        <BreakdownWizard 
          categories={breakdownCategories}
          sessionId={sessionId}
          onComplete={(tasks) => {
            setTasks(tasks);
            setState('tasks-ready');
          }}
        />
      }
      {state === 'tasks-ready' && 
        <TaskList tasks={tasks} onUpdate={refreshTasks} />
      }
    </div>
  );
}
```

---

## Critical Frontend Logic

### 1. Clarity Threshold

**Threshold: clarity_score < 5 triggers clarification**

Frontend should:
- Accept tasks without clarification if score >= 5
- Show clarification prompt if score < 5
- Display score to user (optional, but helpful for transparency)

### 2. Breakdown Detection

**Check for `suggested_breakdown_categories`**:

```javascript
if (response.suggested_breakdown_categories && 
    response.suggested_breakdown_categories.length > 0) {
  // Enter breakdown mode
  enterBreakdownMode(response.suggested_breakdown_categories);
}
```

### 3. Category Loop

**Important**: Call `/tasks/guided-breakdown` for EACH category:

```javascript
for (const category of categories) {
  // Prompt user
  const response = await askUser(`What about ${category}?`);
  
  // Extract tasks for this category
  await POST('/api/v1/tasks/guided-breakdown', {
    session_id,
    category,
    category_response: response
  });
  
  // Refresh task view to show new tasks
  await refreshTasks();
}
```

### 4. Task Accumulation

Tasks from breakdown accumulate in the session. After each category:
- Call `GET /sessions/{session_id}` to get updated task list
- OR maintain local state and append new tasks

---

## API Integration Examples

### TypeScript Types

```typescript
interface TaskItem {
  id: string;
  text: string;
  is_completed: boolean;
  original_thought_snippet: string | null;
  estimated_duration_minutes: number | null;
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  updated_at: string;
}

interface SessionResponse {
  session_id: string;
  needs_clarification: boolean;
  clarity_score: number;
  tasks: TaskItem[];
  follow_up_question: string | null;
  suggested_breakdown_categories: string[] | null;
  metadata: Record<string, any>;
}

interface GuidedBreakdownResponse {
  session_id: string;
  category: string;
  tasks: TaskItem[];
  has_more_in_category: boolean;
}
```

### API Service Class

```typescript
class ClarityVoiceAPI {
  private baseURL = 'http://localhost:8002/api/v1';

  async processAudio(audioFile: File): Promise<SessionResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    
    const response = await fetch(`${this.baseURL}/process`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error.message);
    }
    
    return response.json();
  }

  async refineTasks(
    sessionId: string, 
    clarificationAnswer: string
  ): Promise<SessionResponse> {
    const response = await fetch(`${this.baseURL}/tasks/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        clarification_answer: clarificationAnswer
      })
    });
    
    return response.json();
  }

  async guidedBreakdown(
    sessionId: string,
    category: string,
    categoryResponse: string
  ): Promise<GuidedBreakdownResponse> {
    const response = await fetch(`${this.baseURL}/tasks/guided-breakdown`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        category: category,
        category_response: categoryResponse
      })
    });
    
    return response.json();
  }

  async getSession(sessionId: string): Promise<SessionResponse> {
    const response = await fetch(`${this.baseURL}/sessions/${sessionId}`);
    return response.json();
  }

  async updateTask(taskId: string, isCompleted: boolean): Promise<TaskItem> {
    const response = await fetch(`${this.baseURL}/tasks/${taskId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_completed: isCompleted })
    });
    
    return response.json();
  }

  async deleteTask(taskId: string): Promise<void> {
    await fetch(`${this.baseURL}/tasks/${taskId}`, {
      method: 'DELETE'
    });
  }
}
```

---

## User Experience Guidelines

### For Clear Inputs (60% of users)
- Fast, seamless experience
- Audio → Tasks in ~3 seconds
- No interruptions

### For Medium Clarity (30% of users)
- Still fast, but may have vague task descriptions
- Consider showing clarity score: "I extracted what I could (score: 5/10)"
- Let users edit task text manually

### For Very Vague Inputs (10% of users)
- Empathetic messaging: "It sounds like you're feeling overwhelmed"
- Break it down gently
- Show progress through breakdown
- Celebrate completion: "Great! I found 6 tasks to help you get started"

### Breakdown Mode UX
- **Progress indicator**: "Work (1/4)" at top
- **Skip button**: Always visible, labeled "Nothing here" or "Skip"
- **Voice preferred**: Keep consistency with initial input
- **Visual accumulation**: Show tasks appearing as they're extracted
- **Completion message**: "All done! Here are your 6 tasks."

---

## Testing Your Frontend

### Test Case 1: Clear Input
Record: "I need to buy eggs and call mom at 5pm"
- Should get 2 tasks immediately
- No clarification

### Test Case 2: Medium Clarity
Record: "I should clean something and maybe do that work thing"
- Should get tasks immediately (NEW: threshold = 5)
- Tasks may be slightly vague

### Test Case 3: Vague + Good Clarification
Record: "Everything is overwhelming"
- Get clarification question
- Answer: "I want to focus on work"
- Should get work-related tasks

### Test Case 4: Vague + Vague Clarification (Breakdown)
Record: "Too much to do everywhere"
- Get clarification question
- Answer: "I don't know, all of it"
- Should get breakdown suggestion
- Go through each category
- Should accumulate 4-6 tasks total

---

## Performance Optimization

### Loading States
- Show "Transcribing..." for first 1-2 seconds
- Show "Analyzing..." for next 1-2 seconds
- Total: 2-5 seconds typical

### Caching
- Cache session locally (don't refetch after operations)
- Update task list optimistically on toggle/delete

### Error Recovery
- Retry failed uploads automatically (once)
- Save session_id to recover from refresh
- Provide "Try Again" button on failures

---

## Deployment Notes

### Development
- Backend: `http://localhost:8002`
- Frontend: `http://localhost:3000` or `http://localhost:5173`

### Production
- Update CORS in `main.py` with production domain
- Use HTTPS for both frontend and backend
- Set proper base URL in frontend config

---

## Next Steps

1. **Set up project**: React, Next.js, or your preferred framework
2. **Audio recording**: Integrate RecordRTC or browser MediaRecorder
3. **Implement flow**: Follow the step-by-step implementation above
4. **Test locally**: Use `http://localhost:8002/docs` to explore API
5. **Iterate on UX**: Test with actual users experiencing executive dysfunction

---

## Questions?

Check:
- `API.md` for detailed endpoint specs
- `ARCHITECTURE.md` for system design
- `http://localhost:8002/docs` for interactive API testing

Start server:
```bash
cd /home/anoop130/Project-Important
source venv/bin/activate
uvicorn main:app --port 8002
```
