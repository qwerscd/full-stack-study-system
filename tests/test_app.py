"""
tests/test_app.py
-----------------
Basic tests for the Full-Stack Study System.
Run with:  pytest tests/test_app.py -v
"""

import pytest
from werkzeug.security import generate_password_hash

# ── Import the Flask app and database helpers ──────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as flask_app
from database import get_connection


# ==============================================================================
# Fixtures  (run once per test, always use a fresh in-memory DB)
# ==============================================================================

@pytest.fixture
def app(tmp_path, monkeypatch):
    """
    Configure the Flask app to use a temporary SQLite file so tests never
    touch the real study_system.db.
    """
    test_db = tmp_path / "test.db"

    # Point database.py's DB_PATH at the temp file
    import database
    monkeypatch.setattr(database, "DB_PATH", test_db)

    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    # Build tables and add demo data
    database.init_db()
    database.seed_demo_data()

    yield flask_app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


# ==============================================================================
# Helper: log in as a specific user
# ==============================================================================

def login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    return client.get("/logout", follow_redirects=True)


# ==============================================================================
# 1. Authentication tests
# ==============================================================================

class TestLogin:

    def test_login_page_loads(self, client):
        """GET /login should return 200."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_login_with_correct_credentials(self, client):
        """student1 / student123 should log in successfully."""
        response = login(client, "student1", "student123")
        assert response.status_code == 200
        # After login the dashboard redirects to student courses page
        assert b"course" in response.data.lower()

    def test_login_with_wrong_password(self, client):
        """Wrong password should show an error message."""
        response = login(client, "student1", "wrongpassword")
        assert b"invalid" in response.data.lower()

    def test_login_with_nonexistent_user(self, client):
        """Unknown username should show an error message."""
        response = login(client, "nobody", "anything")
        assert b"invalid" in response.data.lower()

    def test_logout(self, client):
        """After logout the user is redirected to login."""
        login(client, "student1", "student123")
        response = logout(client)
        assert response.status_code == 200
        assert b"login" in response.data.lower()


# ==============================================================================
# 2. Registration tests
# ==============================================================================

class TestRegister:

    def test_register_new_student(self, client):
        """A brand-new username should register successfully."""
        response = client.post(
            "/register",
            data={
                "username": "newstudent",
                "email": "newstudent@test.com",
                "password": "pass1234",
                "role": "student",
            },
            follow_redirects=True,
        )
        assert b"login" in response.data.lower()

    def test_register_duplicate_username(self, client):
        """Registering with an existing username should fail."""
        response = client.post(
            "/register",
            data={
                "username": "student1",       # already exists in seed data
                "email": "other@test.com",
                "password": "pass1234",
                "role": "student",
            },
            follow_redirects=True,
        )
        assert b"already exists" in response.data.lower()

    def test_register_short_password(self, client):
        """Password shorter than 6 characters should be rejected."""
        response = client.post(
            "/register",
            data={
                "username": "shortpwduser",
                "email": "short@test.com",
                "password": "abc",
                "role": "student",
            },
            follow_redirects=True,
        )
        assert b"password" in response.data.lower()


# ==============================================================================
# 3. Student – course browsing and enrolment
# ==============================================================================

class TestStudentEnrollment:

    def test_student_can_see_courses(self, client):
        """Logged-in student should see the course list."""
        login(client, "student1", "student123")
        response = client.get("/student/courses")
        assert response.status_code == 200
        assert b"cs101" in response.data.lower()

    def test_student_can_enroll(self, client):
        """Student should be able to enroll in a course with free seats."""
        login(client, "student1", "student123")
        # CS201 has 30 seats — plenty of room
        response = client.post("/student/enroll/2", follow_redirects=True)
        assert response.status_code == 200
        assert b"enrolled" in response.data.lower()

    def test_duplicate_enrollment_rejected(self, client):
        """Enrolling in the same course twice should show a warning."""
        login(client, "student1", "student123")
        client.post("/student/enroll/2", follow_redirects=True)   # first enroll
        response = client.post("/student/enroll/2", follow_redirects=True)  # duplicate
        assert b"already enrolled" in response.data.lower()

    def test_full_course_rejected(self, client):
        """
        CS101 has max_capacity=2.
        After student1 and student2 enroll, student3 should be blocked.
        """
        login(client, "student1", "student123")
        client.post("/student/enroll/1", follow_redirects=True)
        logout(client)

        login(client, "student2", "student123")
        client.post("/student/enroll/1", follow_redirects=True)
        logout(client)

        login(client, "student3", "student123")
        response = client.post("/student/enroll/1", follow_redirects=True)
        assert b"full" in response.data.lower()

    def test_student_can_drop_course(self, client):
        """Student should be able to drop a course they enrolled in."""
        login(client, "student1", "student123")
        client.post("/student/enroll/2", follow_redirects=True)
        response = client.post(
            "/student/drop/2", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"dropped" in response.data.lower()


# ==============================================================================
# 4. Role-based access control
# ==============================================================================

class TestAccessControl:

    def test_unauthenticated_redirect(self, client):
        """Accessing a protected page without login redirects to /login."""
        response = client.get("/student/courses", follow_redirects=True)
        assert b"login" in response.data.lower()

    def test_student_cannot_access_teacher_page(self, client):
        """A student trying to reach /teacher/courses should be blocked."""
        login(client, "student1", "student123")
        response = client.get("/teacher/courses", follow_redirects=True)
        assert response.status_code == 200
        # Should show a permission error, not the teacher page
        assert b"permission" in response.data.lower() or b"login" in response.data.lower()

    def test_teacher_cannot_access_student_page(self, client):
        """A teacher trying to reach /student/courses should be blocked."""
        login(client, "teacher1", "teacher123")
        response = client.get("/student/courses", follow_redirects=True)
        assert response.status_code == 200
        assert b"permission" in response.data.lower() or b"login" in response.data.lower()


# ==============================================================================
# 5. Teacher – course management
# ==============================================================================

class TestTeacherCourses:

    def test_teacher_sees_own_courses(self, client):
        """Teacher1 should see courses they own (CS101, CS201)."""
        login(client, "teacher1", "teacher123")
        response = client.get("/teacher/courses")
        assert response.status_code == 200
        assert b"cs101" in response.data.lower()

    def test_teacher_can_create_course(self, client):
        """Teacher should be able to create a new course."""
        login(client, "teacher1", "teacher123")
        response = client.post(
            "/teacher/courses/new",
            data={
                "code": "TEST999",
                "title": "Test Course",
                "description": "A course for testing.",
                "max_capacity": "10",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"test999" in response.data.lower()

    def test_teacher_can_delete_own_course(self, client):
        """Teacher should be able to delete a course they created."""
        login(client, "teacher1", "teacher123")
        # First create a course to delete
        client.post(
            "/teacher/courses/new",
            data={
                "code": "DEL001",
                "title": "To Be Deleted",
                "description": "",
                "max_capacity": "5",
            },
            follow_redirects=True,
        )
        # Find the new course id from the DB
        import database
        conn = database.get_connection()
        row = conn.execute("SELECT id FROM courses WHERE code = 'DEL001'").fetchone()
        conn.close()

        response = client.post(
            f"/teacher/courses/{row['id']}/delete", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"deleted" in response.data.lower()
