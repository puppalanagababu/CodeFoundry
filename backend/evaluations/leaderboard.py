from collections import defaultdict
from typing import Any, Dict, List, Optional
from django.contrib.auth import get_user_model
from .models import Evaluation
from .skill_profile import SkillProfileService
from submissions.models import Submission

User = get_user_model()


class LeaderboardService:
    """
    Produces an explainable, deterministic, and high-performance developer leaderboard.
    Calculates leaderboard rankings across distinct active challenges using only completed/evaluated user activity.
    Avoids N+1 queries by bulk-fetching and grouping in memory.
    """

    def __init__(self, skill_profile_service: Optional[SkillProfileService] = None):
        self.skill_profile_service = skill_profile_service or SkillProfileService()

    def get_leaderboard(self, current_user: Any = None) -> List[Dict[str, Any]]:
        """
        Calculates and returns the ranked developer leaderboard list.
        """
        # 1. Fetch all completed evaluations on active challenges in a single query
        evaluations_qs = (
            Evaluation.objects.filter(
                status=Evaluation.Status.COMPLETED,
                submission__challenge__is_active=True,
                submission__user__isnull=False,
            )
            .select_related("submission", "submission__user", "submission__challenge")
            .order_by(
                "submission__user_id",
                "submission__challenge_id",
                "-submission__score",
                "-evaluated_at",
                "-id",
            )
        )

        evaluations_list = list(evaluations_qs)
        if not evaluations_list:
            return []

        # 2. Group evaluations by user_id
        evaluations_by_user: Dict[int, List[Evaluation]] = defaultdict(list)
        user_map: Dict[int, Any] = {}

        for eval_obj in evaluations_list:
            user = getattr(eval_obj.submission, "user", None)
            if not user or not getattr(user, "id", None):
                continue
            user_id = user.id
            user_map[user_id] = user
            evaluations_by_user[user_id].append(eval_obj)

        if not evaluations_by_user:
            return []

        # 3. For each user, select the single best attempt per active challenge
        current_user_id = getattr(current_user, "id", None) if getattr(current_user, "is_authenticated", False) else None
        user_rows: List[Dict[str, Any]] = []

        for user_id, user_evals in evaluations_by_user.items():
            user = user_map[user_id]
            best_evals_by_challenge: Dict[int, Evaluation] = {}

            for eval_obj in user_evals:
                challenge_id = (
                    getattr(eval_obj.submission, "challenge_id", None)
                    or getattr(getattr(eval_obj.submission, "challenge", None), "id", None)
                )
                if challenge_id is None:
                    continue

                if challenge_id not in best_evals_by_challenge:
                    best_evals_by_challenge[challenge_id] = eval_obj
                else:
                    current_best = best_evals_by_challenge[challenge_id]
                    current_score = getattr(current_best.submission, "score", 0) or 0
                    new_score = getattr(eval_obj.submission, "score", 0) or 0

                    if new_score > current_score:
                        best_evals_by_challenge[challenge_id] = eval_obj
                    elif new_score == current_score:
                        current_time = current_best.evaluated_at or current_best.created_at
                        new_time = eval_obj.evaluated_at or eval_obj.created_at
                        if current_time and new_time and new_time > current_time:
                            best_evals_by_challenge[challenge_id] = eval_obj
                        elif current_time == new_time and eval_obj.id > current_best.id:
                            best_evals_by_challenge[challenge_id] = eval_obj

            selected_evals = list(best_evals_by_challenge.values())
            if not selected_evals:
                continue

            # Compute aggregates
            best_scores = [getattr(e.submission, "score", 0) or 0 for e in selected_evals]
            total_points = sum(best_scores)
            
            # Count distinct challenges where user has a passed evaluation
            challenges_completed = sum(
                1 for e in selected_evals if getattr(e.submission, "status", None) == Submission.Status.PASSED
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
