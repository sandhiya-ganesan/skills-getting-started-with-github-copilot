"""
Tests for the Mergington High School Activities API
"""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_has_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_includes_participants(self, client):
        """Test that activities include their current participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        assert "john@mergington.edu" in data["Gym Class"]["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
    
    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up with the same email twice fails"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(f"/activities/Programming%20Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        client.post(f"/activities/Chess%20Club/unregister?email={email}")
        
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
    
    def test_unregister_not_signed_up_fails(self, client):
        """Test that unregistering a student who isn't signed up fails"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=nosuchstudent@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client):
        """Test that a student can unregister and then sign up again"""
        email = "michael@mergington.edu"
        
        # Unregister
        client.post(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Sign up again
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Chess Club"]["participants"]


class TestSignupAndUnregisterIntegration:
    """Integration tests for signup and unregister"""
    
    def test_signup_increases_participants_decreases_available_spots(self, client):
        """Test that signup increases participants count"""
        email = "integration@mergington.edu"
        
        # Get initial state
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Get updated state
        response2 = client.get("/activities")
        final_count = len(response2.json()["Chess Club"]["participants"])
        
        assert final_count == initial_count + 1
    
    def test_unregister_decreases_participants_increases_available_spots(self, client):
        """Test that unregister decreases participants count"""
        email = "michael@mergington.edu"
        
        # Get initial state
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        # Unregister
        client.post(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Get updated state
        response2 = client.get("/activities")
        final_count = len(response2.json()["Chess Club"]["participants"])
        
        assert final_count == initial_count - 1
