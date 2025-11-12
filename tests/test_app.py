"""
Test suite for the Mergington High School API

Tests cover:
- Activity retrieval
- Student signup
- Student unregistration
- Error handling
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
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
    
    # Reset to original state before each test
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Clean up after test
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for retrieving activities"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_participant_count(self, client):
        """Test that activities have the correct initial participant count"""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Gym Class"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for student signup functionality"""
    
    def test_signup_success(self, client):
        """Test successful student signup"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=new-student@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "new-student@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "new-student@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_students(self, client):
        """Test signing up multiple students to same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/Programming%20Class/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all students were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Programming Class"]["participants"]
        
        for email in emails:
            assert email in participants
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test%2Buser@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for student unregistration functionality"""
    
    def test_unregister_success(self, client):
        """Test successful student unregistration"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_unregister_non_registered_student(self, client):
        """Test unregistering a student who is not registered"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_all_participants(self, client):
        """Test unregistering all participants from an activity"""
        # Get initial participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Chess Club"]["participants"].copy()
        
        # Unregister each participant
        for email in participants:
            response = client.delete(
                f"/activities/Chess%20Club/unregister?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all participants were removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data["Chess Club"]["participants"]) == 0


class TestSignupAndUnregisterWorkflow:
    """Integration tests for signup and unregister workflow"""
    
    def test_signup_then_unregister(self, client):
        """Test signing up a student and then unregistering them"""
        email = "workflow-test@mergington.edu"
        activity = "Gym Class"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]
    
    def test_cannot_unregister_twice(self, client):
        """Test that unregistering the same student twice fails"""
        email = "double-unregister@mergington.edu"
        activity = "Chess Club"
        
        # Sign up first
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # First unregister - should succeed
        response1 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Second unregister - should fail
        response2 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response2.status_code == 404
        assert "not registered" in response2.json()["detail"].lower()


class TestActivityCapacity:
    """Tests related to activity capacity and availability"""
    
    def test_activities_show_correct_spots_remaining(self, client):
        """Test that available spots are calculated correctly"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        spots_remaining = chess_club["max_participants"] - len(chess_club["participants"])
        assert spots_remaining == 10  # 12 max - 2 current
        
        programming = data["Programming Class"]
        spots_remaining = programming["max_participants"] - len(programming["participants"])
        assert spots_remaining == 18  # 20 max - 2 current
    
    def test_signup_increases_participant_count(self, client):
        """Test that signup increases the participant count"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up new student
        client.post("/activities/Chess%20Club/signup?email=newstudent@mergington.edu")
        
        # Get updated count
        response = client.get("/activities")
        updated_count = len(response.json()["Chess Club"]["participants"])
        
        assert updated_count == initial_count + 1
    
    def test_unregister_decreases_participant_count(self, client):
        """Test that unregister decreases the participant count"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Unregister existing student
        client.delete("/activities/Chess%20Club/unregister?email=michael@mergington.edu")
        
        # Get updated count
        response = client.get("/activities")
        updated_count = len(response.json()["Chess Club"]["participants"])
        
        assert updated_count == initial_count - 1
