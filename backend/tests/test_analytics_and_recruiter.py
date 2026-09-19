from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.challenge import Challenge, ChallengeType, Difficulty
from app.models.evaluation import Achievement, Evaluation, EvaluationStatus, RequirementType, UserAchievement
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole


# Fixtures
@pytest.fixture
def mock_student():
    return User(
        id=1,
        username="student1",
        email="student1@example.com",
        role=UserRole.STUDENT.value,
        is_active=True,
    )


@pytest.fixture
def mock_recruiter():
    return User(
        id=2,
        username="recruiter_bob",
        email="recruiter@example.com",
        role=UserRole.RECRUITER.value,
        is_active=True,
    )


@pytest.fixture
def student_client(mock_student):
    app.dependency_overrides[get_current_user] = lambda: mock_student
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def recruiter_client(mock_recruiter):
    app.dependency_overrides[get_current_user] = lambda: mock_recruiter
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client


# 1. Dashboard Tests
def test_dashboard_unauthenticated_rejected(unauthed_client):
    response = unauthed_client.get("/api/dashboard/")
    assert response.status_code == 401


def test_dashboard_data_structure(student_client, mock_student):
    mock_db = MagicMock(spec=Session)

    challenge = Challenge(id=1, title="Add Numbers", difficulty="BEGINNER")
    sub = Submission(
        id=10,
        user_id=mock_student.id,
        challenge_id=1,
        challenge=challenge,
        status=SubmissionStatus.PASSED.value,
        score=100,
        language="Python",
        submitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    # Mock count and aggregate queries
    mock_db.query.return_value.filter.return_value.count.return_value = 5
    mock_db.query.return_value.filter.return_value.scalar.side_effect = [3, 2, 85.0]
    mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sub]
    mock_db.query.return_value.join.return_value.filter.return_value.scalar.side_effect = [
        1, 1, 100.0,  # BEGINNER
        0, 0, None,   # INTERMEDIATE
        0, 0, None,   # ADVANCED
        0, 0, None,   # EXPERT
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = student_client.get("/api/dashboard/")
        assert response.status_code == 200
        data = response.json()

        assert "overview" in data
        assert "recent_submissions" in data
        assert "difficulty_progress" in data
        assert data["overview"]["total_submissions"] == 5
        assert len(data["recent_submissions"]) == 1
        assert data["recent_submissions"][0]["challenge_title"] == "Add Numbers"
        assert len(data["difficulty_progress"]) == 4
    finally:
        app.dependency_overrides.pop(get_db, None)


# 2. Skill Profile Tests
def test_skill_profile_unauthenticated_rejected(unauthed_client):
    response = unauthed_client.get("/api/users/skill-profile/")
    assert response.status_code == 401


def test_skill_profile_calculation(student_client, mock_student):
    mock_db = MagicMock(spec=Session)

    challenge = Challenge(id=1, title="Fix Bug", challenge_type=ChallengeType.BUG_FIX.value, is_active=True)
    sub = Submission(id=1, user_id=mock_student.id, challenge_id=1, challenge=challenge, status="PASSED", score=100)
    evaluation = Evaluation(
        id=1,
        submission_id=1,
        status=EvaluationStatus.COMPLETED.value,
        submission=sub,
        skill_breakdown={
            "scores": {
                "problem_solving": 100,
                "debugging": 100,
                "security": None,
                "performance": 90,
                "code_quality": None,
                "testing": None,
            }
        },
        evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [evaluation]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = student_client.get("/api/users/skill-profile/")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] is not None
        assert data["total_evaluations_analyzed"] == 1
        assert data["skills"]["problem_solving"]["status"] == "measured"
        assert data["skills"]["problem_solving"]["score"] == 100
        assert data["skills"]["debugging"]["status"] == "measured"
        assert data["skills"]["code_quality"]["status"] == "not_measured"
        assert data["skills"]["security"]["status"] == "insufficient_data"
    finally:
        app.dependency_overrides.pop(get_db, None)


# 3. Leaderboard Tests
def test_leaderboard_unauthenticated_rejected(unauthed_client):
    response = unauthed_client.get("/api/leaderboard/")
    assert response.status_code == 401


def test_leaderboard_rankings_and_tie_breaking(student_client, mock_student):
    mock_db = MagicMock(spec=Session)

    u1 = User(id=1, username="alice")
    u2 = User(id=2, username="bob")

    c1 = Challenge(id=1, title="Challenge 1", is_active=True)
    c2 = Challenge(id=2, title="Challenge 2", is_active=True)

    s1 = Submission(id=1, user_id=1, user=u1, challenge_id=1, challenge=c1, status="PASSED", score=100)
    e1 = Evaluation(id=1, submission_id=1, submission=s1, status="COMPLETED", evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc), skill_breakdown={"scores": {"problem_solving": 100}})

    s2 = Submission(id=2, user_id=2, user=u2, challenge_id=2, challenge=c2, status="PASSED", score=80)
    e2 = Evaluation(id=2, submission_id=2, submission=s2, status="COMPLETED", evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc), skill_breakdown={"scores": {"problem_solving": 80}})

    mock_db.query.return_value.join.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [e1, e2]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = student_client.get("/api/leaderboard/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["rank"] == 1
        assert data["results"][0]["username"] == "alice"
        assert data["results"][0]["total_points"] == 100
        assert data["results"][0]["is_current_user"] is True
        assert data["results"][1]["rank"] == 2
        assert data["results"][1]["username"] == "bob"
    finally:
        app.dependency_overrides.pop(get_db, None)


# 4. Public Profile Tests
def test_public_profile_privacy_and_data(student_client):
    mock_db = MagicMock(spec=Session)
    user = User(id=10, username="public_alice", email="secret@example.com", password="hashedpassword")
    mock_db.query.return_value.filter.return_value.first.return_value = user

    # No evaluations or empty
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock_db.query.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = student_client.get("/api/users/profile/public_alice/")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "public_alice"
        # Privacy guarantees
        assert "password" not in data
        assert "email" not in data
        assert "jwt" not in data
        assert "token" not in data
        assert "skill_breakdown" in data
        assert "achievements" in data
        assert "recent_activity" in data
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_public_profile_not_found(student_client):
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = student_client.get("/api/users/profile/nonexistent_user/")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


# 5. Achievements Listing Tests
def test_achievements_endpoints(student_client, mock_student):
    mock_db = MagicMock(spec=Session)
    ach = Achievement(
        id=1,
        code="BUG_SLAYER",
        name="Bug Slayer",
        description="Passed 3 Bug Fix challenges",
        icon="🐛",
        is_active=True,
    )
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [ach]
    mock_db.query.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # All achievements
        response = student_client.get("/api/achievements/")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["code"] == "BUG_SLAYER"

        # User achievements
        response2 = student_client.get("/api/users/achievements/")
        assert response2.status_code == 200
        assert "results" in response2.json()
    finally:
        app.dependency_overrides.pop(get_db, None)


# 6. Recruiter Authorization & Endpoints
def test_recruiter_endpoints_rejected_for_student(student_client):
    response = student_client.get("/api/recruiter/candidates/")
    assert response.status_code == 403

    response = student_client.get("/api/recruiter/candidates/alice/")
    assert response.status_code == 403

    response = student_client.post("/api/recruiter/candidates/compare/", json={"usernames": ["alice", "bob"]})
    assert response.status_code == 403


def test_recruiter_candidate_list(recruiter_client):
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.join.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []
    mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = recruiter_client.get("/api/recruiter/candidates/?search=cand&min_skill_score=50")
        assert response.status_code == 200
        assert "results" in response.json()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_recruiter_candidate_comparison_limits(recruiter_client):
    # Less than 2 candidates
    response = recruiter_client.post("/api/recruiter/candidates/compare/", json={"usernames": ["alice"]})
    assert response.status_code == 400
    assert "Comparison requires between 2 and 5 candidates." in response.json()["detail"]

    # More than 5 candidates
    response = recruiter_client.post(
        "/api/recruiter/candidates/compare/",
        json={"usernames": ["u1", "u2", "u3", "u4", "u5", "u6"]}
    )
    assert response.status_code == 400
    assert "Comparison requires between 2 and 5 candidates." in response.json()["detail"]


def test_recruiter_candidate_comparison_success(recruiter_client):
    mock_db = MagicMock(spec=Session)
    u1 = User(id=1, username="alice")
    u2 = User(id=2, username="bob")

    def first_side_effect():
        return u1

    mock_db.query.return_value.filter.return_value.first.side_effect = [u1, u2]
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock_db.query.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = recruiter_client.post(
            "/api/recruiter/candidates/compare/",
            json={"usernames": ["alice", "bob"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert len(data["candidates"]) == 2
        assert data["candidates"][0]["username"] == "alice"
        assert data["candidates"][1]["username"] == "bob"
    finally:
        app.dependency_overrides.pop(get_db, None)
