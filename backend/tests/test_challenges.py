import uuid
import pytest
from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.main import app
from app.models.challenge import Challenge, ChallengeFile, ChallengeType, Difficulty, TestCase
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.services.auth_service import create_access_token, hash_password


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


@pytest.fixture
def test_user(db_session):
    username = f"ch_user_{uuid.uuid4().hex[:6]}"
    user = User(
        username=username,
        email=f"{username}@example.com",
        password=hash_password("Pass123!"),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_challenge_list_unauthenticated(client: TestClient):
    res = client.get("/api/challenges/")
    assert res.status_code == 401


def test_challenge_list_and_filters(client: TestClient, test_user: User, db_session):
    token = create_access_token(test_user.id, test_user.role)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Normal List
    res = client.get("/api/challenges/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)

    # 2. Search filter
    search_res = client.get("/api/challenges/?search=calculator", headers=headers)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert isinstance(search_data["results"], list)

    # 3. Valid Difficulty filter
    diff_res = client.get("/api/challenges/?difficulty=BEGINNER", headers=headers)
    assert diff_res.status_code == 200

    # 4. Invalid Difficulty filter -> 400
    inv_diff_res = client.get("/api/challenges/?difficulty=INVALID_DIFF", headers=headers)
    assert inv_diff_res.status_code == 400
    assert "error" in inv_diff_res.json()

    # 5. Valid Challenge Type filter
    ct_res = client.get("/api/challenges/?challenge_type=BUG_FIX", headers=headers)
    assert ct_res.status_code == 200

    # 6. Invalid Challenge Type filter -> 400
    inv_ct_res = client.get("/api/challenges/?challenge_type=INVALID_TYPE", headers=headers)
    assert inv_ct_res.status_code == 400
    assert "error" in inv_ct_res.json()

    # 7. Programming language filter
    lang_res = client.get("/api/challenges/?programming_language=Python", headers=headers)
    assert lang_res.status_code == 200


def test_challenge_detail_and_hidden_test_protection(client: TestClient, test_user: User, db_session):
    token = create_access_token(test_user.id, test_user.role)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a test repository challenge
    slug = f"test-challenge-{uuid.uuid4().hex[:6]}"
    challenge = Challenge(
        title="Test Protection Challenge",
        slug=slug,
        description="Testing hidden files",
        difficulty=Difficulty.BEGINNER.value,
        challenge_type=ChallengeType.BUG_FIX.value,
        programming_language="Python",
        starter_code="def solve(): pass",
        points=100,
        is_active=True,
    )
    db_session.add(challenge)
    db_session.commit()
    db_session.refresh(challenge)

    # Add public file and hidden test file
    pub_file = ChallengeFile(
        challenge_id=challenge.id,
        path="src/main.py",
        content="print('public')",
        is_test=False,
        is_readonly=False,
    )
    test_file = ChallengeFile(
        challenge_id=challenge.id,
        path="tests/test_solution.py",
        content="SECRET_TEST_CASE_12345",
        is_test=True,
        is_readonly=True,
    )
    db_session.add_all([pub_file, test_file])
    db_session.commit()

    # Fetch detail
    detail_res = client.get(f"/api/challenges/{challenge.id}/", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == challenge.id
    assert detail_data["repository"] is not None

    files = detail_data["repository"]["files"]
    assert len(files) == 2

    # Verify public file content is exposed
    pub_f = next(f for f in files if f["path"] == "src/main.py")
    assert pub_f["content"] == "print('public')"
    assert pub_f["is_test"] is False

    # CRITICAL: Verify test file content is NEVER exposed (must be None)
    sec_f = next(f for f in files if f["path"] == "tests/test_solution.py")
    assert sec_f["is_test"] is True
    assert sec_f["content"] is None


def test_challenge_progress_endpoint(client: TestClient, test_user: User, db_session):
    token = create_access_token(test_user.id, test_user.role)
    headers = {"Authorization": f"Bearer {token}"}

    progress_res = client.get("/api/challenges/progress/", headers=headers)
    assert progress_res.status_code == 200
    data = progress_res.json()
    assert "summary" in data
    assert "total_challenges" in data["summary"]
    assert "completion_percentage" in data["summary"]
    assert "challenges" in data
    assert isinstance(data["challenges"], list)


def test_challenge_submission_history_ownership(client: TestClient, test_user: User, db_session):
    token = create_access_token(test_user.id, test_user.role)
    headers = {"Authorization": f"Bearer {token}"}

    # Other user
    other_user = User(
        username=f"other_{uuid.uuid4().hex[:6]}",
        email="other@example.com",
        password=hash_password("Pass123!"),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    # Get a challenge
    challenge = db_session.query(Challenge).first()
    if not challenge:
        challenge = Challenge(
            title="Dummy",
            slug="dummy-slug",
            description="desc",
            is_active=True,
        )
        db_session.add(challenge)
        db_session.commit()
        db_session.refresh(challenge)

    # Submission by current user
    sub_user = Submission(
        user_id=test_user.id,
        challenge_id=challenge.id,
        code="print('user sub')",
        status=SubmissionStatus.PASSED.value,
        score=100,
    )
    # Submission by other user
    sub_other = Submission(
        user_id=other_user.id,
        challenge_id=challenge.id,
        code="print('other sub')",
        status=SubmissionStatus.PASSED.value,
        score=100,
    )
    db_session.add_all([sub_user, sub_other])
    db_session.commit()

    # Query submission history for current user
    history_res = client.get(f"/api/challenges/{challenge.id}/submissions/", headers=headers)
    assert history_res.status_code == 200
    history_data = history_res.json()

    # Must only contain test_user's submissions
    sub_ids = [s["id"] for s in history_data["results"]]
    assert sub_user.id in sub_ids
    assert sub_other.id not in sub_ids
