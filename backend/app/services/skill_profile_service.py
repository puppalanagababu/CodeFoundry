from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission


# ==============================================================================
# Centralized Difficulty Weight Configuration (Engineering Calibration Parameters)
# ==============================================================================
DIFFICULTY_WEIGHTS: Dict[str, float] = {
    # Standard calibration tiers
    "EASY": 1.0,
    "MEDIUM": 1.25,
    "HARD": 1.5,
    # Database enum mappings
    "BEGINNER": 1.0,
    "INTERMEDIATE": 1.25,
    "ADVANCED": 1.5,
    "EXPERT": 1.75,
}

DEFAULT_DIFFICULTY_WEIGHT: float = 1.0


def get_difficulty_weight(difficulty: Optional[str]) -> float:
    """
    Resolves the numerical difficulty weight for challenge aggregation.
    Defaults to 1.0 for missing, None, or unrecognized difficulty strings.
    """
    if not difficulty or not isinstance(difficulty, str):
        return DEFAULT_DIFFICULTY_WEIGHT
    key = difficulty.strip().upper()
    return DIFFICULTY_WEIGHTS.get(key, DEFAULT_DIFFICULTY_WEIGHT)


class SkillProfileService:
    """
    Dynamically aggregates completed challenge evaluations for a student
    into an explainable, deterministic, difficulty-weighted skill profile.
    Uses standalone SQLAlchemy 2.0 sessions.
    """

    MEASURABLE_DIMENSIONS = {
        "problem_solving",
        "debugging",
        "security",
        "performance",
        "code_quality",
        "testing",
    }

    UNMEASURED_DIMENSIONS = {
        "code_quality",
        "testing",
    }

    ALL_DIMENSIONS = [
        "problem_solving",
        "debugging",
        "security",
        "performance",
        "code_quality",
        "testing",
    ]

    def get_user_profile(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Calculates and returns the aggregated skill profile for a user ID.
        """
        if not user_id:
            return self._empty_profile()

        # Query all completed evaluations belonging to the user
        evaluations = (
            db.query(Evaluation)
            .join(Submission, Evaluation.submission_id == Submission.id)
            .join(Challenge, Submission.challenge_id == Challenge.id)
            .options(
                joinedload(Evaluation.submission).joinedload(Submission.challenge)
            )
            .filter(
                Submission.user_id == user_id,
                Evaluation.status == EvaluationStatus.COMPLETED.value,
                Challenge.is_active == True,
            )
            .order_by(
                Submission.challenge_id.asc(),
                Submission.score.desc(),
                Evaluation.evaluated_at.desc(),
                Evaluation.id.desc(),
            )
            .all()
        )

        if not evaluations:
            return self._empty_profile()

        # Deduplicate by challenge: select best attempt per challenge
        best_evaluations_by_challenge: Dict[int, Evaluation] = {}
        for eval_obj in evaluations:
            ch_id = eval_obj.submission.challenge_id if eval_obj.submission else None
            if ch_id is None:
                continue

            if ch_id not in best_evaluations_by_challenge:
                best_evaluations_by_challenge[ch_id] = eval_obj
            else:
                current_best = best_evaluations_by_challenge[ch_id]
                current_score = current_best.submission.score if current_best.submission else 0
                new_score = eval_obj.submission.score if eval_obj.submission else 0

                if new_score > current_score:
                    best_evaluations_by_challenge[ch_id] = eval_obj
                elif new_score == current_score:
                    current_time = current_best.evaluated_at or current_best.created_at
                    new_time = eval_obj.evaluated_at or eval_obj.created_at
                    if current_time and new_time and new_time > current_time:
                        best_evaluations_by_challenge[ch_id] = eval_obj
                    elif current_time == new_time and eval_obj.id > current_best.id:
                        best_evaluations_by_challenge[ch_id] = eval_obj

        selected_evaluations = list(best_evaluations_by_challenge.values())
        return self.calculate_profile_from_evaluations(selected_evaluations)

    def calculate_profile_from_evaluations(
        self, selected_evaluations: List[Evaluation]
    ) -> Dict[str, Any]:
        """
        Calculates and returns the difficulty-weighted skill profile for a list of evaluated challenge attempts.
        """
        if not selected_evaluations:
            return self._empty_profile()

        total_analyzed = len(selected_evaluations)

        # Track weighted sum, total weights, and counts per dimension
        dim_aggregates: Dict[str, Dict[str, Any]] = {
            dim: {
                "weighted_sum": 0.0,
                "total_weight": 0.0,
                "sample_size": 0,
                "has_measured_attempt": False,
            }
            for dim in self.ALL_DIMENSIONS
        }

        for eval_obj in selected_evaluations:
            breakdown = getattr(eval_obj, "skill_breakdown", None)
            if not isinstance(breakdown, dict):
                continue

            scores_map = breakdown.get("scores")
            if not isinstance(scores_map, dict):
                continue

            # Resolve challenge difficulty weight
            sub = getattr(eval_obj, "submission", None)
            challenge = getattr(sub, "challenge", None)
            diff_str = getattr(challenge, "difficulty", None)
            weight = get_difficulty_weight(diff_str)

            for dim in self.ALL_DIMENSIONS:
                val = scores_map.get(dim)
                # Only include valid numeric measurements (exclude None, booleans, and error strings)
                if val is not None and isinstance(val, (int, float)) and not isinstance(val, bool):
                    dim_aggregates[dim]["weighted_sum"] += float(val) * weight
                    dim_aggregates[dim]["total_weight"] += weight
                    dim_aggregates[dim]["sample_size"] += 1
                    dim_aggregates[dim]["has_measured_attempt"] = True

        # Compute dimension aggregations and statuses
        skills_output: Dict[str, Dict[str, Any]] = {}
        measured_dimension_scores: List[int] = []

        for dim in self.ALL_DIMENSIONS:
            agg = dim_aggregates[dim]
            sample_size = agg["sample_size"]
            total_weight = agg["total_weight"]

            if sample_size > 0 and total_weight > 0:
                weighted_avg = round(agg["weighted_sum"] / total_weight)
                bounded_score = max(0, min(100, weighted_avg))
                skills_output[dim] = {
                    "score": bounded_score,
                    "sample_size": sample_size,
                    "total_weight": round(total_weight, 2),
                    "status": "measured",
                }
                measured_dimension_scores.append(bounded_score)
            else:
                if dim in self.UNMEASURED_DIMENSIONS and not agg["has_measured_attempt"]:
                    status_str = "not_measured"
                else:
                    status_str = "insufficient_data"

                skills_output[dim] = {
                    "score": None,
                    "sample_size": 0,
                    "total_weight": 0.0,
                    "status": status_str,
                }

        # Calculate overall score across measured dimensions
        if measured_dimension_scores:
            overall_avg = round(sum(measured_dimension_scores) / len(measured_dimension_scores))
            overall_score = max(0, min(100, overall_avg))
        else:
            overall_score = None

        return {
            "overall_score": overall_score,
            "skills": skills_output,
            "total_evaluations_analyzed": total_analyzed,
            "measured_dimensions_count": len(measured_dimension_scores),
        }

    def _empty_profile(self) -> Dict[str, Any]:
        skills_output: Dict[str, Dict[str, Any]] = {}
        for dim in self.ALL_DIMENSIONS:
            if dim in self.UNMEASURED_DIMENSIONS:
                status_str = "not_measured"
            else:
                status_str = "insufficient_data"

            skills_output[dim] = {
                "score": None,
                "sample_size": 0,
                "total_weight": 0.0,
                "status": status_str,
            }

        return {
            "overall_score": None,
            "skills": skills_output,
            "total_evaluations_analyzed": 0,
            "measured_dimensions_count": 0,
        }
