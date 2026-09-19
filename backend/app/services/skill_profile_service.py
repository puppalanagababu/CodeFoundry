from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission


class SkillProfileService:
    """
    Dynamically aggregates completed challenge evaluations for a student
    into an explainable, deterministic skill profile.
    Uses standalone SQLAlchemy 2.0 sessions.
    """

    MEASURABLE_DIMENSIONS = {
        "problem_solving",
        "debugging",
        "security",
        "performance",
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

        selected_evaluations = list(best_evaluations_by_challenge.values())
        return self.calculate_profile_from_evaluations(selected_evaluations)

    def calculate_profile_from_evaluations(
        self, selected_evaluations: List[Evaluation]
    ) -> Dict[str, Any]:
        """
        Calculates and returns the aggregated skill profile for a list of evaluated challenge attempts.
        """
        if not selected_evaluations:
            return self._empty_profile()

        total_analyzed = len(selected_evaluations)

        # Collect scores per dimension across deduplicated challenge attempts
        dimension_scores: Dict[str, List[float]] = {dim: [] for dim in self.ALL_DIMENSIONS}

        for eval_obj in selected_evaluations:
            breakdown = eval_obj.skill_breakdown
            if not isinstance(breakdown, dict):
                continue

            scores_map = breakdown.get("scores")
            if not isinstance(scores_map, dict):
                continue

            for dim in self.ALL_DIMENSIONS:
                val = scores_map.get(dim)
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    dimension_scores[dim].append(float(val))

        # Compute dimension aggregations and statuses
        skills_output: Dict[str, Dict[str, Any]] = {}
        measured_dimension_scores: List[int] = []

        for dim in self.ALL_DIMENSIONS:
            scores = dimension_scores[dim]
            sample_size = len(scores)

            if sample_size > 0:
                avg_score = round(sum(scores) / sample_size)
                bounded_score = max(0, min(100, avg_score))
                skills_output[dim] = {
                    "score": bounded_score,
                    "sample_size": sample_size,
                    "status": "measured",
                }
                measured_dimension_scores.append(bounded_score)
            else:
                if dim in self.UNMEASURED_DIMENSIONS:
                    status_str = "not_measured"
                else:
                    status_str = "insufficient_data"

                skills_output[dim] = {
                    "score": None,
                    "sample_size": 0,
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
                "status": status_str,
            }

        return {
            "overall_score": None,
            "skills": skills_output,
            "total_evaluations_analyzed": 0,
        }
