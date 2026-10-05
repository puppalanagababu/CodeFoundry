"""
Unit & Regression Test Suite for CF-025: Achievement & Progress Integrity.

Verifies:
1. Canonical best-attempt aggregation for achievements.
2. Idempotent achievement awarding without duplicate UserAchievement records.
3. Anti-gaming deduplication (repeated submissions do not multiply completion counts or perfect runs).
4. ProgressService metric integrity (attempt count vs distinct completed challenges).
5. Inactive challenge filtering.
6. Score improvement and regression resistance.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from unittest.mock import MagicMock
import pytest
from sqlalchemy.orm import Session

from app.models.challenge import Challenge, ChallengeType, Difficulty
from app.models.evaluation import (
    Achievement,
    Evaluation,
    EvaluationStatus,
    RequirementType,
    UserAchievement,
)
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.achievement_service import AchievementService, SEED_ACHIEVEMENTS
from app.services.progress_service import ChallengeProgressService


# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------

def make_challenge(
    cid: int,
    title: str = "Test Challenge",
    challenge_type: str = ChallengeType.BUG_FIX.value,
    difficulty: str = Difficulty.BEGINNER.value,
    is_active: bool = True,
    points: int = 100,
) -> Challenge:
    return Challenge(
        id=cid,
        title=title,
        slug=f"challenge-{cid}",
        challenge_type=challenge_type,
        difficulty=difficulty,
        is_active=is_active,
        points=points,
        programming_language="python",
    )


def make_submission(
    sid: int,
    user_id: int,
    challenge: Challenge,
    status: str = SubmissionStatus.PASSED.value,
    score: int = 100,
    submitted_at: Optional[datetime] = None,
) -> Submission:
    sub = Submission(
        id=sid,
        user_id=user_id,
        challenge_id=challenge.id,
        status=status,
        score=score,
        language="python",
        code="def solve(): pass",
        submitted_at=submitted_at or datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    sub.challenge = challenge
    return sub


def make_evaluation(
    eid: int,
    submission: Submission,
    status: str = EvaluationStatus.COMPLETED.value,
    evaluated_at: Optional[datetime] = None,
) -> Evaluation:
    ev = Evaluation(
        id=eid,
        submission_id=submission.id,
        status=status,
        score=submission.score,
        evaluated_at=evaluated_at or submission.submitted_at,
    )
    ev.submission = submission
    return ev


@pytest.fixture
def achievement_service() -> AchievementService:
    return AchievementService()


@pytest.fixture
def progress_service() -> ChallengeProgressService:
    return ChallengeProgressService()


@pytest.fixture
def standard_achievements() -> List[Achievement]:
    achievements = []
    for idx, data in enumerate(SEED_ACHIEVEMENTS, start=1):
        ach = Achievement(
            id=idx,
            code=data["code"],
            name=data["name"],
            description=data["description"],
            icon=data["icon"],
            requirement_type=data["requirement_type"],
            requirement_value=data["requirement_value"],
            is_active=True,
        )
        achievements.append(ach)
    return achievements


# ---------------------------------------------------------------------------
# Achievement Tests
# ---------------------------------------------------------------------------

def test_achievement_awarding_idempotency(achievement_service, standard_achievements):
    """
    Test 8.A & 8.J: Processing evaluation/awards repeatedly produces identical results
    and does not duplicate UserAchievement records.
    """
    mock_db = MagicMock(spec=Session)

    # User completed 3 bug fix challenges (satisfies BUG_SLAYER)
    ch1 = make_challenge(1, challenge_type=ChallengeType.BUG_FIX.value)
    ch2 = make_challenge(2, challenge_type=ChallengeType.BUG_FIX.value)
    ch3 = make_challenge(3, challenge_type=ChallengeType.BUG_FIX.value)

    sub1 = make_submission(1, 1, ch1, SubmissionStatus.PASSED.value, 100)
    sub2 = make_submission(2, 1, ch2, SubmissionStatus.PASSED.value, 100)
    sub3 = make_submission(3, 1, ch3, SubmissionStatus.PASSED.value, 100)

    e1 = make_evaluation(1, sub1)
    e2 = make_evaluation(2, sub2)
    e3 = make_evaluation(3, sub3)
    evals = [e1, e2, e3]

    # First call: no existing user achievements
    def mock_query_first(model):
        m = MagicMock()
        if model == Achievement:
            m.filter.return_value.all.return_value = standard_achievements
        elif model == Evaluation:
            m.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals
        elif model == UserAchievement:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query_first
    awarded_first = achievement_service.award_for_user(mock_db, user_id=1)
    
    # Expect BUG_SLAYER to be awarded (3 bug fixes >= 3)
    bug_slayer_achs = [a for a in awarded_first if getattr(a, "achievement_id", None) == 1 or (hasattr(a, "achievement") and a.achievement.code == "BUG_SLAYER")]
    assert len(bug_slayer_achs) == 1

    # Second call: simulated existing user achievements in database
    existing_ua = UserAchievement(id=101, user_id=1, achievement_id=1)
    existing_ua.achievement = standard_achievements[0]

    def mock_query_second(model):
        m = MagicMock()
        if model == Achievement:
            m.filter.return_value.all.return_value = standard_achievements
        elif model == Evaluation:
            m.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals
        elif model == UserAchievement:
            m.filter.return_value.all.return_value = [existing_ua]
        return m

    mock_db.query.side_effect = mock_query_second
    awarded_second = achievement_service.award_for_user(mock_db, user_id=1)

    # Should return existing record, not add a duplicate
    assert len(awarded_second) == 1
    assert awarded_second[0].id == 101


def test_achievement_anti_gaming_repeated_submissions(achievement_service, standard_achievements):
    """
    Test 8.C & 12: Submitting the same challenge 5 times must count as ONE challenge completion,
    NOT 5 distinct completions.
    """
    mock_db = MagicMock(spec=Session)

    ch1 = make_challenge(1, challenge_type=ChallengeType.BUG_FIX.value)

    # 5 passed submissions for the SAME challenge
    evals = []
    for i in range(1, 6):
        sub = make_submission(i, 1, ch1, SubmissionStatus.PASSED.value, 100, datetime(2026, 1, i, tzinfo=timezone.utc))
        ev = make_evaluation(i, sub)
        evals.append(ev)

    def mock_query(model):
        m = MagicMock()
        if model == Achievement:
            m.filter.return_value.all.return_value = standard_achievements
        elif model == Evaluation:
            # Query returns in descending score/date order
            m.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = list(reversed(evals))
        elif model == UserAchievement:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query
    awarded = achievement_service.award_for_user(mock_db, user_id=1)

    # BUG_SLAYER requires 3 distinct challenges; PERFECT_RUN requires 5 distinct; DEVFORGE_VETERAN requires 10.
    # None should be earned with only 1 distinct challenge completed.
    assert len(awarded) == 0


def test_achievement_best_attempt_improves(achievement_service, standard_achievements):
    """
    Test 8.D & 8.E: Best attempt score improvement enables perfect score eligibility.
    Lower subsequent attempts do not regress best attempt.
    """
    mock_db = MagicMock(spec=Session)

    # Create 5 distinct challenges
    challenges = [make_challenge(i, f"Challenge {i}", challenge_type=ChallengeType.PERFORMANCE.value) for i in range(1, 6)]

    # 4 challenges have perfect scores 100; Challenge 5 has an initial attempt of 60
    evals = []
    for i in range(1, 5):
        sub = make_submission(i, 1, challenges[i - 1], SubmissionStatus.PASSED.value, 100)
        evals.append(make_evaluation(i, sub))

    # Challenge 5 attempt 1: score 60
    sub5_1 = make_submission(5, 1, challenges[4], SubmissionStatus.PASSED.value, 60, datetime(2026, 1, 1, tzinfo=timezone.utc))
    ev5_1 = make_evaluation(5, sub5_1)
    evals.append(ev5_1)

    def mock_query_initial(model):
        m = MagicMock()
        if model == Achievement:
            m.filter.return_value.all.return_value = standard_achievements
        elif model == Evaluation:
            m.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals
        elif model == UserAchievement:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query_initial
    awarded_initial = achievement_service.award_for_user(mock_db, user_id=1)
    # PERFECT_RUN (5 perfect scores) is NOT earned yet (only 4 are 100)
    perfect_run_earned = any(getattr(a, "achievement_id", None) == 5 for a in awarded_initial)
    assert not perfect_run_earned

    # Challenge 5 attempt 2: improved to 100!
    sub5_2 = make_submission(6, 1, challenges[4], SubmissionStatus.PASSED.value, 100, datetime(2026, 1, 2, tzinfo=timezone.utc))
    ev5_2 = make_evaluation(6, sub5_2)

    # Challenge 5 attempt 3: lower attempt of 70 afterwards
    sub5_3 = make_submission(7, 1, challenges[4], SubmissionStatus.PASSED.value, 70, datetime(2026, 1, 3, tzinfo=timezone.utc))
    ev5_3 = make_evaluation(7, sub5_3)

    all_evals = evals[:4] + [ev5_2, ev5_3, ev5_1]  # Ordered by score desc

    def mock_query_improved(model):
        m = MagicMock()
        if model == Achievement:
            m.filter.return_value.all.return_value = standard_achievements
        elif model == Evaluation:
            m.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = all_evals
        elif model == UserAchievement:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query_improved
    awarded_improved = achievement_service.award_for_user(mock_db, user_id=1)
    # PERFECT_RUN (achievement_id=5) and PERFORMANCE_ENGINEER (achievement_id=3) should be awarded
    awarded_ids = {a.achievement_id for a in awarded_improved}
    assert 5 in awarded_ids  # PERFECT_RUN earned
    assert 3 in awarded_ids  # PERFORMANCE_ENGINEER earned (>=3 performance challenges passed)


def test_achievement_inactive_challenge_excluded(achievement_service, standard_achievements):
    """
    Test 8.F: Submissions to inactive challenges must not count toward active achievement progress.
    """
    mock_db = MagicMock(spec=Session)

    # 3 bug fix challenges, but 1 is inactive
    ch1 = make_challenge(1, challenge_type=ChallengeType.BUG_FIX.value, is_active=True)
    ch2 = make_challenge(2, challenge_type=ChallengeType.BUG_FIX.value, is_active=True)
    ch3 = make_challenge(3, challenge_type=ChallengeType.BUG_FIX.value, is_active=False)

    sub1 = make_submission(1, 1, ch1, SubmissionStatus.PASSED.value, 100)
    sub2 = make_submission(2, 1, ch2, SubmissionStatus.PASSED.value, 100)
    sub3 = make_submission(3, 1, ch3, SubmissionStatus.PASSED.value, 100)

    # DB query filter `Challenge.is_active == True` excludes ch3
    active_evals = [make_evaluation(1, sub1), make_evaluation(2, sub2)]

    def mock_query(model):
        m = MagicMock()
        if model == Achievement:
            m.filter.return_value.all.return_value = standard_achievements
        elif model == Evaluation:
            m.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = active_evals
        elif model == UserAchievement:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query
    awarded = achievement_service.award_for_user(mock_db, user_id=1)

    # BUG_SLAYER requires 3, but only 2 active challenges were passed
    assert len(awarded) == 0


def test_achievement_multiple_milestones_awarded_together(achievement_service, standard_achievements):
    """
    Test 8.I: Multiple satisfied milestones (e.g. Total Completed + Security Hunter + Perfect Run)
    are all correctly awarded in a single evaluation run.
    """
    mock_db = MagicMock(spec=Session)

    # Create 10 distinct security challenges all passed with 100
    evals = []
    for i in range(1, 11):
        ch = make_challenge(i, f"Sec Challenge {i}", challenge_type=ChallengeType.SECURITY.value)
        sub = make_submission(i, 1, ch, SubmissionStatus.PASSED.value, 100)
        evals.append(make_evaluation(i, sub))

    def mock_query(model):
        m = MagicMock()
        if model == Achievement:
            m.filter.return_value.all.return_value = standard_achievements
        elif model == Evaluation:
            m.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals
        elif model == UserAchievement:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query
    awarded = achievement_service.award_for_user(mock_db, user_id=1)

    awarded_codes = {standard_achievements[a.achievement_id - 1].code for a in awarded}
    assert "SECURITY_HUNTER" in awarded_codes  # >= 3 security
    assert "PERFECT_RUN" in awarded_codes      # >= 5 perfect
    assert "DEVFORGE_VETERAN" in awarded_codes  # >= 10 total


# ---------------------------------------------------------------------------
# Progress Tests
# ---------------------------------------------------------------------------

def test_progress_zero_submissions(progress_service):
    """
    Test 9: User with no submissions has 0 completed, 0 attempted, 0.0% completion.
    """
    mock_db = MagicMock(spec=Session)
    user = User(id=1, username="newbie", is_active=True)

    challenges = [make_challenge(i, f"Challenge {i}") for i in range(1, 6)]

    def mock_query(model):
        m = MagicMock()
        if model == Challenge:
            m.filter.return_value.order_by.return_value.all.return_value = challenges
        elif model == Submission:
            m.join.return_value.filter.return_value.order_by.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query
    res = progress_service.get_user_progress(user, mock_db)

    assert res["summary"]["total_challenges"] == 5
    assert res["summary"]["attempted_challenges"] == 0
    assert res["summary"]["completed_challenges"] == 0
    assert res["summary"]["completion_percentage"] == 0.0

    for ch_item in res["challenges"]:
        assert ch_item["status"] == "NOT_ATTEMPTED"
        assert ch_item["best_score"] is None
        assert ch_item["attempts_count"] == 0


def test_progress_repeated_submissions_do_not_inflate_completed_count(progress_service):
    """
    Test 9 & 12: 5 submissions to challenge 1 (PASSED) and 3 submissions to challenge 2 (FAILED).
    Total active = 4.
    Completed should be 1, attempted should be 2, completion percentage = 25.0%.
    """
    mock_db = MagicMock(spec=Session)
    user = User(id=1, username="coder", is_active=True)

    ch1 = make_challenge(1, "Challenge 1")
    ch2 = make_challenge(2, "Challenge 2")
    ch3 = make_challenge(3, "Challenge 3")
    ch4 = make_challenge(4, "Challenge 4")
    challenges = [ch1, ch2, ch3, ch4]

    subs = [
        # 5 submissions to Challenge 1
        make_submission(1, 1, ch1, SubmissionStatus.PASSED.value, 100, datetime(2026, 1, 5, tzinfo=timezone.utc)),
        make_submission(2, 1, ch1, SubmissionStatus.PASSED.value, 90, datetime(2026, 1, 4, tzinfo=timezone.utc)),
        make_submission(3, 1, ch1, SubmissionStatus.FAILED.value, 40, datetime(2026, 1, 3, tzinfo=timezone.utc)),
        make_submission(4, 1, ch1, SubmissionStatus.FAILED.value, 50, datetime(2026, 1, 2, tzinfo=timezone.utc)),
        make_submission(5, 1, ch1, SubmissionStatus.FAILED.value, 30, datetime(2026, 1, 1, tzinfo=timezone.utc)),
        # 3 submissions to Challenge 2 (all failed)
        make_submission(6, 1, ch2, SubmissionStatus.FAILED.value, 50, datetime(2026, 1, 3, tzinfo=timezone.utc)),
        make_submission(7, 1, ch2, SubmissionStatus.FAILED.value, 40, datetime(2026, 1, 2, tzinfo=timezone.utc)),
        make_submission(8, 1, ch2, SubmissionStatus.FAILED.value, 20, datetime(2026, 1, 1, tzinfo=timezone.utc)),
    ]

    def mock_query(model):
        m = MagicMock()
        if model == Challenge:
            m.filter.return_value.order_by.return_value.all.return_value = challenges
        elif model == Submission:
            m.join.return_value.filter.return_value.order_by.return_value.all.return_value = subs
        return m

    mock_db.query.side_effect = mock_query
    res = progress_service.get_user_progress(user, mock_db)

    assert res["summary"]["total_challenges"] == 4
    assert res["summary"]["attempted_challenges"] == 2
    assert res["summary"]["completed_challenges"] == 1
    assert res["summary"]["completion_percentage"] == 25.0

    # Inspect Challenge 1 details
    ch1_detail = next(c for c in res["challenges"] if c["challenge_id"] == 1)
    assert ch1_detail["status"] == "PASSED"
    assert ch1_detail["attempts_count"] == 5
    assert ch1_detail["best_score"] == 100

    # Inspect Challenge 2 details
    ch2_detail = next(c for c in res["challenges"] if c["challenge_id"] == 2)
    assert ch2_detail["status"] == "FAILED"
    assert ch2_detail["attempts_count"] == 3
    assert ch2_detail["best_score"] == 50

    # Inspect Challenge 3 details
    ch3_detail = next(c for c in res["challenges"] if c["challenge_id"] == 3)
    assert ch3_detail["status"] == "NOT_ATTEMPTED"
    assert ch3_detail["attempts_count"] == 0
    assert ch3_detail["best_score"] is None


def test_progress_all_active_challenges_completed(progress_service):
    """
    Test 9: When all active challenges are passed, completion_percentage is 100.0%.
    """
    mock_db = MagicMock(spec=Session)
    user = User(id=1, username="champion", is_active=True)

    ch1 = make_challenge(1, "Challenge 1")
    ch2 = make_challenge(2, "Challenge 2")
    challenges = [ch1, ch2]

    subs = [
        make_submission(1, 1, ch1, SubmissionStatus.PASSED.value, 100),
        make_submission(2, 1, ch2, SubmissionStatus.PASSED.value, 95),
    ]

    def mock_query(model):
        m = MagicMock()
        if model == Challenge:
            m.filter.return_value.order_by.return_value.all.return_value = challenges
        elif model == Submission:
            m.join.return_value.filter.return_value.order_by.return_value.all.return_value = subs
        return m

    mock_db.query.side_effect = mock_query
    res = progress_service.get_user_progress(user, mock_db)

    assert res["summary"]["total_challenges"] == 2
    assert res["summary"]["attempted_challenges"] == 2
    assert res["summary"]["completed_challenges"] == 2
    assert res["summary"]["completion_percentage"] == 100.0


def test_progress_inactive_challenges_not_counted_in_total(progress_service):
    """
    Test 9: Inactive challenges are filtered out of total_challenges and progress calculations.
    """
    mock_db = MagicMock(spec=Session)
    user = User(id=1, username="dev", is_active=True)

    # 3 active challenges in DB query
    active_challenges = [make_challenge(1, "Active 1"), make_challenge(2, "Active 2"), make_challenge(3, "Active 3")]
    subs = [make_submission(1, 1, active_challenges[0], SubmissionStatus.PASSED.value, 100)]

    def mock_query(model):
        m = MagicMock()
        if model == Challenge:
            # Query filters Challenge.is_active == True
            m.filter.return_value.order_by.return_value.all.return_value = active_challenges
        elif model == Submission:
            m.join.return_value.filter.return_value.order_by.return_value.all.return_value = subs
        return m

    mock_db.query.side_effect = mock_query
    res = progress_service.get_user_progress(user, mock_db)

    assert res["summary"]["total_challenges"] == 3
    assert res["summary"]["completed_challenges"] == 1
    assert res["summary"]["completion_percentage"] == 33.3
