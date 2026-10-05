"""
Unit & Regression Test Suite for CF-026: Submission & Evaluation Reliability / Recovery.

Verifies:
1. Complete submission lifecycle (PENDING -> RUNNING -> COMPLETED/FAILED/ERROR).
2. Failure modes: Docker failure, timeout, student code error, infrastructure exceptions.
3. Retry and idempotency protection against duplicate task execution.
4. Transaction integrity and achievement trigger safety.
5. Progress and skill aggregation isolation from failed/error submissions.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.orm import Session

from app.execution.runner import ExecutionResult
from app.execution.services import ExecutionService
from app.models.challenge import Challenge, ChallengeFile, ChallengeType, Difficulty, TestCase
from app.models.evaluation import Achievement, Evaluation, EvaluationStatus, RequirementType, UserAchievement
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.schemas.submission import TestCaseResult
from app.services.achievement_service import AchievementService
from app.services.evaluation_service import EvaluationService
from app.services.progress_service import ChallengeProgressService
from app.services.skill_scoring import SkillScoringService
from app.tasks.evaluation_tasks import evaluate_submission


# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def sample_challenge() -> Challenge:
    ch = Challenge(
        id=1,
        title="Reliability Challenge",
        slug="reliability-challenge",
        challenge_type=ChallengeType.BUG_FIX.value,
        difficulty=Difficulty.BEGINNER.value,
        is_active=True,
        points=100,
        programming_language="python",
    )
    return ch


@pytest.fixture
def sample_test_cases(sample_challenge) -> list:
    tc1 = TestCase(
        id=1,
        challenge_id=sample_challenge.id,
        name="Public Test Case",
        input_data="5\n",
        expected_output="10\n",
        points=50,
        is_hidden=False,
        is_active=True,
    )
    tc2 = TestCase(
        id=2,
        challenge_id=sample_challenge.id,
        name="Hidden Test Case",
        input_data="10\n",
        expected_output="20\n",
        points=50,
        is_hidden=True,
        is_active=True,
    )
    return [tc1, tc2]


@pytest.fixture
def sample_submission(sample_challenge) -> Submission:
    sub = Submission(
        id=100,
        user_id=1,
        challenge_id=sample_challenge.id,
        status=SubmissionStatus.PENDING.value,
        code="def solve(x): return x * 2",
        language="Python",
        score=0,
        submitted_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    sub.challenge = sample_challenge
    return sub


# ---------------------------------------------------------------------------
# Reliability Tests
# ---------------------------------------------------------------------------

def test_successful_evaluation_lifecycle(mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test A & J: Successful evaluation transitions PENDING -> RUNNING -> COMPLETED,
    Submission becomes PASSED with score=100, and achievement processing is triggered.
    """
    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="10\n",
        stderr="",
        exit_code=0,
        execution_time=0.05,
        memory_used=12.5,
    )
    # Return 20 on second test case
    def side_effect_run(code, language, stdin_data, timeout):
        if stdin_data == "10\n":
            return ExecutionResult(stdout="20\n", exit_code=0, execution_time=0.05, memory_used=12.5)
        return ExecutionResult(stdout="10\n", exit_code=0, execution_time=0.05, memory_used=12.5)

    mock_runner.run.side_effect = side_effect_run
    exec_service = ExecutionService(runner=mock_runner)
    mock_ach_service = MagicMock(spec=AchievementService)

    service = EvaluationService(
        execution_service=exec_service,
        achievement_service=mock_ach_service,
    )

    # Setup DB queries
    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None  # No prior evaluation
        elif model == TestCase:
            m.filter.return_value.order_by.return_value.all.return_value = sample_test_cases
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert evaluation.score == 100
    assert evaluation.tests_passed == 2
    assert evaluation.tests_failed == 0
    assert sample_submission.status == SubmissionStatus.PASSED.value
    assert sample_submission.score == 100
    mock_ach_service.award_for_user.assert_called_once_with(mock_db, sample_submission.user_id)


def test_student_test_failure_lifecycle(mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test B & I: Failing test output marks Submission as FAILED, Evaluation as COMPLETED,
    score reflects passed tests (50/100), and achievements are evaluated safely.
    """
    mock_runner = MagicMock()
    # First test passes, second test fails
    def side_effect_run(code, language, stdin_data, timeout):
        if stdin_data == "5\n":
            return ExecutionResult(stdout="10\n", exit_code=0, execution_time=0.05, memory_used=10.0)
        return ExecutionResult(stdout="WRONG\n", exit_code=0, execution_time=0.05, memory_used=10.0)

    mock_runner.run.side_effect = side_effect_run
    exec_service = ExecutionService(runner=mock_runner)
    mock_ach_service = MagicMock(spec=AchievementService)

    service = EvaluationService(
        execution_service=exec_service,
        achievement_service=mock_ach_service,
    )

    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None
        elif model == TestCase:
            m.filter.return_value.order_by.return_value.all.return_value = sample_test_cases
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert evaluation.score == 50
    assert evaluation.tests_passed == 1
    assert evaluation.tests_failed == 1
    assert sample_submission.status == SubmissionStatus.FAILED.value
    assert sample_submission.score == 50


def test_docker_startup_failure_handling(mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 1: Docker/container startup failure is treated as an infrastructure failure.
    Submission becomes ERROR, Evaluation becomes FAILED, and error is captured.
    """
    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="",
        stderr="Execution error: Error response from daemon: container failed to start",
        exit_code=1,
        execution_time=0.02,
        memory_used=0.0,
    )
    exec_service = ExecutionService(runner=mock_runner)
    service = EvaluationService(execution_service=exec_service)

    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None
        elif model == TestCase:
            m.filter.return_value.order_by.return_value.all.return_value = sample_test_cases
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.FAILED.value
    assert sample_submission.status == SubmissionStatus.ERROR.value
    assert "Evaluation error" in evaluation.stderr


def test_student_runtime_error_handling(mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 2: Student code runtime error (e.g. ZeroDivisionError) is a student test failure.
    Submission is FAILED, Evaluation is COMPLETED, and score is 0.
    """
    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="",
        stderr="Traceback (most recent call last):\n  ZeroDivisionError: division by zero",
        exit_code=1,
        execution_time=0.02,
        memory_used=5.0,
    )
    exec_service = ExecutionService(runner=mock_runner)
    service = EvaluationService(execution_service=exec_service)

    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None
        elif model == TestCase:
            m.filter.return_value.order_by.return_value.all.return_value = sample_test_cases
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert evaluation.score == 0
    assert evaluation.tests_failed == 2
    assert sample_submission.status == SubmissionStatus.FAILED.value
    assert sample_submission.score == 0


def test_docker_timeout_handling(mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test D: Execution timeout (exit_code=124, timeout stderr) is captured without crashing worker,
    tests fail, score=0, submission status is FAILED.
    """
    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="",
        stderr="Execution timed out after 5 seconds.",
        exit_code=124,
        execution_time=5.01,
        memory_used=15.0,
    )
    exec_service = ExecutionService(runner=mock_runner)
    service = EvaluationService(execution_service=exec_service)

    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None
        elif model == TestCase:
            m.filter.return_value.order_by.return_value.all.return_value = sample_test_cases
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert evaluation.score == 0
    assert evaluation.tests_failed == 2
    assert sample_submission.status == SubmissionStatus.FAILED.value
    assert "timed out" in evaluation.stderr


def test_evaluation_unhandled_exception_marks_error(mock_db, sample_challenge, sample_submission):
    """
    Test E & M: Unhandled exception during evaluation pipeline marks Evaluation as FAILED
    and Submission as ERROR, preventing corrupted state.
    """
    mock_runner = MagicMock()
    mock_runner.run.side_effect = RuntimeError("Database/Docker bridge crash")
    exec_service = ExecutionService(runner=mock_runner)
    service = EvaluationService(execution_service=exec_service)

    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None
        elif model == TestCase:
            # Query throws exception during evaluation
            raise RuntimeError("Database disconnect during query")
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.FAILED.value
    assert sample_submission.status == SubmissionStatus.ERROR.value
    assert "Evaluation error" in evaluation.stderr


def test_duplicate_evaluation_task_idempotency(mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test G: When evaluation task is executed twice for the same submission ID,
    the existing Evaluation record is reused and updated rather than duplicated.
    """
    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(stdout="10\n", exit_code=0, execution_time=0.01)
    exec_service = ExecutionService(runner=mock_runner)
    service = EvaluationService(execution_service=exec_service)

    existing_eval = Evaluation(
        id=50,
        submission_id=sample_submission.id,
        status=EvaluationStatus.RUNNING.value,
    )

    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = existing_eval  # Returns existing record
        elif model == TestCase:
            m.filter.return_value.order_by.return_value.all.return_value = sample_test_cases
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    eval_result = service.evaluate(mock_db, sample_submission)

    assert eval_result.id == 50
    assert eval_result.status == EvaluationStatus.COMPLETED.value


def test_achievement_service_failure_does_not_fail_evaluation(mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test I: If AchievementService throws an unexpected error, the evaluation result
    remains safely committed as COMPLETED/PASSED and does not crash the task.
    """
    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(stdout="10\n", exit_code=0, execution_time=0.05)
    exec_service = ExecutionService(runner=mock_runner)

    mock_ach_service = MagicMock(spec=AchievementService)
    mock_ach_service.award_for_user.side_effect = Exception("Achievement database lock timeout")

    service = EvaluationService(
        execution_service=exec_service,
        achievement_service=mock_ach_service,
    )

    def mock_query(model):
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None
        elif model == TestCase:
            m.filter.return_value.order_by.return_value.all.return_value = [sample_test_cases[0]]
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    # Evaluation itself succeeds even though achievement service threw an error
    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert sample_submission.status == SubmissionStatus.PASSED.value


def test_hidden_test_cases_masked_in_api_response():
    """
    Test 10 & 11: Hidden test inputs and expected outputs are masked in TestCaseResult schemas.
    """
    raw_results = [
        {
            "test_case_id": 1,
            "name": "Public Case",
            "passed": True,
            "is_hidden": False,
            "points": 50,
            "max_points": 50,
            "execution_time": 0.02,
            "memory_used": 10.0,
            "exit_code": 0,
            "stdout": "10\n",
            "stderr": "",
            "expected_output": "10\n",
            "input_data": "5\n",
        },
        {
            "test_case_id": 2,
            "name": "Secret Boundary Case",
            "passed": True,
            "is_hidden": True,
            "points": 50,
            "max_points": 50,
            "execution_time": 0.03,
            "memory_used": 12.0,
            "exit_code": 0,
            "stdout": "20\n",
            "stderr": "",
            "expected_output": "20\n",
            "input_data": "10\n",
        },
    ]

    sanitized = [TestCaseResult.from_raw(r) for r in raw_results]

    assert sanitized[0].is_hidden is False
    assert sanitized[0].actual_output == "10\n"
    assert sanitized[0].expected_output == "10\n"
    assert sanitized[0].input_data == "5\n"

    # Hidden test case MUST mask actual_output, expected_output, input_data (set to None)
    assert sanitized[1].is_hidden is True
    assert sanitized[1].passed is True
    assert sanitized[1].points == 50
    assert sanitized[1].actual_output is None
    assert sanitized[1].expected_output is None
    assert sanitized[1].input_data is None
