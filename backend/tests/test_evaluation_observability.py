"""
Unit & Regression Test Suite for CF-027: Evaluation Observability & Operational Diagnostics.

Verifies:
1. Evaluation start, completion, and failure structured logging with correlation fields.
2. Error classification consistency:
   - Student test/runtime failure -> FAILED / COMPLETED
   - Execution timeout -> FAILED / COMPLETED
   - Docker infrastructure failure -> ERROR / FAILED
   - Generic unhandled exception -> ERROR / FAILED
3. Achievement post-processing exception isolation.
4. API-safe error visibility (hidden test data masking).
5. Safe diagnostics without leaking raw secrets or hidden test inputs to logs.
"""

from datetime import datetime, timezone
import logging
from unittest.mock import MagicMock
import pytest
from sqlalchemy.orm import Session

from app.execution.runner import ExecutionResult
from app.execution.services import ExecutionService
from app.models.challenge import Challenge, ChallengeFile, ChallengeType, Difficulty, TestCase
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SubmissionStatus
from app.schemas.submission import TestCaseResult
from app.services.achievement_service import AchievementService
from app.services.evaluation_service import EvaluationService


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def sample_challenge() -> Challenge:
    return Challenge(
        id=42,
        title="Observability Challenge",
        slug="observability-challenge",
        challenge_type=ChallengeType.PERFORMANCE.value,
        difficulty=Difficulty.INTERMEDIATE.value,
        is_active=True,
        points=100,
        programming_language="python",
    )


@pytest.fixture
def sample_test_cases(sample_challenge) -> list:
    return [
        TestCase(
            id=101,
            challenge_id=sample_challenge.id,
            name="Public Test Case",
            input_data="input_data_1\n",
            expected_output="output_data_1\n",
            points=50,
            is_hidden=False,
            is_active=True,
        ),
        TestCase(
            id=102,
            challenge_id=sample_challenge.id,
            name="Secret Hidden Test Case",
            input_data="SECRET_INPUT\n",
            expected_output="SECRET_EXPECTED_OUTPUT\n",
            points=50,
            is_hidden=True,
            is_active=True,
        ),
    ]


@pytest.fixture
def sample_submission(sample_challenge) -> Submission:
    sub = Submission(
        id=999,
        user_id=77,
        challenge_id=sample_challenge.id,
        status=SubmissionStatus.PENDING.value,
        code="def solve(): return 42",
        language="Python",
        score=0,
        submitted_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    sub.challenge = sample_challenge
    return sub


# ---------------------------------------------------------------------------
# Observability & Diagnostics Tests
# ---------------------------------------------------------------------------

def test_evaluation_lifecycle_logging_and_correlation(caplog, mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 1: Start and completion of evaluation produce correlated log records containing
    submission_id, evaluation_id, challenge_id, and user_id.
    """
    caplog.set_level(logging.INFO)

    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="output_data_1\n",
        stderr="",
        exit_code=0,
        execution_time=0.08,
        memory_used=14.2,
    )
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
            m.filter.return_value.order_by.return_value.all.return_value = [sample_test_cases[0]]
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert sample_submission.status == SubmissionStatus.PASSED.value

    # Verify correlated log records
    log_messages = [rec.message for rec in caplog.records]
    
    start_logs = [msg for msg in log_messages if "Evaluation started:" in msg]
    assert len(start_logs) >= 1
    assert "submission_id=999" in start_logs[0]
    assert "challenge_id=42" in start_logs[0]
    assert "user_id=77" in start_logs[0]

    complete_logs = [msg for msg in log_messages if "Evaluation completed:" in msg]
    assert len(complete_logs) >= 1
    assert "submission_id=999" in complete_logs[0]
    assert "submission_status=PASSED" in complete_logs[0]
    assert "evaluation_status=COMPLETED" in complete_logs[0]


def test_student_failure_classification_and_logging(caplog, mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 2: Student wrong output is classified as student failure (FAILED / COMPLETED).
    """
    caplog.set_level(logging.INFO)

    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="incorrect_output\n",
        stderr="",
        exit_code=0,
        execution_time=0.04,
        memory_used=8.0,
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
            m.filter.return_value.order_by.return_value.all.return_value = [sample_test_cases[0]]
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert sample_submission.status == SubmissionStatus.FAILED.value
    assert evaluation.score == 0

    complete_logs = [rec.message for rec in caplog.records if "Evaluation completed:" in rec.message]
    assert len(complete_logs) >= 1
    assert "submission_status=FAILED" in complete_logs[0]
    assert "evaluation_status=COMPLETED" in complete_logs[0]


def test_docker_infrastructure_failure_observability(caplog, mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 3: Docker startup failure is classified as infrastructure failure (ERROR / FAILED)
    and logged at ERROR level with diagnostic context.
    """
    caplog.set_level(logging.ERROR)

    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="",
        stderr="Execution error: Docker daemon unreachable or socket permission denied",
        exit_code=1,
        execution_time=0.01,
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
            m.filter.return_value.order_by.return_value.all.return_value = [sample_test_cases[0]]
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.FAILED.value
    assert sample_submission.status == SubmissionStatus.ERROR.value
    assert "Execution error:" in evaluation.stderr

    error_logs = [rec.message for rec in caplog.records if "Evaluation infrastructure/pipeline failure:" in rec.message]
    assert len(error_logs) >= 1
    assert "submission_id=999" in error_logs[0]
    assert "Docker daemon unreachable" in error_logs[0]


def test_execution_timeout_diagnostics(caplog, mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 4: Execution timeout is classified as student execution timeout (FAILED / COMPLETED).
    """
    caplog.set_level(logging.INFO)

    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        stdout="",
        stderr="Execution timed out after 5.0 seconds.",
        exit_code=124,
        execution_time=5.0,
        memory_used=16.0,
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
            m.filter.return_value.order_by.return_value.all.return_value = [sample_test_cases[0]]
        elif model == ChallengeFile:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert sample_submission.status == SubmissionStatus.FAILED.value
    assert evaluation.score == 0
    assert "timed out" in evaluation.stderr.lower()


def test_unexpected_exception_diagnostics(caplog, mock_db, sample_challenge, sample_submission):
    """
    Test 5: Unexpected database or evaluation pipeline exception produces ERROR/FAILED
    and logs full context.
    """
    caplog.set_level(logging.ERROR)

    service = EvaluationService()

    def mock_query(model):
        if model == TestCase:
            raise ConnectionResetError("PostgreSQL server closed connection unexpectedly")
        m = MagicMock()
        if model == Submission:
            m.options.return_value.filter.return_value.first.return_value = sample_submission
        elif model == Evaluation:
            m.filter.return_value.first.return_value = None
        return m

    mock_db.query.side_effect = mock_query

    evaluation = service.evaluate(mock_db, sample_submission)

    assert evaluation.status == EvaluationStatus.FAILED.value
    assert sample_submission.status == SubmissionStatus.ERROR.value

    error_logs = [rec.message for rec in caplog.records if "Evaluation infrastructure/pipeline failure:" in rec.message]
    assert len(error_logs) >= 1
    assert "submission_id=999" in error_logs[0]
    assert "PostgreSQL server closed connection" in error_logs[0]


def test_achievement_failure_isolation_and_logging(caplog, mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 6: Failure during achievement post-processing is logged as an error
    without corrupting or rolling back the completed evaluation.
    """
    caplog.set_level(logging.ERROR)

    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(stdout="output_data_1\n", exit_code=0)
    exec_service = ExecutionService(runner=mock_runner)

    mock_ach_service = MagicMock(spec=AchievementService)
    mock_ach_service.award_for_user.side_effect = TimeoutError("Redis badge cache timed out")

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

    assert evaluation.status == EvaluationStatus.COMPLETED.value
    assert sample_submission.status == SubmissionStatus.PASSED.value

    ach_error_logs = [rec.message for rec in caplog.records if "Error during automatic achievement evaluation:" in rec.message]
    assert len(ach_error_logs) >= 1


def test_hidden_test_data_masked_in_api_response(sample_test_cases):
    """
    Test 7: Hidden test case inputs and expected outputs are never returned to client APIs.
    """
    raw_results = [
        {
            "test_case_id": sample_test_cases[0].id,
            "name": sample_test_cases[0].name,
            "passed": True,
            "is_hidden": False,
            "points": 50,
            "max_points": 50,
            "execution_time": 0.02,
            "stdout": "output_data_1\n",
            "expected_output": "output_data_1\n",
            "input_data": "input_data_1\n",
        },
        {
            "test_case_id": sample_test_cases[1].id,
            "name": sample_test_cases[1].name,
            "passed": True,
            "is_hidden": True,
            "points": 50,
            "max_points": 50,
            "execution_time": 0.03,
            "stdout": "SECRET_EXPECTED_OUTPUT\n",
            "expected_output": "SECRET_EXPECTED_OUTPUT\n",
            "input_data": "SECRET_INPUT\n",
        },
    ]

    sanitized = [TestCaseResult.from_raw(r) for r in raw_results]

    # Public case preserves outputs
    assert sanitized[0].is_hidden is False
    assert sanitized[0].actual_output == "output_data_1\n"
    assert sanitized[0].expected_output == "output_data_1\n"
    assert sanitized[0].input_data == "input_data_1\n"

    # Hidden case MUST be masked (None)
    assert sanitized[1].is_hidden is True
    assert sanitized[1].actual_output is None
    assert sanitized[1].expected_output is None
    assert sanitized[1].input_data is None


def test_logs_do_not_expose_hidden_test_inputs(caplog, mock_db, sample_challenge, sample_test_cases, sample_submission):
    """
    Test 8: System evaluation logs do not dump hidden test input or secret output payloads.
    """
    caplog.set_level(logging.INFO)

    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(stdout="SECRET_EXPECTED_OUTPUT\n", exit_code=0)
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

    service.evaluate(mock_db, sample_submission)

    full_log_text = " ".join(rec.message for rec in caplog.records)
    assert "SECRET_INPUT" not in full_log_text
    assert "SECRET_EXPECTED_OUTPUT" not in full_log_text
