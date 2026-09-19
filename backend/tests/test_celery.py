import uuid
import pytest
from app.celery_app import celery_app
from app.database import SessionLocal, get_db_context
from app.models.challenge import Challenge, Difficulty, ChallengeType
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.services.auth_service import hash_password
from app.tasks.evaluation_tasks import evaluate_submission


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_celery_app_configuration():
    assert celery_app.main == "codefoundry_fastapi"
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.task_serializer == "json"
    assert "evaluate_submission" in celery_app.tasks


def test_db_context_manager():
    with get_db_context() as db:
        user_count = db.query(User).count()
        assert isinstance(user_count, int)
    # Session is closed after with-block


def test_evaluate_submission_task_nonexistent(db_session):
    # Running task directly with nonexistent ID
    result = evaluate_submission.apply(args=[999999]).get()
    assert "error" in result
    assert result["submission_id"] == 999999


def test_evaluate_submission_task_valid(db_session):
    # Setup test user and challenge
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"celery_user_{unique_suffix}",
        email=f"celery_{unique_suffix}@example.com",
        password=hash_password("Pass123!"),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    challenge = Challenge(
        title=f"Celery Challenge {unique_suffix}",
        slug=f"celery-slug-{unique_suffix}",
        description="Testing celery execution",
        difficulty=Difficulty.BEGINNER.value,
        challenge_type=ChallengeType.BUG_FIX.value,
        programming_language="Python",
        points=100,
        is_active=True,
    )
    db_session.add_all([user, challenge])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(challenge)

    # Create submission
    submission = Submission(
        user_id=user.id,
        challenge_id=challenge.id,
        code="print('Hello from Celery!')",
        status=SubmissionStatus.PENDING.value,
        score=0,
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    # Execute task using Celery .apply (eager / local runner)
    async_res = evaluate_submission.apply(args=[submission.id])
    res_data = async_res.get()

    assert async_res.status == "SUCCESS"
    assert res_data["submission_id"] == submission.id
    assert res_data["status"] == SubmissionStatus.FAILED.value
    assert res_data["evaluation_id"] is not None

    # Verify DB state updated via SQLAlchemy
    with get_db_context() as db:
        sub_in_db = db.query(Submission).filter(Submission.id == submission.id).first()
        assert sub_in_db.status == SubmissionStatus.FAILED.value
        eval_in_db = db.query(Evaluation).filter(Evaluation.submission_id == submission.id).first()
        assert eval_in_db is not None
        assert eval_in_db.status == EvaluationStatus.FAILED.value
