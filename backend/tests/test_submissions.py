from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import Base, get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.challenge import Challenge, ChallengeFile, ChallengeType, Difficulty, TestCase
from app.models.evaluation import Achievement, Evaluation, EvaluationStatus, RequirementType, UserAchievement
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.services.achievement_service import AchievementService
from app.services.evaluation_service import EvaluationService, normalize_output
from app.services.skill_scoring import SkillScoringService
from app.execution.runner import ExecutionResult


# Setup fixtures
@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="student1",
        email="student1@example.com",
        role=UserRole.STUDENT.value,
        is_active=True,
    )


@pytest.fixture
def mock_attacker():
    return User(
        id=2,
        username="attacker",
        email="attacker@example.com",
        role=UserRole.STUDENT.value,
        is_active=True,
    )


@pytest.fixture
def client(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client


# 1. Output normalization tests
def test_normalize_output():
    assert normalize_output("hello world \r\n") == "hello world"
    assert normalize_output("  line 1  \r\nline 2   ") == "line 1\nline 2"
    assert normalize_output(None) == ""


# 2. Unauthenticated request rejection
def test_unauthenticated_request_is_rejected(unauthed_client):
    response = unauthed_client.post("/api/submissions/", json={"challenge": 1, "code": "print(1)"})
    assert response.status_code == 401

    response = unauthed_client.get("/api/submissions/")
    assert response.status_code == 401

    response = unauthed_client.get("/api/submissions/1/")
    assert response.status_code == 401

    response = unauthed_client.get("/api/submissions/best/")
    assert response.status_code == 401


# 3. Validation & Sanitization Tests
def test_missing_code_and_files_rejected(client):
    response = client.post("/api/submissions/", json={"challenge": 1})
    assert response.status_code in [400, 422]


def test_test_file_injection_is_stripped():
    from app.schemas.submission import SubmissionCreateRequest
    req = SubmissionCreateRequest(
        challenge=1,
        files={
            "app/solution.py": "def add(a, b): return a + b",
            "tests/test_solution.py": "def test_bypass(): assert True",
            "test_hack.py": "import os; os.system('rm -rf /')",
            "check_test.py": "assert 1 == 1",
        }
    )
    assert "app/solution.py" in req.files
    assert "tests/test_solution.py" not in req.files
    assert "test_hack.py" not in req.files
    assert "check_test.py" not in req.files
    assert req.code == "def add(a, b): return a + b"


# 4. Submission creation & Celery task dispatch
@patch("app.routers.submissions.evaluate_submission.delay")
def test_submission_creation_and_celery_dispatch(mock_delay, client, mock_user):
    mock_db = MagicMock(spec=Session)
    mock_challenge = Challenge(id=1, title="Test Challenge", points=100, is_active=True)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_challenge

    def add_side_effect(obj):
        if isinstance(obj, Submission):
            obj.id = 42

    mock_db.add.side_effect = add_side_effect
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/submissions/",
            json={"challenge": 1, "code": "print(42)", "language": "Python"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["submission_id"] == 42
        assert data["challenge"] == 1
        assert data["status"] == "PENDING"
        assert data["score"] == 0
        assert data["message"] == "Submission queued for evaluation."
        mock_delay.assert_called_once_with(42)
    finally:
        app.dependency_overrides.pop(get_db, None)


# 5. Nonexistent challenge rejection
def test_submission_nonexistent_challenge_rejected(client):
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/submissions/",
            json={"challenge": 9999, "code": "print(1)"}
        )
        assert response.status_code == 400
        assert "challenge" in response.json()
    finally:
        app.dependency_overrides.pop(get_db, None)


# 6. Submission detail view & Hidden test masking
def test_submission_detail_masks_hidden_tests(client, mock_user):
    mock_db = MagicMock(spec=Session)
    submission = Submission(
        id=10,
        user_id=mock_user.id,
        challenge_id=1,
        status="PASSED",
        score=100,
    )
    evaluation = Evaluation(
        id=5,
        submission_id=10,
        status="COMPLETED",
        score=100,
        tests_total=2,
        tests_passed=2,
        tests_failed=0,
        stdout="Output",
        stderr="",
        execution_time=0.15,
        memory_used=12.5,
        test_results=[
            {
                "test_case_id": 1,
                "name": "Visible test",
                "passed": True,
                "is_hidden": False,
                "points": 50,
                "max_points": 50,
                "input_data": "2 3",
                "expected_output": "5",
                "stdout": "5",
                "stderr": "",
                "execution_time": 0.05,
            },
            {
                "test_case_id": 2,
                "name": "Hidden test",
                "passed": True,
                "is_hidden": True,
                "points": 50,
                "max_points": 50,
                "input_data": "SECRET",
                "expected_output": "SECRET_OUT",
                "stdout": "SECRET_OUT",
                "stderr": "",
                "execution_time": 0.06,
            }
        ],
        skill_breakdown={"problem_solving": 100},
    )
    submission.evaluation = evaluation
    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = submission
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/submissions/10/")
        assert response.status_code == 200
        data = response.json()
        assert data["submission_id"] == 10
        assert data["status"] == "PASSED"
        assert data["score"] == 100
        assert data["evaluation"] is not None

        results = data["evaluation"]["test_results"]
        assert len(results) == 2

        # Visible test includes details
        assert results[0]["is_hidden"] is False
        assert results[0]["input_data"] == "2 3"
        assert results[0]["expected_output"] == "5"
        assert results[0]["actual_output"] == "5"

        # Hidden test masks input/output
        assert results[1]["is_hidden"] is True
        assert results[1]["input_data"] is None
        assert results[1]["expected_output"] is None
        assert results[1]["actual_output"] is None
        assert results[1]["stderr"] is None
    finally:
        app.dependency_overrides.pop(get_db, None)


# 7. User ownership isolation
def test_user_cannot_access_other_users_submission(client):
    mock_db = MagicMock(spec=Session)
    # Query returns None because user_id doesn't match
    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/submissions/999/")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


# 8. Best Submissions Endpoint
def test_best_submissions_aggregation(client, mock_user):
    mock_db = MagicMock(spec=Session)
    challenge1 = Challenge(id=1, title="Add Numbers")
    challenge2 = Challenge(id=2, title="Bug Fix")

    sub1 = Submission(
        id=1, user_id=mock_user.id, challenge_id=1, score=50, status="FAILED",
        submitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc), challenge=challenge1
    )
    sub2 = Submission(
        id=2, user_id=mock_user.id, challenge_id=1, score=100, status="PASSED",
        submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc), challenge=challenge1
    )
    sub3 = Submission(
        id=3, user_id=mock_user.id, challenge_id=2, score=80, status="FAILED",
        submitted_at=datetime(2026, 1, 3, tzinfo=timezone.utc), challenge=challenge2
    )

    mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [
        sub1, sub2, sub3
    ]
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/submissions/best/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2

        ch1_res = next(r for r in data["results"] if r["challenge"] == 1)
        assert ch1_res["challenge_title"] == "Add Numbers"
        assert ch1_res["best_score"] == 100
        assert ch1_res["attempts"] == 2

        ch2_res = next(r for r in data["results"] if r["challenge"] == 2)
        assert ch2_res["challenge_title"] == "Bug Fix"
        assert ch2_res["best_score"] == 80
        assert ch2_res["attempts"] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)


# 9. Submissions History Listing with filters
def test_list_submissions_filters_and_pagination(client, mock_user):
    mock_db = MagicMock(spec=Session)
    challenge1 = Challenge(id=1, title="Add Numbers", slug="add-numbers")
    sub1 = Submission(
        id=10, user_id=mock_user.id, challenge_id=1, score=100, status="PASSED",
        language="Python", submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        challenge=challenge1, evaluation=None
    )

    query_mock = mock_db.query.return_value.options.return_value.filter.return_value
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.count.return_value = 1
    query_mock.offset.return_value.limit.return_value.all.return_value = [sub1]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/submissions/?challenge=1&status=PASSED&page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == 10
        assert data["results"][0]["challenge_slug"] == "add-numbers"
    finally:
        app.dependency_overrides.pop(get_db, None)


# 10. Evaluation Service Logic & Scoring
def test_evaluation_service_execution():
    mock_exec_service = MagicMock()
    mock_exec_service.execute.return_value = ExecutionResult(
        stdout="5\n",
        stderr="",
        exit_code=0,
        execution_time=0.1,
        memory_used=5.0,
    )

    mock_skill_service = SkillScoringService()
    mock_ach_service = MagicMock()

    service = EvaluationService(
        execution_service=mock_exec_service,
        skill_scoring_service=mock_skill_service,
        achievement_service=mock_ach_service,
    )

    challenge = Challenge(
        id=1,
        title="Calculator",
        points=100,
        time_limit=5,
        memory_limit=128,
        challenge_type="BUG_FIX",
    )
    test_case = TestCase(
        id=1,
        challenge_id=1,
        name="Test 1",
        input_data="2 3",
        expected_output="5",
        points=100,
        is_hidden=False,
        is_active=True,
    )
    submission = Submission(
        id=100,
        user_id=1,
        challenge_id=1,
        code="print(5)",
        language="Python",
        challenge=challenge,
    )

    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [test_case]
    mock_db.query.return_value.filter.return_value.all.return_value = []

    evaluation = service.evaluate(mock_db, submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert evaluation.score == 100
    assert evaluation.tests_passed == 1
    assert evaluation.tests_failed == 0
    assert submission.status == SubmissionStatus.PASSED.value
    assert submission.score == 100
    mock_ach_service.award_for_user.assert_called_once_with(mock_db, 1)


# 11. Achievement Service Logic
def test_achievement_service_awarding():
    service = AchievementService()
    mock_db = MagicMock(spec=Session)

    ach = Achievement(
        id=1,
        code="BUG_SLAYER",
        name="Bug Slayer",
        description="Passed 3 Bug Fix challenges",
        requirement_type=RequirementType.BUG_FIX_COUNT.value,
        requirement_value=1,
        is_active=True,
    )

    challenge = Challenge(
        id=1,
        challenge_type=ChallengeType.BUG_FIX.value,
        is_active=True,
    )
    submission = Submission(
        id=10,
        user_id=1,
        challenge_id=1,
        status=SubmissionStatus.PASSED.value,
        score=100,
        challenge=challenge,
    )
    evaluation = Evaluation(
        id=10,
        submission_id=10,
        status=EvaluationStatus.COMPLETED.value,
        submission=submission,
        evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    mock_db.query.return_value.filter.return_value.all.return_value = [ach]
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [evaluation]
    mock_db.query.return_value.filter.return_value.all.side_effect = [[ach], []]

    awarded = service.award_for_user(mock_db, user_id=1)
    assert len(awarded) == 1
    mock_db.commit.assert_called()


# 12. CF-016 Readonly File & Test Protection Enforcement Tests
def test_evaluation_service_readonly_file_cannot_be_overridden():
    mock_exec_service = MagicMock()
    mock_exec_service.execute.return_value = ExecutionResult(
        stdout="42\n",
        stderr="",
        exit_code=0,
        execution_time=0.1,
        memory_used=5.0,
    )
    mock_skill_service = SkillScoringService()
    mock_ach_service = MagicMock()

    service = EvaluationService(
        execution_service=mock_exec_service,
        skill_scoring_service=mock_skill_service,
        achievement_service=mock_ach_service,
    )

    challenge = Challenge(
        id=1,
        title="Calculator Service",
        points=100,
        time_limit=5,
        memory_limit=128,
        entrypoint="app/main.py",
    )
    readme_file = ChallengeFile(
        challenge_id=1,
        path="README.md",
        content="AUTHORITATIVE_README",
        is_readonly=True,
        is_test=False,
    )
    req_file = ChallengeFile(
        challenge_id=1,
        path="requirements.txt",
        content="AUTHORITATIVE_REQUIREMENTS",
        is_readonly=True,
        is_test=False,
    )
    calc_file = ChallengeFile(
        challenge_id=1,
        path="app/calculator.py",
        content="OLD_CALC_IMPLEMENTATION",
        is_readonly=False,
        is_test=False,
    )
    test_case = TestCase(
        id=1,
        challenge_id=1,
        name="Test 1",
        input_data="10 20",
        expected_output="42",
        points=100,
        is_hidden=False,
        is_active=True,
    )
    submission = Submission(
        id=101,
        user_id=1,
        challenge_id=1,
        files={
            "README.md": "STUDENT_OVERWRITTEN_README",
            "requirements.txt": "STUDENT_OVERWRITTEN_REQ",
            "app/calculator.py": "STUDENT_NEW_CALC",
        },
        language="Python",
        challenge=challenge,
    )

    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [test_case]
    # challenge_files query
    mock_db.query.return_value.filter.return_value.all.return_value = [
        readme_file, req_file, calc_file
    ]

    service.evaluate(mock_db, submission)

    # Verify files passed to execution_service
    executed_files = mock_exec_service.execute.call_args.kwargs.get("files", {})
    assert executed_files["README.md"] == "AUTHORITATIVE_README", "Readonly README.md must retain server content"
    assert executed_files["requirements.txt"] == "AUTHORITATIVE_REQUIREMENTS", "Readonly requirements.txt must retain server content"
    assert executed_files["app/calculator.py"] == "STUDENT_NEW_CALC", "Editable calculator.py should be overridden"


def test_evaluation_service_test_file_cannot_be_overridden():
    mock_exec_service = MagicMock()
    mock_exec_service.execute.return_value = ExecutionResult(
        stdout="42\n",
        stderr="",
        exit_code=0,
        execution_time=0.1,
        memory_used=5.0,
    )
    service = EvaluationService(
        execution_service=mock_exec_service,
        skill_scoring_service=SkillScoringService(),
        achievement_service=MagicMock(),
    )

    challenge = Challenge(id=1, title="Calculator", points=100, entrypoint="app/main.py")
    test_file = ChallengeFile(
        challenge_id=1,
        path="tests/test_calculator.py",
        content="AUTHORITATIVE_SERVER_TEST_SUITE",
        is_readonly=True,
        is_test=True,
    )
    calc_file = ChallengeFile(
        challenge_id=1,
        path="app/calculator.py",
        content="OLD_CODE",
        is_readonly=False,
        is_test=False,
    )
    test_case = TestCase(
        id=1,
        challenge_id=1,
        name="Test 1",
        input_data="",
        expected_output="42",
        points=100,
        is_hidden=False,
        is_active=True,
    )
    submission = Submission(
        id=102,
        user_id=1,
        challenge_id=1,
        files={
            "tests/test_calculator.py": "HACKED_TEST_ASSERT_TRUE",
            "test_exploit.py": "def test_bypass(): pass",
            "app/calculator.py": "FIXED_CODE",
        },
        language="Python",
        challenge=challenge,
    )

    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [test_case]
    mock_db.query.return_value.filter.return_value.all.return_value = [test_file, calc_file]

    service.evaluate(mock_db, submission)

    executed_files = mock_exec_service.execute.call_args.kwargs.get("files", {})
    assert executed_files["tests/test_calculator.py"] == "AUTHORITATIVE_SERVER_TEST_SUITE"
    assert "test_exploit.py" not in executed_files
    assert executed_files["app/calculator.py"] == "FIXED_CODE"


def test_evaluation_service_alternate_path_representations_protected():
    mock_exec_service = MagicMock()
    mock_exec_service.execute.return_value = ExecutionResult(
        stdout="42\n",
        stderr="",
        exit_code=0,
        execution_time=0.1,
        memory_used=5.0,
    )
    service = EvaluationService(
        execution_service=mock_exec_service,
        skill_scoring_service=SkillScoringService(),
        achievement_service=MagicMock(),
    )

    challenge = Challenge(id=1, title="Calculator", points=100, entrypoint="app/main.py")
    readme_file = ChallengeFile(
        challenge_id=1,
        path="README.md",
        content="SERVER_README",
        is_readonly=True,
        is_test=False,
    )
    calc_file = ChallengeFile(
        challenge_id=1,
        path="app/calculator.py",
        content="SERVER_CALC",
        is_readonly=False,
        is_test=False,
    )
    test_case = TestCase(
        id=1,
        challenge_id=1,
        name="Test 1",
        input_data="",
        expected_output="42",
        points=100,
        is_hidden=False,
        is_active=True,
    )
    submission = Submission(
        id=103,
        user_id=1,
        challenge_id=1,
        files={
            "./README.md": "HACKED_README_VIA_DOT_SLASH",
            ".\\README.md": "HACKED_README_VIA_BACKSLASH",
            "./app/calculator.py": "UPDATED_CALC_VIA_DOT_SLASH",
        },
        language="Python",
        challenge=challenge,
    )

    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [test_case]
    mock_db.query.return_value.filter.return_value.all.return_value = [readme_file, calc_file]

    service.evaluate(mock_db, submission)

    executed_files = mock_exec_service.execute.call_args.kwargs.get("files", {})
    assert executed_files["README.md"] == "SERVER_README"
    assert "./README.md" not in executed_files
    assert ".\\README.md" not in executed_files
    assert executed_files["app/calculator.py"] == "UPDATED_CALC_VIA_DOT_SLASH"


def test_evaluation_service_multi_file_submission_with_new_helpers():
    mock_exec_service = MagicMock()
    mock_exec_service.execute.return_value = ExecutionResult(
        stdout="42\n",
        stderr="",
        exit_code=0,
        execution_time=0.1,
        memory_used=5.0,
    )
    service = EvaluationService(
        execution_service=mock_exec_service,
        skill_scoring_service=SkillScoringService(),
        achievement_service=MagicMock(),
    )

    challenge = Challenge(id=1, title="Multi-File Challenge", points=100, entrypoint="app/main.py")
    main_file = ChallengeFile(
        challenge_id=1,
        path="app/main.py",
        content="from app.helper import compute; print(compute())",
        is_readonly=False,
        is_test=False,
    )
    test_case = TestCase(
        id=1,
        challenge_id=1,
        name="Test 1",
        input_data="",
        expected_output="42",
        points=100,
        is_hidden=False,
        is_active=True,
    )
    submission = Submission(
        id=104,
        user_id=1,
        challenge_id=1,
        files={
            "app/main.py": "from app.helper import compute; print(compute())",
            "app/helper.py": "def compute(): return 42",
        },
        language="Python",
        challenge=challenge,
    )

    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [test_case]
    mock_db.query.return_value.filter.return_value.all.return_value = [main_file]

    service.evaluate(mock_db, submission)

    executed_files = mock_exec_service.execute.call_args.kwargs.get("files", {})
    assert "app/main.py" in executed_files
    assert "app/helper.py" in executed_files
    assert executed_files["app/helper.py"] == "def compute(): return 42"

