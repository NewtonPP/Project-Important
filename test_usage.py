"""
ClarityVoice Backend - Example Usage Script

This script demonstrates how to interact with the ClarityVoice API
using Python's requests library.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    return response.status_code == 200


def test_process_audio(audio_file_path):
    """Test main process endpoint with audio file."""
    print(f"\nUploading audio file: {audio_file_path}")
    
    with open(audio_file_path, "rb") as f:
        files = {"audio_file": f}
        response = requests.post(f"{BASE_URL}/api/v1/process", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSuccess!")
        print(f"Session ID: {data['session_id']}")
        print(f"Clarity Score: {data['clarity_score']}/10")
        print(f"Needs Clarification: {data['needs_clarification']}")
        
        if data['needs_clarification']:
            print(f"\nFollow-up Question: {data['follow_up_question']}")
        else:
            print(f"\nTasks Extracted: {len(data['tasks'])}")
            for i, task in enumerate(data['tasks'], 1):
                print(f"  {i}. {task['text']} (Priority: {task['priority']})")
        
        return data
    else:
        print(f"\nError: {response.status_code}")
        print(response.json())
        return None


def test_extract_from_text(transcript):
    """Test task extraction from text (no audio)."""
    print(f"\nExtracting tasks from text...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/tasks/extract",
        json={"transcript": transcript}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Clarity Score: {data['clarity_score']}/10")
        print(f"Tasks: {len(data['tasks'])}")
        return data
    else:
        print(f"Error: {response.status_code}")
        return None


def test_list_sessions():
    """Test listing sessions."""
    print(f"\nFetching sessions...")
    
    response = requests.get(f"{BASE_URL}/api/v1/sessions?page=1&limit=5")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['pagination']['total_count']} sessions")
        for session in data['sessions']:
            print(f"  - {session['session_id']}: {session['task_count']} tasks ({session['completed_task_count']} completed)")
        return data
    else:
        print(f"Error: {response.status_code}")
        return None


def test_update_task(task_id, is_completed):
    """Test updating task status."""
    print(f"\nUpdating task {task_id}...")
    
    response = requests.patch(
        f"{BASE_URL}/api/v1/tasks/{task_id}",
        json={"is_completed": is_completed}
    )
    
    if response.status_code == 200:
        data = response.json()
        status = "Completed" if data['is_completed'] else "Pending"
        print(f"{status}: {data['text']}")
        return data
    else:
        print(f"Error: {response.status_code}")
        return None


if __name__ == "__main__":
    print("ClarityVoice API Test Suite")
    print("=" * 50)
    
    if not test_health():
        print("\nBackend is not running!")
        print("Start it with: ./start.sh")
        exit(1)
    
    print("\n" + "=" * 50)
    print("Test 1: Extract from text (no audio)")
    print("=" * 50)
    
    result = test_extract_from_text(
        "I need to buy groceries and finish the report by tomorrow"
    )
    
    if result and result['tasks']:
        session_id = result['session_id']
        task_id = result['tasks'][0]['id']
        
        print("\n" + "=" * 50)
        print("Test 2: Mark task as complete")
        print("=" * 50)
        test_update_task(task_id, True)
    
    print("\n" + "=" * 50)
    print("Test 3: List all sessions")
    print("=" * 50)
    test_list_sessions()
    
    print("\n" + "=" * 50)
    print("All tests complete!")
    print("\nTo test with audio:")
    print("  python test_usage.py /path/to/audio.mp3")
    print("\nOr use the API docs: http://localhost:8000/docs")
