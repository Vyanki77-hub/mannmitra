import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///./data/test_mannmitra.db"
os.environ["COOKIE_SECURE"] = "false"
os.environ["LLM_PROVIDER"] = "ollama"

from db.database import Base, get_db
from db.models import User, AuthSession
import auth
from main import app

# Create test engine and session
test_engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    # Clean recreate tables
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    # Clear rate limiter state
    auth._failed_login_attempts.clear()
    yield
    Base.metadata.drop_all(bind=test_engine)


# --------------------------------------------------
# Registration Tests
# --------------------------------------------------

def test_register_success():
    res = client.post(
        "/auth/register",
        json={"name": "Aarav Sharma", "email": "aarav@example.com", "password": "Password123"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Aarav Sharma"
    assert data["email"] == "aarav@example.com"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email():
    payload = {"name": "Aarav Sharma", "email": "AARAV@example.com", "password": "Password123"}
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt with lowercase version of same email
    payload2 = {"name": "Aarav S", "email": "aarav@example.com", "password": "Password456"}
    res2 = client.post("/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_register_weak_password():
    # Too short (< 8)
    res = client.post(
        "/auth/register",
        json={"name": "Student", "email": "s1@example.com", "password": "Pass1"},
    )
    assert res.status_code == 422

    # No digits
    res = client.post(
        "/auth/register",
        json={"name": "Student", "email": "s2@example.com", "password": "PasswordOnly"},
    )
    assert res.status_code == 422

    # No letters
    res = client.post(
        "/auth/register",
        json={"name": "Student", "email": "s3@example.com", "password": "1234567890"},
    )
    assert res.status_code == 422


def test_register_bad_email():
    res = client.post(
        "/auth/register",
        json={"name": "Student", "email": "not-an-email", "password": "Password123"},
    )
    assert res.status_code == 422


def test_register_invalid_name():
    # Too short (< 2)
    res = client.post(
        "/auth/register",
        json={"name": " A ", "email": "s4@example.com", "password": "Password123"},
    )
    assert res.status_code == 422


# --------------------------------------------------
# Login Tests
# --------------------------------------------------

def test_login_success_and_cookie():
    # Register
    client.post(
        "/auth/register",
        json={"name": "Priya Patel", "email": "priya@lpu.in", "password": "SecurePass99"},
    )

    # Login
    res = client.post(
        "/auth/login",
        json={"email": "PRIYA@lpu.in", "password": "SecurePass99", "remember_me": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Priya Patel"
    assert data["email"] == "priya@lpu.in"

    # Check session cookie set
    assert "session_token" in res.cookies
    cookie = res.cookies["session_token"]
    assert len(cookie) > 20


def test_login_fail_bad_password():
    client.post(
        "/auth/register",
        json={"name": "Priya Patel", "email": "priya2@lpu.in", "password": "SecurePass99"},
    )

    res = client.post(
        "/auth/login",
        json={"email": "priya2@lpu.in", "password": "WrongPassword1"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_login_fail_nonexistent_email():
    res = client.post(
        "/auth/login",
        json={"email": "nonexistent@lpu.in", "password": "SomePassword123"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


# --------------------------------------------------
# /auth/me and Session Validation Tests
# --------------------------------------------------

def test_auth_me_with_and_without_cookie():
    # 1. Without cookie -> 401
    res_no_cookie = client.get("/auth/me")
    assert res_no_cookie.status_code == 401

    # 2. Register & login
    client.post(
        "/auth/register",
        json={"name": "Rohan Verma", "email": "rohan@example.com", "password": "Password123"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "rohan@example.com", "password": "Password123"},
    )
    assert login_res.status_code == 200
    token = login_res.cookies.get("session_token")

    # 3. With valid cookie -> 200
    res_with_cookie = client.get("/auth/me", cookies={"session_token": token})
    assert res_with_cookie.status_code == 200
    user_data = res_with_cookie.json()
    assert user_data["name"] == "Rohan Verma"
    assert user_data["email"] == "rohan@example.com"


def test_logout_invalidates_session():
    # Register & login
    client.post(
        "/auth/register",
        json={"name": "Simran Kaur", "email": "simran@example.com", "password": "Password123"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "simran@example.com", "password": "Password123"},
    )
    token = login_res.cookies.get("session_token")

    # Verify session works
    me_res1 = client.get("/auth/me", cookies={"session_token": token})
    assert me_res1.status_code == 200

    # Logout
    logout_res = client.post("/auth/logout", cookies={"session_token": token})
    assert logout_res.status_code == 200
    assert "Logged out successfully" in logout_res.json()["message"]

    # Verify session is now rejected
    me_res2 = client.get("/auth/me", cookies={"session_token": token})
    assert me_res2.status_code == 401


# --------------------------------------------------
# Rate Limiting Tests (5 failed logins per 15 min -> 429)
# --------------------------------------------------

def test_login_rate_limiting():
    email = "target@example.com"
    client.post(
        "/auth/register",
        json={"name": "Target User", "email": email, "password": "CorrectPassword1"},
    )

    # 5 failed attempts
    for i in range(5):
        res = client.post("/auth/login", json={"email": email, "password": f"WrongPass{i}"})
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid email or password"

    # 6th attempt must trigger 429 Too Many Requests
    res_blocked = client.post("/auth/login", json={"email": email, "password": "CorrectPassword1"})
    assert res_blocked.status_code == 429
    assert "Too many failed login attempts" in res_blocked.json()["detail"]


# --------------------------------------------------
# Existing Endpoints Preservation Tests
# --------------------------------------------------

def test_health_check_and_resources_unaffected():
    # Health check
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ok"

    # Resources endpoint
    res_res = client.get("/resources")
    assert res_res.status_code == 200
    assert "resources" in res_res.json()
