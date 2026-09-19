import pytest
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    Achievement,
    Challenge,
    ChallengeFile,
    ChallengeType,
    Difficulty,
    Evaluation,
    EvaluationStatus,
    RequirementType,
    Submission,
    SubmissionStatus,
    TestCase,
    User,
    UserAchievement,
    UserRole,
)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_models_import_and_metadata():
    assert User.__tablename__ == "users_user"
    assert Challenge.__tablename__ == "challenges_challenge"
    assert TestCase.__tablename__ == "challenges_testcase"
    assert ChallengeFile.__tablename__ == "challenges_challengefile"
    assert Submission.__tablename__ == "submissions_submission"
    assert Evaluation.__tablename__ == "evaluations_evaluation"
    assert Achievement.__tablename__ == "evaluations_achievement"
    assert UserAchievement.__tablename__ == "evaluations_userachievement"


def test_query_existing_database_models(db_session: Session):
    # Verify we can query all tables cleanly
    users = db_session.query(User).all()
    assert isinstance(users, list)

    challenges = db_session.query(Challenge).all()
    assert isinstance(challenges, list)

    test_cases = db_session.query(TestCase).all()
    assert isinstance(test_cases, list)

    challenge_files = db_session.query(ChallengeFile).all()
    assert isinstance(challenge_files, list)

    submissions = db_session.query(Submission).all()
    assert isinstance(submissions, list)

    evaluations = db_session.query(Evaluation).all()
    assert isinstance(evaluations, list)

    achievements = db_session.query(Achievement).all()
    assert isinstance(achievements, list)


def test_relationships_and_foreign_keys(db_session: Session):
    # Check relationships on challenges
    challenge = db_session.query(Challenge).first()
    if challenge:
        assert isinstance(challenge.test_cases, list)
        assert isinstance(challenge.files, list)
        assert isinstance(challenge.submissions, list)

    # Check relationships on submissions
    submission = db_session.query(Submission).first()
    if submission:
        assert submission.user is not None
        assert submission.challenge is not None
        if submission.evaluation:
            assert submission.evaluation.submission_id == submission.id


def test_enums_integrity():
    assert UserRole.STUDENT == "STUDENT"
    assert Difficulty.BEGINNER == "BEGINNER"
    assert ChallengeType.BUG_FIX == "BUG_FIX"
    assert SubmissionStatus.PENDING == "PENDING"
    assert EvaluationStatus.COMPLETED == "COMPLETED"
    assert RequirementType.BUG_FIX_COUNT == "BUG_FIX_COUNT"
