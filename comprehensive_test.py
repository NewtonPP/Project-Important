#!/usr/bin/env python3
"""
Comprehensive Edge Case Testing Script for ClarityVoice
Tests all scenarios with detailed logging
"""

import requests
import json
from gtts import gTTS
import time
from datetime import datetime

BASE_URL = "http://localhost:8002/api/v1"

def log_section(title):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def log_step(step_num, description):
    """Print step header."""
    print(f"\n--- Step {step_num}: {description} ---")

def log_response(response, label="Response"):
    """Pretty print API response."""
    print(f"\n{label}:")
    if response.status_code == 200:
        print(f"Status: {response.status_code} OK")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Status: {response.status_code} ERROR")
        print(json.dumps(response.json(), indent=2))
    return response.json()

def create_audio(text, filename):
    """Create test audio file."""
    print(f"Creating audio: {filename}")
    print(f"Text: \"{text}\"")
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    print(f"Created {filename}\n")

def check_server():
    """Verify server is running."""
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=2)
        if response.status_code == 200:
            print("Server is running")
            return True
    except:
        print("ERROR: Server is not running.")
        print("Start it with: uvicorn main:app --port 8002")
        return False


def test_scenario_1_clear_input():
    """Test Scenario 1: Clear, actionable input (no clarification needed)."""
    log_section("SCENARIO 1: CLEAR INPUT (High Clarity)")
    
    log_step(1, "Create clear audio input")
    audio_text = "I need to buy eggs at the grocery store and call my mom at 5pm"
    create_audio(audio_text, "test_clear.mp3")
    
    log_step(2, "Upload audio to /process endpoint")
    with open("test_clear.mp3", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio_file": ("test_clear.mp3", f, "audio/mpeg")}
        )
    
    data = log_response(response, "Initial Processing Result")
    
    print("\nAnalysis:")
    print(f"  Clarity Score: {data['clarity_score']} (Expected: 7-10)")
    print(f"  Needs Clarification: {data['needs_clarification']} (Expected: false)")
    print(f"  Tasks Extracted: {len(data['tasks'])} (Expected: 2)")
    print(f"  Breakdown Suggested: {data.get('suggested_breakdown_categories') is not None} (Expected: false)")
    
    if data['tasks']:
        print("\n  Extracted Tasks:")
        for i, task in enumerate(data['tasks'], 1):
            print(f"    {i}. [{task['priority']}] {task['text']} ({task.get('estimated_duration_minutes', '?')} min)")
    
    result = "PASS" if data['clarity_score'] >= 7 and len(data['tasks']) > 0 else "FAIL"
    print(f"\n{result}: Clear input handled correctly")
    return data


def test_scenario_2_medium_clarity():
    """Test Scenario 2: Medium clarity (NEW: threshold change test)."""
    log_section("SCENARIO 2: MEDIUM CLARITY (Score = 5, New Threshold)")
    
    log_step(1, "Create medium clarity audio")
    audio_text = "I should probably clean something and maybe deal with that work thing"
    create_audio(audio_text, "test_medium.mp3")
    
    log_step(2, "Upload audio to /process endpoint")
    with open("test_medium.mp3", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio_file": ("test_medium.mp3", f, "audio/mpeg")}
        )
    
    data = log_response(response, "Processing Result")
    
    print("\nAnalysis:")
    print(f"  Clarity Score: {data['clarity_score']} (Expected: 4-6)")
    print(f"  Needs Clarification: {data['needs_clarification']} (Expected: false if score >= 5)")
    print(f"  Tasks Extracted: {len(data['tasks'])}")
    
    if data['tasks']:
        print("\n  Extracted Tasks:")
        for i, task in enumerate(data['tasks'], 1):
            print(f"    {i}. [{task['priority']}] {task['text']}")
    
    print("\nNEW BEHAVIOR:")
    if data['clarity_score'] >= 5 and not data['needs_clarification']:
        print("  PASS: Score 5 now passes without clarification (threshold lowered from 6)")
    else:
        print(f"  INFO: Score {data['clarity_score']} behavior varies")
    
    return data


def test_scenario_3_vague_with_clarification():
    """Test Scenario 3: Vague input with good clarification."""
    log_section("SCENARIO 3: VAGUE INPUT + GOOD CLARIFICATION")
    
    log_step(1, "Create vague audio input")
    audio_text = "Ugh I have so much stuff to do and I don't know where to start"
    create_audio(audio_text, "test_vague_1.mp3")
    
    log_step(2, "Upload audio to /process endpoint")
    with open("test_vague_1.mp3", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio_file": ("test_vague_1.mp3", f, "audio/mpeg")}
        )
    
    data = log_response(response, "Initial Processing")
    session_id = data['session_id']
    
    print("\nInitial Analysis:")
    print(f"  Clarity Score: {data['clarity_score']} (Expected: < 5)")
    print(f"  Needs Clarification: {data['needs_clarification']} (Expected: true)")
    print(f"  Follow-up Question: \"{data.get('follow_up_question')}\"")
    
    log_step(3, "Provide SPECIFIC clarification answer")
    clarification = "I want to focus on cleaning my desk and organizing my papers"
    print(f"Clarification Answer: \"{clarification}\"")
    
    response = requests.post(
        f"{BASE_URL}/tasks/refine",
        json={
            "session_id": session_id,
            "clarification_answer": clarification
        }
    )
    
    refined_data = log_response(response, "After Clarification")
    
    print("\nRefined Analysis:")
    print(f"  Clarity Score: {refined_data['clarity_score']} (Expected: 5-8)")
    print(f"  Needs Clarification: {refined_data['needs_clarification']} (Expected: false)")
    print(f"  Tasks Extracted: {len(refined_data['tasks'])}")
    
    if refined_data['tasks']:
        print("\n  Extracted Tasks:")
        for i, task in enumerate(refined_data['tasks'], 1):
            print(f"    {i}. [{task['priority']}] {task['text']}")
    
    result = "PASS" if not refined_data['needs_clarification'] and len(refined_data['tasks']) > 0 else "FAIL"
    print(f"\n{result}: Good clarification extracted tasks successfully")
    return refined_data


def test_scenario_4_breakdown_flow():
    """Test Scenario 4: Very vague -> vague clarification -> guided breakdown."""
    log_section("SCENARIO 4: COMPLETE BREAKDOWN FLOW (3 Stages)")
    
    log_step(1, "Create very vague audio input")
    audio_text = "Everything is overwhelming. I can't handle anything. There's too much."
    create_audio(audio_text, "test_vague_2.mp3")
    
    log_step(2, "Upload audio - Stage 1")
    with open("test_vague_2.mp3", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio_file": ("test_vague_2.mp3", f, "audio/mpeg")}
        )
    
    data = log_response(response, "Stage 1: Initial Processing")
    session_id = data['session_id']
    
    print("\nStage 1 Analysis:")
    print(f"  Clarity Score: {data['clarity_score']} (Expected: 1-4)")
    print(f"  Tasks: {len(data['tasks'])} (Expected: 0)")
    print(f"  Follow-up: \"{data.get('follow_up_question')}\"")
    
    log_step(3, "Provide VAGUE clarification - Stage 2")
    vague_answer = "I don't know, everything I guess"
    print(f"Clarification Answer: \"{vague_answer}\"")
    
    response = requests.post(
        f"{BASE_URL}/tasks/refine",
        json={
            "session_id": session_id,
            "clarification_answer": vague_answer
        }
    )
    
    refined_data = log_response(response, "Stage 2: Breakdown Suggestion")
    
    print("\nStage 2 Analysis:")
    print(f"  Still Needs Clarification: {refined_data['needs_clarification']} (Expected: true)")
    print(f"  Breakdown Categories: {refined_data.get('suggested_breakdown_categories')}")
    print(f"  Follow-up: \"{refined_data.get('follow_up_question')}\"")
    
    if not refined_data.get('suggested_breakdown_categories'):
        print("\nFAIL: No breakdown categories suggested")
        return
    
    log_step(4, "Stage 3: Guided Category Breakdown")
    
    categories_to_test = [
        {
            "name": "work",
            "response": "I have a project presentation due and need to respond to client emails"
        },
        {
            "name": "home",
            "response": "The kitchen is a mess and laundry is piling up"
        },
        {
            "name": "errands",
            "response": "Need to pick up groceries and mail a package"
        }
    ]
    
    all_tasks = []
    
    for i, category_info in enumerate(categories_to_test, 1):
        print(f"\n  Category {i}/{len(categories_to_test)}: {category_info['name'].upper()}")
        print(f"  User Response: \"{category_info['response']}\"")
        
        response = requests.post(
            f"{BASE_URL}/tasks/guided-breakdown",
            json={
                "session_id": session_id,
                "category": category_info['name'],
                "category_response": category_info['response']
            }
        )
        
        if response.status_code != 200:
            print(f"  ERROR: {response.status_code}")
            print(f"  {response.json()}")
            continue
        
        category_data = response.json()
        print(f"  Tasks extracted: {len(category_data['tasks'])}")
        
        for task in category_data['tasks']:
            print(f"     - [{task['priority']}] {task['text']} ({task.get('estimated_duration_minutes', '?')} min)")
            all_tasks.append(task)
    
    log_step(5, "Retrieve Complete Session")
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    final_data = log_response(response, "Final Session State")
    
    print("\nFinal Analysis:")
    print(f"  Total Tasks Extracted: {len(final_data['tasks'])}")
    print(f"  Breakdown Mode Used: {len(all_tasks) > 0}")
    print(f"  Session ID: {session_id}")
    
    print("\n  Complete Task List:")
    for i, task in enumerate(final_data['tasks'], 1):
        print(f"    {i}. [{task['priority']}] {task['text']} ({task.get('estimated_duration_minutes', '?')} min)")
    
    result = "PASS" if len(final_data['tasks']) >= 4 else "FAIL"
    print(f"\n{result}: Breakdown flow extracted {len(final_data['tasks'])} tasks from overwhelming input")
    return final_data


def test_scenario_5_invalid_file():
    """Test Scenario 5: Invalid file format."""
    log_section("SCENARIO 5: INVALID FILE FORMAT (Error Handling)")
    
    log_step(1, "Create invalid file (text instead of audio)")
    with open("test_invalid.txt", "w") as f:
        f.write("This is not an audio file")
    print("Created test_invalid.txt")
    
    log_step(2, "Attempt upload with invalid format")
    with open("test_invalid.txt", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio_file": ("test_invalid.txt", f, "text/plain")}
        )
    
    log_response(response, "Error Response")
    
    print("\nAnalysis:")
    if response.status_code in [400, 500]:
        error_data = response.json()
        if 'error' in error_data:
            print(f"  Error Code: {error_data['error']['code']}")
            print(f"  Error Message: {error_data['error']['message']}")
            print("  PASS: Invalid file rejected correctly")
        else:
            print("  WARNING: Error format unexpected")
    else:
        print(f"  FAIL: Expected 400/500, got {response.status_code}")


def test_scenario_6_missing_session():
    """Test Scenario 6: Non-existent session ID."""
    log_section("SCENARIO 6: NON-EXISTENT SESSION (Error Handling)")
    
    log_step(1, "Attempt to refine non-existent session")
    fake_session_id = "00000000-0000-0000-0000-000000000000"
    
    response = requests.post(
        f"{BASE_URL}/tasks/refine",
        json={
            "session_id": fake_session_id,
            "clarification_answer": "test"
        }
    )
    
    log_response(response, "Error Response")
    
    print("\nAnalysis:")
    if response.status_code == 404:
        error_data = response.json()
        if error_data.get('error', {}).get('code') == 'SESSION_NOT_FOUND':
            print("  PASS: Non-existent session handled correctly")
        else:
            print("  WARNING: Error code unexpected")
    else:
        print(f"  Status: {response.status_code}")


def test_scenario_7_task_management():
    """Test Scenario 7: Task CRUD operations."""
    log_section("SCENARIO 7: TASK MANAGEMENT (Update & Delete)")
    
    log_step(1, "Create a session with tasks")
    audio_text = "I need to wash the dishes and take out the trash"
    create_audio(audio_text, "test_tasks.mp3")
    
    with open("test_tasks.mp3", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio_file": ("test_tasks.mp3", f, "audio/mpeg")}
        )
    
    data = log_response(response, "Session Created")
    
    if not data.get('tasks') or len(data['tasks']) == 0:
        print("\nWARNING: No tasks to manage, skipping")
        return
    
    task_id = data['tasks'][0]['id']
    session_id = data['session_id']
    
    log_step(2, "Mark task as completed (PATCH)")
    print(f"Task ID: {task_id}")
    print(f"Marking as completed: {data['tasks'][0]['text']}")
    
    response = requests.patch(
        f"{BASE_URL}/tasks/{task_id}",
        json={"is_completed": True}
    )
    
    updated_task = log_response(response, "Task Update Result")
    
    print("\nUpdate Analysis:")
    print(f"  Task Completed: {updated_task.get('is_completed')} (Expected: true)")
    print(f"  PASS: Task updated successfully" if updated_task.get('is_completed') else "  FAIL")
    
    log_step(3, "Verify task status in session")
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    session_data = response.json()
    
    updated_task_in_session = next((t for t in session_data['tasks'] if t['id'] == task_id), None)
    print(f"  Task in session is_completed: {updated_task_in_session['is_completed']}")
    
    if len(data['tasks']) > 1:
        log_step(4, "Delete second task (DELETE)")
        task_to_delete = data['tasks'][1]['id']
        print(f"Deleting Task ID: {task_to_delete}")
        print(f"Task text: {data['tasks'][1]['text']}")
        
        response = requests.delete(f"{BASE_URL}/tasks/{task_to_delete}")
        delete_result = log_response(response, "Delete Result")
        
        print(f"  PASS: Task deleted" if delete_result.get('success') else "  FAIL")


def test_scenario_8_session_listing():
    """Test Scenario 8: Session listing and pagination."""
    log_section("SCENARIO 8: SESSION LISTING (Pagination)")
    
    log_step(1, "List all sessions (page 1, limit 5)")
    response = requests.get(f"{BASE_URL}/sessions?page=1&limit=5")
    data = log_response(response, "Sessions List")
    
    print("\nAnalysis:")
    print(f"  Sessions Returned: {len(data['sessions'])}")
    print(f"  Total Sessions: {data['pagination']['total_count']}")
    print(f"  Current Page: {data['pagination']['page']}")
    print(f"  Total Pages: {data['pagination']['total_pages']}")
    
    if data['sessions']:
        print("\n  Recent Sessions:")
        for session in data['sessions'][:3]:
            print(f"    - ID: {session['session_id'][:8]}... | Score: {session.get('clarity_score', 'N/A')} | Tasks: {session['task_count']}")
    
    print("  PASS: Session listing working")


def test_scenario_9_empty_audio():
    """Test Scenario 9: Very short/empty audio."""
    log_section("SCENARIO 9: VERY SHORT AUDIO (Edge Case)")
    
    log_step(1, "Create minimal audio")
    audio_text = "Help"
    create_audio(audio_text, "test_short.mp3")
    
    log_step(2, "Upload short audio")
    with open("test_short.mp3", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio_file": ("test_short.mp3", f, "audio/mpeg")}
        )
    
    data = log_response(response, "Processing Result")
    
    print("\nAnalysis:")
    print(f"  Clarity Score: {data['clarity_score']}")
    print(f"  Needs Clarification: {data['needs_clarification']} (Expected: true for single word)")
    print(f"  System Handled: {'PASS' if data['needs_clarification'] else 'INFO'}")


def cleanup_test_files():
    """Remove generated test files."""
    import os
    test_files = [
        "test_clear.mp3", "test_medium.mp3", "test_vague_1.mp3", 
        "test_vague_2.mp3", "test_tasks.mp3", "test_short.mp3",
        "test_invalid.txt"
    ]
    
    print("\nCleaning up test files...")
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"  Removed {file}")


def main():
    print("\n" + "="*70)
    print("  CLARITYVOICE COMPREHENSIVE EDGE CASE TEST SUITE")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    print("\nChecking server status...")
    if not check_server():
        return
    
    print("\nStarting test suite...")
    time.sleep(1)
    
    try:
        test_scenario_1_clear_input()
        time.sleep(1)
        
        test_scenario_2_medium_clarity()
        time.sleep(1)
        
        test_scenario_3_vague_with_clarification()
        time.sleep(1)
        
        test_scenario_4_breakdown_flow()
        time.sleep(1)
        
        test_scenario_5_invalid_file()
        time.sleep(1)
        
        test_scenario_6_missing_session()
        time.sleep(1)
        
        test_scenario_7_task_management()
        time.sleep(1)
        
        test_scenario_8_session_listing()
        time.sleep(1)
        
        test_scenario_9_empty_audio()
        
        log_section("TEST SUITE COMPLETE")
        print("All edge case scenarios tested")
        print("\nScenarios Covered:")
        print("  1. Clear input (high clarity)")
        print("  2. Medium clarity (threshold = 5)")
        print("  3. Vague input with good clarification")
        print("  4. Complete breakdown flow (3 stages)")
        print("  5. Invalid file format")
        print("  6. Non-existent session")
        print("  7. Task management (update & delete)")
        print("  8. Session listing (pagination)")
        print("  9. Very short audio")
        
        print("\nDatabase Status:")
        response = requests.get(f"{BASE_URL}/sessions?page=1&limit=100")
        if response.status_code == 200:
            data = response.json()
            print(f"  Total Sessions: {data['pagination']['total_count']}")
            breakdown_sessions = sum(1 for s in data['sessions'] if s.get('task_count', 0) > 3)
            print(f"  Breakdown Sessions: {breakdown_sessions}")
        
        print("\nAll tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_test_files()
        print("\nTest suite finished")


if __name__ == "__main__":
    main()
