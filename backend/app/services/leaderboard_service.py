from collections import defaultdict
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.skill_profile_service import SkillProfileService


class LeaderboardService:
    """
    Produces an explainable, deterministic, and high-performance developer leaderboard.
    Calculates leaderboard rankings across distinct active challenges using only completed/evaluated user activity.
    Avoids N+1 queries by bulk-fetching and grouping in memory.
    """

    def __init__(self, skill_profile_service: Optional[SkillProfileService] = None):
        self.skill_profile_service = skill_profile_service or SkillProfileService()

    def get_leaderboard(
        self, db: Session, current_user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculates and returns the ranked developer leaderboard list.
        """
        # 1. Fetch all completed evaluations on active challenges in a single query
        evaluations = (
            db.query(Evaluation)
            .join(Submission, Evaluation.submission_id == Submission.id)
            .join(Challenge, Submission.challenge_id == Challenge.id)
            .join(User, Submission.user_id == User.id)
            .options(
                joinedload(Evaluation.submission).joinedload(Submission.user),
                joinedload(Evaluation.submission).joinedload(Submission.challenge),
            )
            .filter(
                Evaluation.status == EvaluationStatus.COMPLETED.value,
                Challenge.is_active == True,
            )
            .order_by(
                Submission.user_id.asc(),
                Submission.challenge_id.asc(),
                Submission.score.desc(),
                Evaluation.evaluated_at.desc(),
                Evaluation.id.desc(),
            )
            .all()
        )

        if not evaluations:
            return []

        # 2. Group evaluations by user_id
        evaluations_by_user: Dict[int, List[Evaluation]] = defaultdict(list)
        user_map: Dict[int, User] = {}

        for eval_obj in evaluations:
            sub = eval_obj.submission
            if not sub or not sub.user_id:
                continue
            u_id = sub.user_id
            user_map[u_id] = sub.user
            evaluations_by_user[u_id].append(eval_obj)

        if not evaluations_by_user:
            return []

        # 3. For each user, select the single best attempt per active challenge
        user_rows: List[Dict[str, Any]] = []

        for user_id, user_evals in evaluations_by_user.items():
            user = user_map[user_id]
            best_evals_by_challenge: Dict[int, Evaluation] = {}

            for eval_obj in user_evals:
                ch_id = eval_obj.submission.challenge_id if eval_obj.submission else None
                if ch_id is None:
                    continue

                if ch_id not in best_evals_by_challenge:
                    best_evals_by_challenge[ch_id] = eval_obj
                else:
                    current_best = best_evals_by_challenge[ch_id]
                    current_score = current_best.submission.score if current_best.submission else 0
                    new_score = eval_obj.submission.score if eval_obj.submission else 0

                    if new_score > current_score:
                        best_evals_by_challenge[ch_id] = eval_obj
                    elif new_score == current_score:
                        current_time = current_best.evaluated_at or current_best.created_at
                        new_time = eval_obj.evaluated_at or eval_obj.created_at
                        if current_time and new_time and new_time > current_time:
                            best_evals_by_challenge[ch_id] = eval_obj
                        elif current_time == new_time and eval_obj.id > current_best.id:
                            best_evals_by_challenge[ch_id] = eval_obj

            selected_evals = list(best_evals_by_challenge.values())
            if not selected_evals:
                continue

            # Compute aggregates
            best_scores = [e.submission.score or 0 for e in selected_evals if e.submission]
            total_points = sum(best_scores)

            # Count distinct challenges where user has a passed evaluation
            challenges_completed = sum(
                1 for e in selected_evals if e.submission and e.submission.status == SubmissionStatus.PASSED.value
            )

            # Average score across distinct attempted challenges
            avg_score = round(sum(best_scores) / len(best_scores), 1) if best_scores else 0.0

            # Compute overall skill score via SkillProfileService
            profile = self.skill_profile_service.calculate_profile_from_evaluations(selected_evals)
            overall_skill_score = profile.get("overall_score")

            is_current = (current_user_id == user_id) if current_user_id is not None else False

            user_rows.append({
                "user_id": user_id,
                "username": getattr(user, "username", f"user_{user_id}"),
                "total_points": total_points,
                "challenges_completed": challenges_completed,
                "average_score": avg_score,
                "overall_skill_score": overall_skill_score,
                "is_current_user": is_current,
            })

        # 4. Deterministic Ranking:
        # 1. total_points DESC
        # 2. challenges_completed DESC
        # 3. average_score DESC
        # 4. overall_skill_score DESC (None treated as -1)
        # 5. username ASC (case-insensitive)
        def sort_key(row: Dict[str, Any]):
            skill_score = row["overall_skill_score"]
            skill_score_val = -1 if skill_score is None else skill_score
            return (
                -row["total_points"],
                -row["challenges_completed"],
                -row["average_score"],
                -skill_score_val,
                str(row["username"]).lower(),
            )

        user_rows.sort(key=sort_key)

        # 5. Assign 1-based rank
        for rank_idx, row in enumerate(user_rows, start=1):
            row["rank"] = rank_idx

        return user_rows
