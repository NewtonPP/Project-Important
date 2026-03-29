# Test Audio Files

## Creating Test Audio Files

For testing the ClarityVoice backend, you'll need audio files. Here are two test cases:

### Test Case A: Clear Input
**File**: `test_clear.mp3`

**Script to record**:
"I need to go to the grocery store for eggs and milk, then call my mom at 5pm."

**Expected Result**:
- Clarity score: 7-9
- Tasks extracted: 2
- Needs clarification: false

---

### Test Case B: Cluttered Input
**File**: `test_cluttered.mp3`

**Script to record**:
"Ugh, I'm so overwhelmed. The house is a mess, and I keep thinking about that project at work, but I don't know where to start. Maybe I should just clean something?"

**Expected Result**:
- Clarity score: 3-5
- Tasks extracted: 0
- Needs clarification: true
- Follow-up question: Present

---

## How to Create Audio Files

### Option 1: Use your phone
1. Open voice recorder app
2. Record the script
3. Export as MP3 or M4A
4. Transfer to this directory

### Option 2: Use online TTS
1. Visit https://ttsmaker.com/ or similar
2. Paste the script
3. Generate and download MP3

### Option 3: Use macOS/Linux
```bash
# macOS (requires `say` command)
say "I need to go to the grocery store" -o test_clear.aiff
ffmpeg -i test_clear.aiff test_clear.mp3

# Linux (requires `espeak` and `ffmpeg`)
espeak "I need to go to the grocery store" --stdout | ffmpeg -i - test_clear.mp3
```

---

## Testing with curl

```bash
# Test with your audio file
curl -X POST http://localhost:8000/api/v1/process \
  -F "audio_file=@tests/test_audio/test_clear.mp3" \
  | jq .

# Or test extraction only (no audio)
curl -X POST http://localhost:8000/api/v1/tasks/extract \
  -H "Content-Type: application/json" \
  -d '{"transcript": "I need to buy eggs and call mom"}' \
  | jq .
```

---

## Note

Place your test audio files in the `tests/test_audio/` directory.
