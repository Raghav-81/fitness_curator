"""
Quick test script for workout creator functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_client():
    """Test creating a client"""
    client_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "age": 30,
        "goals": "Build muscle and increase strength",
        "trainer_notes": "Beginner level, no previous injuries"
    }
    
    response = requests.post(f"{BASE_URL}/api/clients", json=client_data)
    print(f"Create Client Response: {response.status_code}")
    if response.ok:
        print(json.dumps(response.json(), indent=2))
        return response.json()['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_get_clients():
    """Test getting all clients"""
    response = requests.get(f"{BASE_URL}/api/clients")
    print(f"\nGet Clients Response: {response.status_code}")
    if response.ok:
        clients = response.json()
        print(f"Found {len(clients)} clients")
        for client in clients:
            print(f"  - {client['name']} ({client['email']})")
        return clients
    else:
        print(f"Error: {response.text}")
        return []

def test_create_workout_plan(client_id, video_ids):
    """Test creating a workout plan"""
    plan_data = {
        "client_id": client_id,
        "plan_name": "4-Week Strength Building Program",
        "description": "Progressive strength training program focusing on compound movements",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-28T00:00:00",
        "is_template": False,
        "day_type": "day_number",
        "exercises": [
            {
                "video_id": video_ids[0] if len(video_ids) > 0 else 1,
                "day": "1",
                "sets": 3,
                "reps": "10",
                "notes": "Focus on form",
                "order_index": 0
            },
            {
                "video_id": video_ids[1] if len(video_ids) > 1 else 2,
                "day": "1",
                "sets": 3,
                "reps": "12",
                "notes": "Control the movement",
                "order_index": 1
            },
            {
                "video_id": video_ids[2] if len(video_ids) > 2 else 3,
                "day": "2",
                "sets": 4,
                "reps": "8",
                "notes": "Heavy weight",
                "order_index": 0
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/workout-plans", json=plan_data)
    print(f"\nCreate Workout Plan Response: {response.status_code}")
    if response.ok:
        plan = response.json()
        print(f"Plan created: {plan['plan_name']}")
        print(f"Share token: {plan['share_token']}")
        print(f"Share URL: {BASE_URL}/workout-plan/{plan['share_token']}")
        print(f"Number of exercises: {len(plan['exercises'])}")
        return plan
    else:
        print(f"Error: {response.text}")
        return None

def test_get_videos():
    """Get some video IDs for testing"""
    response = requests.get(f"{BASE_URL}/api/videos")
    if response.ok:
        videos = response.json()
        return [v['id'] for v in videos[:5]]  # Get first 5 video IDs
    return []

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Workout Creator API")
    print("=" * 60)
    
    # Test 1: Create a client
    print("\n1. Creating a test client...")
    client_id = test_create_client()
    
    if not client_id:
        print("\nFailed to create client. Trying to get existing clients...")
        clients = test_get_clients()
        if clients:
            client_id = clients[0]['id']
            print(f"Using existing client ID: {client_id}")
    
    # Test 2: Get all clients
    print("\n2. Getting all clients...")
    test_get_clients()
    
    # Test 3: Get video IDs
    print("\n3. Getting video IDs...")
    video_ids = test_get_videos()
    print(f"Found {len(video_ids)} videos")
    
    # Test 4: Create a workout plan
    if client_id and video_ids:
        print("\n4. Creating a workout plan...")
        plan = test_create_workout_plan(client_id, video_ids)
        
        if plan:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print(f"\nYou can now:")
            print(f"1. Visit http://localhost:8000 and click 'Workout Creator' tab")
            print(f"2. Share this link with client: {BASE_URL}/workout-plan/{plan['share_token']}")
        else:
            print("\n❌ Failed to create workout plan")
    else:
        print("\n❌ Missing client_id or video_ids")
    
    print("\n" + "=" * 60)
