import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from app.models.challenge import Challenge, ChallengeType, Difficulty
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.skill_profile_service import (
    DIFFICULTY_WEIGHTS,
    DEFAULT_DIFFICULTY_WEIGHT,
    SkillProfileService,
    get_difficulty_weight,
)
from app.services.leaderboard_service import LeaderboardService
from app.services.profile_service import PublicProfileService
from app.services.recruiter_service import RecruiterDashboardService


@pytest.fixture
def skill_profile_service():
    return SkillProfileService()


@pytest.fixture
def leaderboard_service(skill_profile_service):
    return LeaderboardService(skill_profile_service=skill_profile_service)


@pytest.fixture
def public_profile_service(skill_profile_service):
    return PublicProfileService(skill_profile_service=skill_profile_service)


@pytest.fixture
def recruiter_service(skill_profile_service):
    return RecruiterDashboardService(skill_profile_service=skill_profile_service)


def build_evaluation(
    eval_id: int,
    user_id: int,
    challenge_id: int,
    difficulty: str,
    submission_score: int,
    scores_dict: dict,
    evaluated_at: datetime = None,
) -> Evaluation:
    challenge = Challenge(
        id=challenge_id,
        title=f"Challenge {challenge_id}",
        slug=f"challenge-{challenge_id}",
        difficulty=difficulty,
        challenge_type="BUG_FIX",
        is_active=True,
    )
    user = User(id=user_id, username=f"user_{user_id}", email=f"user_{user_id}@example.com", is_active=True)
    submission = Submission(
        id=eval_id * 100,
        user_id=user_id,
        user=user,
        challenge_id=challenge_id,
        challenge=challenge,
        score=submission_score,
        status="PASSED" if submission_score >= 70 else "FAILED",
    )
    return Evaluation(
        id=eval_id,
        submission_id=submission.id,
        submission=submission,
        status=EvaluationStatus.COMPLETED.value,
        skill_breakdown={"scores": scores_dict},
        evaluated_at=evaluated_at or datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


# A. Multiple Submissions to Same Challenge (Best Attempt Selection)
def test_best_attempt_selection_highest_score_wins(skill_profile_service):
    mock_db = MagicMock()
    # Submission 1: Score 50, PS=50
    # Submission 2: Score 100, PS=100 (Best)
    # Submission 3 (later): Score 60, PS=60
    e1 = build_evaluation(1, 1, 1, "MEDIUM", 50, {"problem_solving": 50}, evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    e2 = build_evaluation(2, 1, 1, "MEDIUM", 100, {"problem_solving": 100}, evaluated_at=datetime(2026, 1, 2, tzinfo=timezone.utc))
    e3 = build_evaluation(3, 1, 1, "MEDIUM", 60, {"problem_solving": 60}, evaluated_at=datetime(2026, 1, 3, tzinfo=timezone.utc))

    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [e1, e2, e3]

    profile = skill_profile_service.get_user_profile(mock_db, user_id=1)
    # Highest score (100) must be selected as the best attempt
    assert profile["total_evaluations_analyzed"] == 1
    assert profile["skills"]["problem_solving"]["score"] == 100
    assert profile["skills"]["problem_solving"]["sample_size"] == 1
    assert profile["skills"]["problem_solving"]["total_weight"] == 1.25


# B. Difficulty Weighting Consistency Across Easy + Medium + Hard
def test_difficulty_weighting_across_tiers(skill_profile_service):
    # Easy (w=1.0, score=70), Medium (w=1.25, score=80), Hard (w=1.5, score=95)
    # Weighted PS = (70*1.0 + 80*1.25 + 95*1.5) / (1.0 + 1.25 + 1.5) = (70 + 100 + 142.5) / 3.75 = 312.5 / 3.75 = 83.33 -> 83
    e1 = build_evaluation(1, 1, 1, "EASY", 70, {"problem_solving": 70})
    e2 = build_evaluation(2, 1, 2, "MEDIUM", 80, {"problem_solving": 80})
    e3 = build_evaluation(3, 1, 3, "HARD", 95, {"problem_solving": 95})

    profile = skill_profile_service.calculate_profile_from_evaluations([e1, e2, e3])
    assert profile["skills"]["problem_solving"]["score"] == 83
    assert profile["skills"]["problem_solving"]["sample_size"] == 3
    assert profile["skills"]["problem_solving"]["total_weight"] == 3.75


# C. Mixed Measured Dimensions (Unavailable Dimensions Never Become Zero)
def test_mixed_measured_dimensions_no_zero_pollution(skill_profile_service):
    # Challenge 1: measures Problem Solving (100) and Performance (90). Security is None.
    # Challenge 2: measures Security (80) on Hard (w=1.5).
    e1 = build_evaluation(1, 1, 1, "EASY", 100, {"problem_solving": 100, "performance": 90, "security": None})
    e2 = build_evaluation(2, 1, 2, "HARD", 80, {"problem_solving": None, "performance": None, "security": 80})

    profile = skill_profile_service.calculate_profile_from_evaluations([e1, e2])
    # PS: 100 (sample=1, weight=1.0)
    assert profile["skills"]["problem_solving"]["score"] == 100
    assert profile["skills"]["problem_solving"]["sample_size"] == 1

    # Perf: 90 (sample=1, weight=1.0)
    assert profile["skills"]["performance"]["score"] == 90

    # Security: 80 (sample=1, weight=1.5, not contaminated by e1's None)
    assert profile["skills"]["security"]["score"] == 80
    assert profile["skills"]["security"]["sample_size"] == 1
    assert profile["skills"]["security"]["total_weight"] == 1.5

    # Overall: round((100 + 90 + 80) / 3) = 90
    assert profile["overall_score"] == 90
    assert profile["measured_dimensions_count"] == 3


# D. Overall Score Averages Only Measured Dimensions
def test_overall_score_only_averages_measured_dimensions(skill_profile_service):
    # Only 1 dimension measured (Testing = 75), all other 5 dimensions None
    e1 = build_evaluation(1, 1, 1, "MEDIUM", 75, {"testing": 75})

    profile = skill_profile_service.calculate_profile_from_evaluations([e1])
    assert profile["skills"]["testing"]["score"] == 75
    assert profile["skills"]["problem_solving"]["score"] is None
    # Overall score must be 75, NOT (75 + 0 + 0 + 0 + 0 + 0) / 6 = 13!
    assert profile["overall_score"] == 75
    assert profile["measured_dimensions_count"] == 1


# E. Zero Score Is a Valid Measured Result
def test_zero_score_is_legitimate_measured_result(skill_profile_service):
    # Candidate scored 0 on Easy (w=1.0) and 100 on Hard (w=1.5)
    # Expected weighted score = (0 + 150) / 2.5 = 60
    e1 = build_evaluation(1, 1, 1, "EASY", 0, {"problem_solving": 0})
    e2 = build_evaluation(2, 1, 2, "HARD", 100, {"problem_solving": 100})

    profile = skill_profile_service.calculate_profile_from_evaluations([e1, e2])
    assert profile["skills"]["problem_solving"]["score"] == 60
    assert profile["skills"]["problem_solving"]["sample_size"] == 2
    assert profile["overall_score"] == 60


# F. No Measurements Produces overall_score = None
def test_no_measurements_produces_none_overall_score(skill_profile_service):
    e1 = build_evaluation(1, 1, 1, "EASY", 0, {"problem_solving": None, "debugging": None, "security": None})

    profile = skill_profile_service.calculate_profile_from_evaluations([e1])
    assert profile["overall_score"] is None
    assert profile["measured_dimensions_count"] == 0
    for dim, item in profile["skills"].items():
        assert item["score"] is None


# G. Duplicate Contribution Protection
def test_repeated_submissions_do_not_multiply_weight(skill_profile_service):
    mock_db = MagicMock()
    # 10 identical submissions to Challenge 1 (Hard, w=1.5, score=100)
    evals = [
        build_evaluation(i, 1, 1, "HARD", 100, {"problem_solving": 100}, evaluated_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc))
        for i in range(10)
    ]
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals

    profile = skill_profile_service.get_user_profile(mock_db, user_id=1)
    # Total evaluations analyzed must be exactly 1
    assert profile["total_evaluations_analyzed"] == 1
    assert profile["skills"]["problem_solving"]["sample_size"] == 1
    assert profile["skills"]["problem_solving"]["total_weight"] == 1.5


# H. Cross-Service Consistency: SkillProfile, Leaderboard, PublicProfile, Recruiter
def test_cross_service_consistency(
    skill_profile_service,
    leaderboard_service,
    public_profile_service,
    recruiter_service,
):
    mock_db = MagicMock()
    u1 = User(id=1, username="alex", email="alex@example.com", is_active=True)

    # Candidate has 2 challenges evaluated:
    # Challenge 1 (Beginner, w=1.0): PS=100, Performance=90
    # Challenge 2 (Advanced, w=1.5): PS=80, Debugging=100, Testing=90
    e1 = build_evaluation(1, 1, 1, "BEGINNER", 100, {"problem_solving": 100, "performance": 90})
    e2 = build_evaluation(2, 1, 2, "ADVANCED", 90, {"problem_solving": 80, "debugging": 100, "testing": 90})

    # PS weighted: (100*1.0 + 80*1.5) / 2.5 = (100 + 120) / 2.5 = 88
    # Perf: 90
    # Debugging: 100
    # Testing: 90
    # Overall: round((88 + 90 + 100 + 90) / 4) = round(368 / 4) = 92

    evals = [e1, e2]

    # 1. Direct SkillProfileService
    profile_result = skill_profile_service.calculate_profile_from_evaluations(evals)
    assert profile_result["overall_score"] == 92
    assert profile_result["skills"]["problem_solving"]["score"] == 88

    # 2. LeaderboardService (aggregates user row)
    mock_db.query.return_value.join.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals
    leaderboard_rows = leaderboard_service.get_leaderboard(mock_db, current_user_id=1)
    assert len(leaderboard_rows) == 1
    assert leaderboard_rows[0]["overall_skill_score"] == 92
    assert leaderboard_rows[0]["challenges_completed"] == 2
    assert leaderboard_rows[0]["total_points"] == 190  # 100 + 90

    # 3. PublicProfileService
    mock_db.query.return_value.filter.return_value.first.return_value = u1
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals
    public_profile = public_profile_service.get_public_profile(mock_db, username="alex")
    assert public_profile["overall_skill_score"] == 92
    assert public_profile["skill_breakdown"]["problem_solving"]["score"] == 88
    assert public_profile["skill_breakdown"]["debugging"]["score"] == 100
    assert public_profile["skill_breakdown"]["testing"]["score"] == 90
    assert public_profile["skill_breakdown"]["performance"]["score"] == 90

    # 4. RecruiterDashboardService
    mock_db.query.return_value.filter.return_value.first.return_value = u1
    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals
    candidate_detail = recruiter_service.get_candidate_detail(mock_db, username="alex")
    assert candidate_detail["overall_skill_score"] == 92
    assert candidate_detail["skills"]["problem_solving"]["score"] == 88
    assert candidate_detail["skills"]["debugging"]["score"] == 100
