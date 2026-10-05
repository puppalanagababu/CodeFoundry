import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app.models.user import User, UserRole
from app.models.challenge import Challenge, ChallengeType, Difficulty
from app.models.submission import Submission, SubmissionStatus
from app.models.evaluation import Evaluation, EvaluationStatus
from app.services.auth_service import create_access_token, hash_password


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def test_user(db_session):
    user = db_session.query(User).filter(User.username == "contract_test_student").first()
    if not user:
        user = User(
            username="contract_test_student",
            email="contract_student@example.com",
            password=hash_password("StudentPass123!"),
            role=UserRole.STUDENT.value,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def recruiter_user(db_session):
    user = db_session.query(User).filter(User.username == "contract_test_recruiter").first()
    if not user:
        user = User(
            username="contract_test_recruiter",
            email="contract_recruiter@example.com",
            password=hash_password("RecruiterPass123!"),
            role=UserRole.RECRUITER.value,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session):
    user = db_session.query(User).filter(User.username == "contract_other_student").first()
    if not user:
        user = User(
            username="contract_other_student",
            email="contract_other@example.com",
            password=hash_password("OtherPass123!"),
            role=UserRole.STUDENT.value,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def sample_challenge(db_session):
    ch = db_session.query(Challenge).filter(Challenge.slug == "contract-test-challenge").first()
    if not ch:
        ch = Challenge(
            title="Contract Test Challenge",
            slug="contract-test-challenge",
            description="Testing API contracts and schemas",
            difficulty=Difficulty.BEGINNER.value,
            challenge_type=ChallengeType.BUG_FIX.value,
            programming_language="Python",
            starter_code="def solve():\n    pass\n",
            time_limit=5,
            memory_limit=128,
            points=100,
            is_active=True,
        )
        db_session.add(ch)
        db_session.commit()
        db_session.refresh(ch)
    return ch


def auth_headers(user: User) -> dict:
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Unauthenticated / Unauthorized Status Code Contracts
# ==============================================================================

def test_unauthenticated_request_returns_401_with_bearer_header(client):
    res = client.get("/api/challenges/")
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers
    assert "Bearer" in res.headers["WWW-Authenticate"]
    assert "detail" in res.json()


def test_recruiter_endpoint_forbidden_for_student_returns_403(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/recruiter/candidates/", headers=headers)
    assert res.status_code == 403
    assert "detail" in res.json()


def test_recruiter_endpoint_allowed_for_recruiter_returns_200(client, recruiter_user):
    headers = auth_headers(recruiter_user)
    res = client.get("/api/recruiter/candidates/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert isinstance(data["results"], list)


# ==============================================================================
# 2. Resource Not Found (404) Contracts
# ==============================================================================

def test_nonexistent_challenge_returns_404(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/challenges/99999999/", headers=headers)
    assert res.status_code == 404
    assert "detail" in res.json()


def test_nonexistent_submission_returns_404(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/submissions/99999999/", headers=headers)
    assert res.status_code == 404
    assert "detail" in res.json()


def test_nonexistent_public_profile_returns_404(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/users/profile/nonexistent_user_xyz_12345/", headers=headers)
    assert res.status_code == 404
    assert "detail" in res.json()


# ==============================================================================
# 3. Request Validation & Bad Request (400/422) Contracts
# ==============================================================================

def test_submission_creation_missing_code_and_files_rejected(client, test_user, sample_challenge):
    headers = auth_headers(test_user)
    res = client.post(
        "/api/submissions/",
        json={"challenge": sample_challenge.id, "code": "", "files": {}},
        headers=headers,
    )
    assert res.status_code in [400, 422]


def test_submission_creation_nonexistent_challenge_returns_400(client, test_user):
    headers = auth_headers(test_user)
    res = client.post(
        "/api/submissions/",
        json={"challenge": 99999999, "code": "print(1)"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "challenge" in res.json()


def test_execution_run_empty_payload_rejected(client, test_user):
    headers = auth_headers(test_user)
    res = client.post(
        "/api/execution/run/",
        json={"code": "", "files": {}},
        headers=headers,
    )
    assert res.status_code in [400, 422]


def test_invalid_difficulty_filter_returns_400(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/challenges/?difficulty=SUPER_HARD_INVALID", headers=headers)
    assert res.status_code == 400
    assert "error" in res.json()


def test_invalid_challenge_type_filter_returns_400(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/challenges/?challenge_type=QUANTUM_AI_INVALID", headers=headers)
    assert res.status_code == 400
    assert "error" in res.json()


def test_candidate_comparison_requires_2_to_5_candidates(client, recruiter_user):
    headers = auth_headers(recruiter_user)
    # Only 1 candidate
    res1 = client.post(
        "/api/recruiter/candidates/compare/",
        json={"usernames": ["single_candidate"]},
        headers=headers,
    )
    assert res1.status_code == 400

    # 6 candidates (more than 5)
    res6 = client.post(
        "/api/recruiter/candidates/compare/",
        json={"usernames": ["u1", "u2", "u3", "u4", "u5", "u6"]},
        headers=headers,
    )
    assert res6.status_code == 400


# ==============================================================================
# 4. Cross-User Privacy & Isolation
# ==============================================================================

def test_user_cannot_access_other_users_submission(client, db_session, test_user, other_user, sample_challenge):
    # Create submission owned by other_user
    sub = Submission(
        user_id=other_user.id,
        challenge_id=sample_challenge.id,
        code="def solve(): return True",
        status=SubmissionStatus.PASSED.value,
        score=100,
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    # Attempt to access with test_user
    headers = auth_headers(test_user)
    res = client.get(f"/api/submissions/{sub.id}/", headers=headers)
    assert res.status_code == 404  # Private resource returns 404 to prevent ID enumeration


# ==============================================================================
# 5. Pagination Contract Consistency
# ==============================================================================

def test_challenges_pagination_schema(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/challenges/?page=1&page_size=5", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) <= 5


def test_submissions_history_pagination_schema(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/submissions/?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data
    assert isinstance(data["results"], list)


# ==============================================================================
# 6. Submission & Evaluation Lifecycle Schema Invariants
# ==============================================================================

def test_submission_creation_and_lifecycle_response(client, db_session, test_user, sample_challenge, monkeypatch):
    # Mock Celery delay to avoid launching docker during test
    import app.routers.submissions as sub_router
    monkeypatch.setattr(sub_router.evaluate_submission, "delay", lambda *args, **kwargs: None)

    headers = auth_headers(test_user)
    res = client.post(
        "/api/submissions/",
        json={"challenge": sample_challenge.id, "code": "def solve(): return 42\n"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert "submission_id" in data
    assert data["challenge"] == sample_challenge.id
    assert data["status"] == "PENDING"
    assert data["score"] == 0
    assert "message" in data


def test_submission_detail_with_completed_evaluation_schema(client, db_session, test_user, sample_challenge):
    sub = Submission(
        user_id=test_user.id,
        challenge_id=sample_challenge.id,
        code="def solve(): return 42\n",
        status=SubmissionStatus.PASSED.value,
        score=100,
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    eval_record = Evaluation(
        submission_id=sub.id,
        status=EvaluationStatus.COMPLETED.value,
        score=100,
        tests_total=3,
        tests_passed=3,
        tests_failed=0,
        stdout="All tests passed",
        stderr="",
        execution_time=0.12,
        memory_used=12.5,
        test_results=[
            {
                "test_case_id": 1,
                "name": "Public Case 1",
                "passed": True,
                "points": 50,
                "max_points": 50,
                "execution_time": 0.04,
                "is_hidden": False,
                "input_data": "10",
                "expected_output": "20",
                "stdout": "20",
                "stderr": "",
            },
            {
                "test_case_id": 2,
                "name": "Hidden Case 2",
                "passed": True,
                "points": 50,
                "max_points": 50,
                "execution_time": 0.08,
                "is_hidden": True,
                "input_data": "SECRET_INPUT",
                "expected_output": "SECRET_OUTPUT",
                "stdout": "SECRET_OUTPUT",
                "stderr": "",
            },
        ],
        skill_breakdown={"problem_solving": 100, "code_quality": 95},
    )
    db_session.add(eval_record)
    db_session.commit()

    headers = auth_headers(test_user)
    res = client.get(f"/api/submissions/{sub.id}/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["submission_id"] == sub.id
    assert data["status"] == "PASSED"
    assert data["score"] == 100

    evaluation = data["evaluation"]
    assert evaluation["status"] == "COMPLETED"
    assert evaluation["score"] == 100
    assert evaluation["tests_total"] == 3
    assert len(evaluation["test_results"]) == 2

    # Verify hidden test case masking contract
    hidden_case = next(tc for tc in evaluation["test_results"] if tc["is_hidden"])
    assert hidden_case["input_data"] is None
    assert hidden_case["expected_output"] is None
    assert hidden_case["actual_output"] is None
    assert hidden_case["stderr"] is None

    # Verify public test case has data
    public_case = next(tc for tc in evaluation["test_results"] if not tc["is_hidden"])
    assert public_case["input_data"] == "10"
    assert public_case["expected_output"] == "20"


# ==============================================================================
# 7. Dashboard & Leaderboard Schemas
# ==============================================================================

def test_dashboard_endpoint_contract(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/dashboard/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "overview" in data
    assert "recent_submissions" in data
    assert "difficulty_progress" in data
    assert "challenges_attempted" in data["overview"]
    assert "challenges_passed" in data["overview"]


def test_leaderboard_endpoint_contract(client, test_user):
    headers = auth_headers(test_user)
    res = client.get("/api/leaderboard/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert isinstance(data["results"], list)
