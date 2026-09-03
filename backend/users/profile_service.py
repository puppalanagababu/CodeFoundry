from typing import Any, Dict, List, Optional
from django.contrib.auth import get_user_model
from evaluations.models import Evaluation
from evaluations.skill_profile import SkillProfileService
from submissions.models import Submission

User = get_user_model()


class PublicProfileService:
    """
    Produces a safe, deterministic, read-only developer public profile.
    Aggregates evaluated challenge metrics using the established best-attempt rules.
    """

    def __init__(self, skill_profile_service: Optional[SkillProfileService] = None):
        self.skill_profile_service = skill_profile_service or SkillProfileService()

    def get_public_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves and aggregates the public profile for the specified username.
        Returns None if user is not found.
        """
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        # 1. Fetch all completed evaluations on active challenges for this user in a single query
        evaluations_qs = (
            Evaluation.objects.filter(
                submission__user=user,
                status=Evaluation.Status.COMPLETED,
                submission__challenge__is_active=True,
            )
            .select_related("submission", "submission__challenge")
            .order_by(
                "submission__challenge_id",
                "-submission__score",
                "-evaluated_at",
                "-id",
            )
        )

        evaluations_list = list(evaluations_qs)

        # 2. Deduplicate by challenge: select best attempt per active challenge
        best_evals_by_challenge: Dict[int, Evaluation] = {}
        for eval_obj in evaluations_list:
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

        # 3. Compute Metrics
        challenges_attempted = len(selected_evals)

        if challenges_attempted > 0:
            best_scores = [getattr(e.submission, "score", 0) or 0 for e in selected_evals]
            total_points = sum(best_scores)
            challenges_completed = sum(
                1 for e in selected_evals if getattr(e.submission, "status", None) == Submission.Status.PASSED
            )
            completion_percentage = round((challenges_completed / challenges_attempted) * 100, 1)
            average_score = round(sum(best_scores) / challenges_attempted, 1)

            # Skill profile breakdown
            profile_data = self.skill_profile_service.calculate_profile_from_evaluations(selected_evals)
            overall_skill_score = profile_data.get("overall_score")
            skill_breakdown = profile_data.get("skills", {})
        else:
            total_points = 0
            challenges_completed = 0
            completion_percentage = 0.0
            average_score = None
            empty_profile = self.skill_profile_service._empty_profile()
            overall_skill_score = None
            skill_breakdown = empty_profile.get("skills", {})

        # 4. Fetch 5 most recent evaluated activities
        recent_evals_qs = (
            Evaluation.objects.filter(
                submission__user=user,
                status=Evaluation.Status.COMPLETED,
                submission__challenge__is_active=True,
            )
            .select_related("submission", "submission__challenge")
            .order_by("-evaluated_at", "-id")[:5]
        )

        recent_activity: List[Dict[str, Any]] = []
        for eval_obj in recent_evals_qs:
            challenge = getattr(eval_obj.submission, "challenge", None)
            if not challenge:
                continue

            evaluated_at_str = (
                eval_obj.evaluated_at.isoformat()
                if eval_obj.evaluated_at
                else (eval_obj.created_at.isoformat() if eval_obj.created_at else None)
            )

            recent_activity.append({
                "challenge_id": challenge.id,
                "challenge_title": challenge.title,
                "challenge_type": challenge.challenge_type,
                "difficulty": challenge.difficulty,
                "score": getattr(eval_obj.submission, "score", 0) or 0,
                "status": getattr(eval_obj.submission, "status", "COMPLETED"),
                "evaluated_at": evaluated_at_str,
            })

        # 5. Fetch earned achievements via AchievementService
        from evaluations.achievements import AchievementService
        earned_achievements = AchievementService().get_user_achievements(user)

        return {
            "username": user.username,
            "overall_skill_score": overall_skill_score,
            "skill_breakdown": skill_breakdown,
            "challenges_completed": challenges_completed,
            "challenges_attempted": challenges_attempted,
            "completion_percentage": completion_percentage,
            "average_score": average_score,
            "total_points": total_points,
            "achievements": earned_achievements,
            "recent_activity": recent_activity,
        }
