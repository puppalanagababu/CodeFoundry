import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.challenge import Challenge, Difficulty, ChallengeType, TestCase, ChallengeFile
from app.models.user import User, UserRole
from app.models.submission import Submission, SubmissionStatus
from app.models.evaluation import Evaluation, EvaluationStatus, Achievement
from app.services.evaluation_service import EvaluationService
from app.services.auth_service import hash_password


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_complete_student_journey_e2e(client, db, monkeypatch):
    """
    End-to-End simulation of the complete student journey:
    Register -> Login -> Dashboard -> Challenge List -> Challenge Detail
    -> Code Execution -> Solution Submission -> Evaluation -> Score/Skill Breakdown
    -> Submission History -> Progress -> Achievements -> Skill Profile -> Leaderboard -> Public Profile.
    """
    # 0. Setup a verified challenge in DB if needed
    slug = "e2e-journey-calculator"
    challenge = db.query(Challenge).filter(Challenge.slug == slug).first()
    if not challenge:
        challenge = Challenge(
            title="E2E Broken Calculator",
            slug=slug,
            description="Fix broken basic arithmetic",
            difficulty=Difficulty.BEGINNER.value,
            challenge_type=ChallengeType.BUG_FIX.value,
            programming_language="Python",
            starter_code="class Calculator:\n    def add(self, a, b): return a + b\n",
            time_limit=5,
            memory_limit=128,
            points=100,
            is_active=True,
        )
        db.add(challenge)
        db.commit()
        db.refresh(challenge)

        # Add test cases
        tc1 = TestCase(
            challenge_id=challenge.id,
            name="Test Add",
            input_data="1 2",
            expected_output="3",
            is_hidden=False,
            points=50,
            is_active=True,
        )
        tc2 = TestCase(
            challenge_id=challenge.id,
            name="Test Add Negative",
            input_data="-1 -2",
            expected_output="-3",
            is_hidden=True,
            points=50,
            is_active=True,
        )
        db.add_all([tc1, tc2])
        db.commit()

    # Ensure an achievement definition exists
    ach = db.query(Achievement).filter(Achievement.code == "FIRST_SUBMISSION").first()
    if not ach:
        ach = Achievement(
            code="FIRST_SUBMISSION",
            name="First Submission",
            description="Submitted your first solution",
            icon="🚀",
            requirement_type="submissions_count",
            requirement_value=1,
            is_active=True,
        )
        db.add(ach)
        db.commit()

    # Step 1: Register
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"journey_alex_{unique_suffix}"
    email = f"alex_{unique_suffix}@example.com"
    password = "SecurePassword123!"

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
    assert reg_res.json()["user"]["username"] == username

    # Step 2: Login
    login_res = client.post(
        "/api/auth/login/",
        json={"username": username, "password": password},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    access_token = token_data["access"]
    refresh_token = token_data["refresh"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 3: Initial Dashboard
    dash_res = client.get("/api/dashboard/", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["overview"]["challenges_attempted"] == 0
    assert dash_data["overview"]["challenges_passed"] == 0

    # Step 4: Challenge List
    ch_list_res = client.get("/api/challenges/", headers=headers)
    assert ch_list_res.status_code == 200
    ch_list = ch_list_res.json()
    assert ch_list["count"] >= 1
    assert any(c["slug"] == slug for c in ch_list["results"])

    # Step 5: Challenge Detail
    ch_detail_res = client.get(f"/api/challenges/{challenge.id}/", headers=headers)
    assert ch_detail_res.status_code == 200
    ch_detail = ch_detail_res.json()
    assert ch_detail["title"] == challenge.title
    assert ch_detail["points"] == 100

    # Step 6: Workspace / Code Execution (Run Code in sandbox)
    run_res = client.post(
        "/api/execution/run/",
        json={
            "code": "print('CodeFoundry execution sandbox ready')",
            "language": "Python",
        },
        headers=headers,
    )
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] in ["SUCCESS", "FAILED"]

    # Step 7: Submit Solution (Queue for Celery evaluation)
    # Mock evaluate_submission Celery delay to avoid docker worker daemon in pytest
    monkeypatch.setattr("app.routers.submissions.evaluate_submission.delay", lambda *args, **kwargs: None)
    eval_service = EvaluationService()

    # Capture submission ID created
    sub_res = client.post(
        "/api/submissions/",
        json={
            "challenge": challenge.id,
            "code": "class Calculator:\n    def add(self, a, b):\n        return a + b\n",
            "language": "Python",
        },
        headers=headers,
    )
    assert sub_res.status_code == 201
    sub_data = sub_res.json()
    submission_id = sub_data["submission_id"]
    assert sub_data["status"] == "PENDING"

    # Step 8: Perform Evaluation via EvaluationService
    # Mock execution_service.execute to return correct outputs for both test cases
    from app.execution.runner import ExecutionResult

    def mock_execute(*args, **kwargs):
        stdin_val = kwargs.get("stdin_data", "") or ""
        expected = "-3\n" if "-1" in stdin_val else "3\n"
        return ExecutionResult(
            stdout=expected,
            stderr="",
            exit_code=0,
            execution_time=0.05,
            memory_used=12.0,
        )

    monkeypatch.setattr(eval_service.execution_service, "execute", mock_execute)
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    eval_result = eval_service.evaluate(db, sub)
    assert eval_result.status == EvaluationStatus.COMPLETED.value
    assert eval_result.score == 100

    # Step 9: Verify Submission Detail & Skill Breakdown
    sub_detail_res = client.get(f"/api/submissions/{submission_id}/", headers=headers)
    assert sub_detail_res.status_code == 200
    sub_detail = sub_detail_res.json()
    assert sub_detail["status"] == "PASSED"
    assert sub_detail["score"] == 100
    assert sub_detail["evaluation"]["status"] == "COMPLETED"
    assert sub_detail["evaluation"]["tests_passed"] == 2
    assert "skill_breakdown" in sub_detail["evaluation"]

    # Verify hidden test case masking
    test_results = sub_detail["evaluation"]["test_results"]
    hidden_case = next(tc for tc in test_results if tc["is_hidden"])
    assert hidden_case["input_data"] is None
    assert hidden_case["expected_output"] is None
    assert hidden_case["actual_output"] is None

    # Step 10: Submission History
    history_res = client.get("/api/submissions/", headers=headers)
    assert history_res.status_code == 200
    assert history_res.json()["count"] >= 1

    ch_history_res = client.get(f"/api/challenges/{challenge.id}/submissions/", headers=headers)
    assert ch_history_res.status_code == 200
    assert ch_history_res.json()["count"] >= 1

    # Step 11: Challenge Progress
    prog_res = client.get("/api/challenges/progress/", headers=headers)
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["summary"]["attempted_challenges"] >= 1
    assert prog_data["summary"]["completed_challenges"] >= 1

    # Step 12: Achievements
    ach_res = client.get("/api/users/achievements/", headers=headers)
    assert ach_res.status_code == 200
    assert isinstance(ach_res.json()["results"], list)

    # Step 13: Skill Profile
    skill_res = client.get("/api/users/skill-profile/", headers=headers)
    assert skill_res.status_code == 200
    skill_profile = skill_res.json()
    assert "skills" in skill_profile
    assert "problem_solving" in skill_profile["skills"]
    assert skill_profile["skills"]["problem_solving"]["status"] == "measured"

    # Step 14: Leaderboard
    lb_res = client.get("/api/leaderboard/", headers=headers)
    assert lb_res.status_code == 200
    lb_data = lb_res.json()
    assert len(lb_data["results"]) >= 1
    alex_entry = next((item for item in lb_data["results"] if item["username"] == username), None)
    assert alex_entry is not None
    assert alex_entry["challenges_completed"] >= 1

    # Step 15: Public Profile
    pub_res = client.get(f"/api/users/profile/{username}/", headers=headers)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["username"] == username
    assert pub_data["challenges_completed"] >= 1
    assert "skill_breakdown" in pub_data
    assert len(pub_data["recent_activity"]) >= 1


def test_student_auth_token_refresh_flow(client, db):
    """
    Verifies that a student can refresh their session token and continue accessing protected endpoints.
    """
    import uuid
    uid = uuid.uuid4().hex[:8]
    user = User(
        username=f"refresh_user_{uid}",
        email=f"refresh_{uid}@example.com",
        password=hash_password("Pass123!"),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Login to get initial tokens
    login_res = client.post(
        "/api/auth/login/",
        json={"username": user.username, "password": "Pass123!"},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    old_refresh = tokens["refresh"]

    # Refresh token
    refresh_res = client.post(
        "/api/auth/refresh/",
        json={"refresh": old_refresh},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access" in new_tokens
    assert "refresh" in new_tokens
    assert new_tokens["refresh"] != old_refresh

    # Access protected route with new access token
    headers = {"Authorization": f"Bearer {new_tokens['access']}"}
    me_res = client.get("/api/auth/me/", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == user.username


def test_student_failed_submission_journey(client, db, monkeypatch):
    """
    Simulates a student submitting an incorrect solution:
    Verifies status = FAILED, evaluation = COMPLETED, score = 0, and dashboard metrics update.
    """
    import uuid
    from app.execution.runner import ExecutionResult

    uid = uuid.uuid4().hex[:8]
    user = User(
        username=f"failing_student_{uid}",
        email=f"fail_{uid}@example.com",
        password=hash_password("Pass123!"),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db.add(user)

    ch = db.query(Challenge).filter(Challenge.slug == "e2e-journey-calculator").first()
    db.commit()
    db.refresh(user)

    login_res = client.post(
        "/api/auth/login/",
        json={"username": user.username, "password": "Pass123!"},
    )
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access']}"}

    # Submit buggy solution
    monkeypatch.setattr("app.routers.submissions.evaluate_submission.delay", lambda *args, **kwargs: None)
    sub_res = client.post(
        "/api/submissions/",
        json={
            "challenge": ch.id,
            "code": "class Calculator:\n    def add(self, a, b):\n        return a - b  # Bug!\n",
            "language": "Python",
        },
        headers=headers,
    )
    assert sub_res.status_code == 201
    sub_id = sub_res.json()["submission_id"]

    # Evaluate with failing execution result
    eval_service = EvaluationService()
    monkeypatch.setattr(
        eval_service.execution_service,
        "execute",
        lambda *args, **kwargs: ExecutionResult(
            stdout="-1\n",  # Wrong output
            stderr="",
            exit_code=0,
            execution_time=0.05,
            memory_used=10.0,
        ),
    )
    sub = db.query(Submission).filter(Submission.id == sub_id).first()
    eval_result = eval_service.evaluate(db, sub)

    assert eval_result.status == EvaluationStatus.COMPLETED.value
    assert eval_result.score == 0

    # Verify submission detail
    detail_res = client.get(f"/api/submissions/{sub_id}/", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "FAILED"
    assert detail["score"] == 0
    assert detail["evaluation"]["status"] == "COMPLETED"
    assert detail["evaluation"]["tests_failed"] == 2

