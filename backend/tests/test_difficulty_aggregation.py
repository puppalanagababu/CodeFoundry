import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from app.models.challenge import Challenge, ChallengeType, Difficulty
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission
from app.services.skill_profile_service import (
    DIFFICULTY_WEIGHTS,
    DEFAULT_DIFFICULTY_WEIGHT,
    SkillProfileService,
    get_difficulty_weight,
)


@pytest.fixture
def profile_service():
    return SkillProfileService()


def create_eval(
    eval_id: int,
    challenge_id: int,
    difficulty: str,
    scores: dict,
    submission_score: int = 100,
    evaluated_at: datetime = None,
) -> Evaluation:
    challenge = Challenge(
        id=challenge_id,
        title=f"Challenge {challenge_id}",
        slug=f"challenge-{challenge_id}",
        difficulty=difficulty,
        is_active=True,
    )
    sub = Submission(
        id=eval_id * 10,
        user_id=1,
        challenge_id=challenge_id,
        challenge=challenge,
        score=submission_score,
        status="PASSED",
    )
    return Evaluation(
        id=eval_id,
        submission_id=sub.id,
        submission=sub,
        status=EvaluationStatus.COMPLETED.value,
        skill_breakdown={"scores": scores},
        evaluated_at=evaluated_at or datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


# 1. Easy / Medium / Hard Weighted Average
def test_easy_medium_hard_weighted_average(profile_service):
    # Easy (w=1.0, score=80), Hard (w=1.5, score=100)
    # Expected weighted PS = (80 * 1.0 + 100 * 1.5) / (1.0 + 1.5) = (80 + 150) / 2.5 = 92
    e1 = create_eval(1, 1, "EASY", {"problem_solving": 80})
    e2 = create_eval(2, 2, "HARD", {"problem_solving": 100})

    profile = profile_service.calculate_profile_from_evaluations([e1, e2])
    ps_data = profile["skills"]["problem_solving"]
    assert ps_data["status"] == "measured"
    assert ps_data["score"] == 92
    assert ps_data["sample_size"] == 2
    assert ps_data["total_weight"] == 2.5


# 2. Equal Difficulty Weighting
def test_equal_difficulty_weighting(profile_service):
    # Two MEDIUM challenges (w=1.25): scores 60 and 80 -> average 70
    e1 = create_eval(1, 1, "MEDIUM", {"problem_solving": 60})
    e2 = create_eval(2, 2, "MEDIUM", {"problem_solving": 80})

    profile = profile_service.calculate_profile_from_evaluations([e1, e2])
    ps_data = profile["skills"]["problem_solving"]
    assert ps_data["score"] == 70
    assert ps_data["total_weight"] == 2.5


# 3. Single Challenge Evaluation
def test_single_challenge_evaluation(profile_service):
    # Single Hard challenge (w=1.5, score=75) -> weighted score is exactly 75
    e1 = create_eval(1, 1, "HARD", {"problem_solving": 75, "performance": 85})

    profile = profile_service.calculate_profile_from_evaluations([e1])
    assert profile["skills"]["problem_solving"]["score"] == 75
    assert profile["skills"]["problem_solving"]["total_weight"] == 1.5
    assert profile["skills"]["performance"]["score"] == 85
    assert profile["overall_score"] == 80  # (75 + 85) / 2


# 4. Score of Zero Included in Weighted Average
def test_score_of_zero_included(profile_service):
    # Easy (w=1.0, score=0), Hard (w=1.5, score=100)
    # Expected PS = (0 * 1.0 + 100 * 1.5) / 2.5 = 150 / 2.5 = 60
    e1 = create_eval(1, 1, "EASY", {"problem_solving": 0})
    e2 = create_eval(2, 2, "HARD", {"problem_solving": 100})

    profile = profile_service.calculate_profile_from_evaluations([e1, e2])
    assert profile["skills"]["problem_solving"]["score"] == 60


# 5. Score of 100 Bounded Correctly
def test_score_of_100_bounded(profile_service):
    e1 = create_eval(1, 1, "HARD", {"problem_solving": 100, "code_quality": 100})
    e2 = create_eval(2, 2, "ADVANCED", {"problem_solving": 100, "code_quality": 100})

    profile = profile_service.calculate_profile_from_evaluations([e1, e2])
    assert profile["skills"]["problem_solving"]["score"] == 100
    assert profile["skills"]["code_quality"]["score"] == 100
    assert profile["overall_score"] == 100


# 6. None and Non-Measured Excluded from Denominator (Never Counted as Zero)
def test_none_and_unmeasured_excluded_from_denominator(profile_service):
    # Challenge 1 has security=None (not measured on that challenge), Challenge 2 has security=90 (HARD)
    e1 = create_eval(1, 1, "EASY", {"problem_solving": 100, "security": None})
    e2 = create_eval(2, 2, "HARD", {"problem_solving": 100, "security": 90})

    profile = profile_service.calculate_profile_from_evaluations([e1, e2])
    # Security must NOT be pulled down to 45 by treating e1 as 0; must be 90
    assert profile["skills"]["security"]["score"] == 90
    assert profile["skills"]["security"]["sample_size"] == 1
    assert profile["skills"]["security"]["total_weight"] == 1.5


# 7. No Available Measurements Returns Insufficient Data
def test_no_available_measurements_returns_insufficient_data(profile_service):
    e1 = create_eval(1, 1, "EASY", {"problem_solving": None, "debugging": None})

    profile = profile_service.calculate_profile_from_evaluations([e1])
    assert profile["skills"]["problem_solving"]["score"] is None
    assert profile["skills"]["problem_solving"]["status"] == "insufficient_data"
    assert profile["overall_score"] is None


# 8. Empty Evaluation List
def test_empty_evaluations_profile(profile_service):
    profile = profile_service.calculate_profile_from_evaluations([])
    assert profile["overall_score"] is None
    assert profile["total_evaluations_analyzed"] == 0
    assert profile["measured_dimensions_count"] == 0
    assert profile["skills"]["problem_solving"]["score"] is None


# 9. Missing and Unknown Difficulty Fallback to 1.0
def test_missing_and_unknown_difficulty_fallback(profile_service):
    assert get_difficulty_weight(None) == 1.0
    assert get_difficulty_weight("") == 1.0
    assert get_difficulty_weight("UNKNOWN_TIER") == 1.0
    assert get_difficulty_weight("CUSTOM_DIFFICULTY") == 1.0

    # Challenge with unknown difficulty gets weight 1.0
    e1 = create_eval(1, 1, "UNKNOWN", {"problem_solving": 80})
    profile = profile_service.calculate_profile_from_evaluations([e1])
    assert profile["skills"]["problem_solving"]["total_weight"] == 1.0
    assert profile["skills"]["problem_solving"]["score"] == 80


# 10. Case-Insensitive Difficulty Matching
def test_case_insensitive_difficulty_matching():
    assert get_difficulty_weight("easy") == 1.0
    assert get_difficulty_weight("Medium") == 1.25
    assert get_difficulty_weight("HARD") == 1.5
    assert get_difficulty_weight("beginner") == 1.0
    assert get_difficulty_weight("Intermediate") == 1.25
    assert get_difficulty_weight("advanced") == 1.5
    assert get_difficulty_weight("Expert") == 1.75


# 11. Overall Profile Calculation Across Measured Dimensions Only
def test_overall_profile_score_calculation(profile_service):
    # Challenge 1 has PS=80, Challenge 2 has Debugging=100
    e1 = create_eval(1, 1, "EASY", {"problem_solving": 80, "debugging": None})
    e2 = create_eval(2, 2, "EASY", {"problem_solving": None, "debugging": 100})

    profile = profile_service.calculate_profile_from_evaluations([e1, e2])
    assert profile["skills"]["problem_solving"]["score"] == 80
    assert profile["skills"]["debugging"]["score"] == 100
    # Overall score = (80 + 100) / 2 = 90
    assert profile["overall_score"] == 90
    assert profile["measured_dimensions_count"] == 2


# 12. Multi-Dimension Mixed Measurements Across Varied Difficulties
def test_multi_dimension_mixed_difficulties(profile_service):
    # Challenge 1: Beginner (w=1.0) -> PS=100, Perf=80
    # Challenge 2: Intermediate (w=1.25) -> PS=80, CQ=90, Testing=70
    # Challenge 3: Advanced (w=1.5) -> PS=60, Debugging=100, Security=90
    e1 = create_eval(1, 1, "BEGINNER", {"problem_solving": 100, "performance": 80})
    e2 = create_eval(2, 2, "INTERMEDIATE", {"problem_solving": 80, "code_quality": 90, "testing": 70})
    e3 = create_eval(3, 3, "ADVANCED", {"problem_solving": 60, "debugging": 100, "security": 90})

    profile = profile_service.calculate_profile_from_evaluations([e1, e2, e3])

    # PS weighted: (100*1.0 + 80*1.25 + 60*1.5) / (1.0 + 1.25 + 1.5) = (100 + 100 + 90) / 3.75 = 290 / 3.75 = 77.33 -> 77
    assert profile["skills"]["problem_solving"]["score"] == 77
    assert profile["skills"]["problem_solving"]["sample_size"] == 3
    assert profile["skills"]["problem_solving"]["total_weight"] == 3.75

    # Perf: (80*1.0) / 1.0 = 80
    assert profile["skills"]["performance"]["score"] == 80

    # CQ: (90*1.25) / 1.25 = 90
    assert profile["skills"]["code_quality"]["score"] == 90

    # Testing: (70*1.25) / 1.25 = 70
    assert profile["skills"]["testing"]["score"] == 70

    # Debugging: (100*1.5) / 1.5 = 100
    assert profile["skills"]["debugging"]["score"] == 100

    # Security: (90*1.5) / 1.5 = 90
    assert profile["skills"]["security"]["score"] == 90

    # Overall: round((77 + 80 + 90 + 70 + 100 + 90) / 6) = round(507 / 6) = round(84.5) = 84
    assert profile["overall_score"] == 84
    assert profile["measured_dimensions_count"] == 6


# 13. Anti-Gaming: Best Attempt Deduplication Prevents Weight Multiplication
def test_anti_gaming_best_attempt_deduplication(profile_service):
    # User submits 5 times to the same HARD challenge (challenge_id = 1)
    # The deduplication logic in get_user_profile selects the single best attempt
    mock_db = MagicMock()
    c1 = Challenge(id=1, slug="hard-challenge", title="Hard Challenge", difficulty="HARD", is_active=True)

    subs = [
        Submission(id=i, user_id=1, challenge_id=1, challenge=c1, score=100 - i * 10, status="PASSED")
        for i in range(5)
    ]
    evals = [
        Evaluation(
            id=i,
            submission_id=subs[i].id,
            submission=subs[i],
            status="COMPLETED",
            skill_breakdown={"scores": {"problem_solving": 100}},
            evaluated_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
        )
        for i in range(5)
    ]

    mock_db.query.return_value.join.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = evals

    profile = profile_service.get_user_profile(mock_db, user_id=1)
    # Must only analyze 1 evaluation with weight 1.5, NOT 5 evaluations with weight 7.5
    assert profile["total_evaluations_analyzed"] == 1
    assert profile["skills"]["problem_solving"]["sample_size"] == 1
    assert profile["skills"]["problem_solving"]["total_weight"] == 1.5
    assert profile["skills"]["problem_solving"]["score"] == 100
