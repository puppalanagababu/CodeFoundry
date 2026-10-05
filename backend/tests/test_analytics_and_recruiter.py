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


# 6. CF-019 Calibrated Performance Scoring Tests
def test_performance_scoring_optimal_execution():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(
        id=1,
        slug="the-slow-report-generator",
        time_limit=5,
        memory_limit=128,
        challenge_type="PERFORMANCE",
    )
    # 5 test cases: T_opt = 5 * 0.15 = 0.75s, M_opt = 32MB
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=5,
        tests_failed=0,
        execution_time=0.45,
        memory_used=22.0,
    )
    assert breakdown["scores"]["performance"] == 100
    assert breakdown["evidence"]["performance"] == "execution_metrics"
    assert breakdown["scores"]["problem_solving"] == 100


def test_performance_scoring_proportional_interpolation():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(
        id=1,
        slug="the-slow-report-generator",
        time_limit=5,
        memory_limit=128,
        challenge_type="PERFORMANCE",
    )
    # T_opt = 0.75s, T_naive = 6.00s. Midpoint = 3.375s (TimeScore = 0.50)
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=5,
        tests_failed=0,
        execution_time=3.375,
        memory_used=20.0,  # MemScore = 1.0
    )
    # 0.75 * 0.50 + 0.25 * 1.0 = 0.625 -> 62.5 -> round half-to-even = 62
    assert breakdown["scores"]["performance"] == 62


def test_performance_scoring_slower_than_naive_threshold():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(
        id=1,
        slug="the-slow-report-generator",
        time_limit=5,
        memory_limit=128,
        challenge_type="PERFORMANCE",
    )
    # Slower than T_naive (6.00s) and high memory (128MB)
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=5,
        tests_failed=0,
        execution_time=7.50,
        memory_used=128.0,
    )
    assert breakdown["scores"]["performance"] == 0


def test_performance_scoring_crash_and_timeout_zero_score():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(
        id=1,
        slug="the-slow-report-generator",
        time_limit=5,
        memory_limit=128,
        challenge_type="PERFORMANCE",
    )
    # 0 passed tests (e.g. timeout or crash)
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=0,
        tests_failed=5,
        execution_time=5.0,
        memory_used=15.0,
    )
    assert breakdown["scores"]["performance"] == 0
    assert breakdown["scores"]["problem_solving"] == 0


def test_performance_scoring_missing_and_invalid_inputs():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(id=1, slug="fix-the-broken-calculator", time_limit=5, memory_limit=128)

    # Missing execution_time
    b1 = service.calculate_skill_breakdown(challenge=challenge, tests_total=5, tests_passed=5, tests_failed=0, execution_time=None)
    assert b1["scores"]["performance"] is None
    assert b1["evidence"]["performance"] == "not_measured"

    # Negative execution_time
    b2 = service.calculate_skill_breakdown(challenge=challenge, tests_total=5, tests_passed=5, tests_failed=0, execution_time=-1.0)
    assert b2["scores"]["performance"] is None

    # Zero tests_total
    b3 = service.calculate_skill_breakdown(challenge=challenge, tests_total=0, tests_passed=0, tests_failed=0, execution_time=0.1)
    assert b3["scores"]["performance"] is None


def test_performance_scoring_invalid_thresholds_safe_guard():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    # Invalid challenge where t_optimal >= t_naive
    class CustomChallenge:
        t_optimal = 10.0
        t_naive = 5.0
        time_limit = 5
        memory_limit = 128
        challenge_type = "PERFORMANCE"
        slug = "custom-challenge"

    challenge = CustomChallenge()
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=1,
        tests_passed=1,
        tests_failed=0,
        execution_time=2.0,
        memory_used=20.0,
    )
    assert 0 <= breakdown["scores"]["performance"] <= 100


# 7. CF-020 Debugging and Security Measurement Tests
def test_debugging_scoring_all_defect_and_regression_pass():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(id=1, slug="fix-the-broken-calculator", challenge_type="BUG_FIX")
    test_results = [
        {"name": "Basic Arithmetic", "passed": True, "is_hidden": False},
        {"name": "Compound Expression", "passed": True, "is_hidden": False},
        {"name": "Mixed Operations with Division", "passed": True, "is_hidden": True},
        {"name": "Division by Zero Handling", "passed": True, "is_hidden": True},
        {"name": "Chained Multi-Operator Expression", "passed": True, "is_hidden": True},
    ]
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=5,
        tests_failed=0,
        test_results=test_results,
    )
    assert breakdown["scores"]["debugging"] == 100
    assert breakdown["evidence"]["debugging"] == "defect_and_regression_tests"


def test_debugging_scoring_regression_failure_drops_score():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(id=1, slug="fix-the-broken-calculator", challenge_type="BUG_FIX")
    # Defect tests all pass, but baseline regression test fails
    test_results = [
        {"name": "Basic Arithmetic", "passed": False, "is_hidden": False},  # Regression failed!
        {"name": "Compound Expression", "passed": True, "is_hidden": False},
        {"name": "Mixed Operations with Division", "passed": True, "is_hidden": True},
        {"name": "Division by Zero Handling", "passed": True, "is_hidden": True},
        {"name": "Chained Multi-Operator Expression", "passed": True, "is_hidden": True},
    ]
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=4,
        tests_failed=1,
        test_results=test_results,
    )
    # Defect: 4/4 = 1.0, Regression: 0/1 = 0.0 -> Score = 0
    assert breakdown["scores"]["debugging"] == 0
    assert breakdown["scores"]["problem_solving"] == 80  # PS gives partial credit (4/5)


def test_debugging_scoring_partial_defect_resolution():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(id=1, slug="fix-the-broken-calculator", challenge_type="BUG_FIX")
    # Baseline passes, but only 2 of 4 defect tests pass
    test_results = [
        {"name": "Basic Arithmetic", "passed": True, "is_hidden": False},
        {"name": "Compound Expression", "passed": True, "is_hidden": False},
        {"name": "Mixed Operations with Division", "passed": True, "is_hidden": True},
        {"name": "Division by Zero Handling", "passed": False, "is_hidden": True},
        {"name": "Chained Multi-Operator Expression", "passed": False, "is_hidden": True},
    ]
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=3,
        tests_failed=2,
        test_results=test_results,
    )
    # Defect: 2/4 = 0.5, Regression: 1/1 = 1.0 -> Score = 50
    assert breakdown["scores"]["debugging"] == 50


def test_security_scoring_all_exploit_blocked_and_authorized_pass():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(id=1, slug="the-exposed-admin-endpoint", challenge_type="SECURITY")
    test_results = [
        {"name": "Administrator access", "passed": True, "is_hidden": False},
        {"name": "Public endpoint behavior", "passed": True, "is_hidden": False},
        {"name": "Restricted account access", "passed": True, "is_hidden": True},
        {"name": "Missing authentication access", "passed": True, "is_hidden": True},
        {"name": "Secondary non-admin role rejection", "passed": True, "is_hidden": True},
    ]
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=5,
        tests_failed=0,
        test_results=test_results,
    )
    assert breakdown["scores"]["security"] == 100
    assert breakdown["evidence"]["security"] == "exploit_and_authorization_tests"


def test_security_scoring_deny_all_exploit_blocked_from_full_score():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(id=1, slug="the-exposed-admin-endpoint", challenge_type="SECURITY")
    # Deny-all: All exploit tests pass (403 returned), but all authorized tests fail (admin denied)
    test_results = [
        {"name": "Administrator access", "passed": False, "is_hidden": False},  # Failed!
        {"name": "Public endpoint behavior", "passed": False, "is_hidden": False},  # Failed!
        {"name": "Restricted account access", "passed": True, "is_hidden": True},
        {"name": "Missing authentication access", "passed": True, "is_hidden": True},
        {"name": "Secondary non-admin role rejection", "passed": True, "is_hidden": True},
    ]
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=3,
        tests_failed=2,
        test_results=test_results,
    )
    # Exploit: 3/3 = 1.0 (60%), Auth: 0/2 = 0.0 (0%) -> Score = 60
    assert breakdown["scores"]["security"] == 60
    assert breakdown["scores"]["problem_solving"] == 60


def test_security_scoring_allow_all_unauthorized_fails_exploit_rejection():
    from app.services.skill_scoring import SkillScoringService
    service = SkillScoringService()
    challenge = Challenge(id=1, slug="the-exposed-admin-endpoint", challenge_type="SECURITY")
    # Allow-all: Authorized pass (2/2), but exploits fail (0/3 blocked)
    test_results = [
        {"name": "Administrator access", "passed": True, "is_hidden": False},
        {"name": "Public endpoint behavior", "passed": True, "is_hidden": False},
        {"name": "Restricted account access", "passed": False, "is_hidden": True},
        {"name": "Missing authentication access", "passed": False, "is_hidden": True},
        {"name": "Secondary non-admin role rejection", "passed": False, "is_hidden": True},
    ]
    breakdown = service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=2,
        tests_failed=3,
        test_results=test_results,
    )
    # Exploit: 0/3 = 0.0 (0%), Auth: 2/2 = 1.0 (40%) -> Score = 40
    assert breakdown["scores"]["security"] == 40


