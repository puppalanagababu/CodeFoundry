import uuid
from datetime import timedelta
import pytest
from fastapi import Depends, HTTPException
from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.dependencies.auth import get_current_user, require_role
from app.main import app
from app.models.user import User, UserRole
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    hash_password,
)

# Test helper endpoint for RBAC validation
@app.get("/api/test-recruiter-only/")
def mock_recruiter_endpoint(user: User = Depends(require_role(["RECRUITER", "ADMIN"]))):
    return {"status": "ok", "user": user.username, "role": user.role}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_register_and_login_flow(client: TestClient, db_session):
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"testuser_{unique_suffix}"
    email = f"{username}@example.com"
    password = "TestPassword@123"

    # 1. Register
    reg_res = client.post(
        "/api/auth/register/",
        json={
            "username": username,
            "email": email,
            "password": password,
            "password2": password,
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["user"]["username"] == username
    assert reg_data["user"]["role"] == "STUDENT"

    # 2. Duplicate registration fails
    dup_res = client.post(
        "/api/auth/register/",
        json={
            "username": username,
            "email": email,
            "password": password,
            "password2": password,
        },
    )
    assert dup_res.status_code == 400

    # 3. Login
    login_res = client.post(
        "/api/auth/login/",
        json={"username": username, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access" in login_data
    assert "refresh" in login_data
    assert login_data["user"]["username"] == username

    access_token = login_data["access"]
    refresh_token = login_data["refresh"]

    # 4. Access /me with token
    me_res = client.get(
        "/api/auth/me/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == username

    # 5. Access /me without token fails
    unauth_res = client.get("/api/auth/me/")
    assert unauth_res.status_code == 401

    # 6. Refresh token rotation
    refresh_res = client.post(
        "/api/auth/refresh/",
        json={"refresh": refresh_token},
    )
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access" in refresh_data
    assert "refresh" in refresh_data
    new_access = refresh_data["access"]
    new_refresh = refresh_data["refresh"]

    # 7. Old refresh token is blacklisted and fails
    old_refresh_res = client.post(
        "/api/auth/refresh/",
        json={"refresh": refresh_token},
    )
    assert old_refresh_res.status_code == 401

    # 8. New access token works
    me_res2 = client.get(
        "/api/auth/me/",
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert me_res2.status_code == 200

    # 9. Logout blacklists the new refresh token
    logout_res = client.post(
        "/api/auth/logout/",
        json={"refresh": new_refresh},
    )
    assert logout_res.status_code == 200

    # 10. Logged out refresh token fails
    after_logout_res = client.post(
        "/api/auth/refresh/",
        json={"refresh": new_refresh},
    )
    assert after_logout_res.status_code == 401


def test_invalid_login_credentials(client: TestClient):
    random_user = f"nonexistent_{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/auth/login/",
        json={"username": random_user, "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    assert "detail" in res.json()


def test_existing_user_login(client: TestClient, db_session):
    user = db_session.query(User).filter(User.is_active == True).first()
    if user:
        user.password = hash_password("ValidPassword@123")
        db_session.commit()

        login_res = client.post(
            "/api/auth/login/",
            json={"username": user.username, "password": "ValidPassword@123"},
        )
        assert login_res.status_code == 200
        assert "access" in login_res.json()


def test_password_reset_flow(client: TestClient, db_session):
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"resetuser_{unique_suffix}"
    email = f"{username}@example.com"
    initial_password = "OldPassword@123"
    new_password = "NewSecurePassword@456"

    # Create user
    user = User(
        username=username,
        email=email,
        password=hash_password(initial_password),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 1. Request reset
    req_res = client.post(
        "/api/auth/password-reset/",
        json={"email": email},
    )
    assert req_res.status_code == 200

    # 2. Generate token for user
    uid_b64, reset_token = generate_password_reset_token(user.id)

    # 3. Confirm reset
    confirm_res = client.post(
        "/api/auth/password-reset/confirm/",
        json={
            "uid": uid_b64,
            "token": reset_token,
            "new_password": new_password,
            "new_password2": new_password,
        },
    )
    assert confirm_res.status_code == 200

    # 4. Login with new password
    login_res = client.post(
        "/api/auth/login/",
        json={"username": username, "password": new_password},
    )
    assert login_res.status_code == 200

    # 5. Old password fails
    old_login_res = client.post(
        "/api/auth/login/",
        json={"username": username, "password": initial_password},
    )
    assert old_login_res.status_code == 401


def test_login_rate_limiting(client: TestClient):
    target_user = f"brute_target_{uuid.uuid4().hex[:6]}"
    for _ in range(5):
        client.post(
            "/api/auth/login/",
            json={"username": target_user, "password": "WrongPassword"},
        )

    blocked_res = client.post(
        "/api/auth/login/",
        json={"username": target_user, "password": "WrongPassword"},
    )
    assert blocked_res.status_code == 429


def test_role_based_access_control(client: TestClient, db_session):
    # 1. Student User
    student = User(
        username=f"student_{uuid.uuid4().hex[:6]}",
        email="student@example.com",
        password=hash_password("Pass123!"),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    # 2. Recruiter User
    recruiter = User(
        username=f"recruiter_{uuid.uuid4().hex[:6]}",
        email="recruiter@example.com",
        password=hash_password("Pass123!"),
        role=UserRole.RECRUITER.value,
        is_active=True,
    )
    db_session.add_all([student, recruiter])
    db_session.commit()
    db_session.refresh(student)
    db_session.refresh(recruiter)

    student_token = create_access_token(student.id, student.role)
    recruiter_token = create_access_token(recruiter.id, recruiter.role)

    # Student trying to access recruiter endpoint -> 403 Forbidden
    student_attempt = client.get(
        "/api/test-recruiter-only/",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_attempt.status_code == 403

    # Recruiter accessing recruiter endpoint -> 200 OK
    recruiter_attempt = client.get(
        "/api/test-recruiter-only/",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert recruiter_attempt.status_code == 200
    assert recruiter_attempt.json()["role"] == "RECRUITER"
