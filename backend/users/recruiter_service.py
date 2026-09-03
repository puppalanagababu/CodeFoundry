import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional
from django.contrib.auth import get_user_model
from django.db.models import Count
from challenges.models import Challenge
from evaluations.achievements import AchievementService
from evaluations.models import Evaluation, UserAchievement
from evaluations.skill_profile import SkillProfileService
from submissions.models import Submission

logger = logging.getLogger(__name__)
User = get_user_model()


class RecruiterDashboardService:
    """
    Service layer providing authorized recruiters with safe, deterministic
    candidate engineering assessments derived from evaluated challenges.
    """

    def get_candidates(
        self,
        search: str = "",
        min_skill_score: Optional[int] = None,
        challenge_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves candidate summaries for developers who have completed evaluations.
        Applies filtering, best-attempt deduplication, deterministic sorting, and privacy data minimization.
        Zero N+1 queries.
        """
        # 1. Fetch all completed evaluations on active challenges in a single bulk query
        evaluations_qs = (
            Evaluation.objects.filter(
                status=Evaluation.Status.COMPLETED,
                submission__challenge__is_active=True,
            )
            .select_related("submission", "submission__challenge", "submission__user")
            .order_by("-submission__score", "-evaluated_at", "-id")
        )

        evaluations_list = list(evaluations_qs)
        if not evaluations_list:
            return []

        # 2. Bulk load achievement counts per user in a single query
        achievement_counts = {
            row["user_id"]: row["count"]
            for row in UserAchievement.objects.filter(achievement__is_active=True)
            .values("user_id")
            .annotate(count=Count("id"))
        }

        # 3. Group evaluations by user
        evals_by_user = defaultdict(list)
        users_by_id = {}

        for eval_obj in evaluations_list:
            sub = eval_obj.submission
            user = getattr(sub, "user", None)
            if not user or not user.id:
                continue

            users_by_id[user.id] = user
            evals_by_user[user.id].append(eval_obj)

        candidates: List[Dict[str, Any]] = []

        # 4. Process each candidate with best-attempt deduplication
        for user_id, user_evals in evals_by_user.items():
            user = users_by_id[user_id]

            # Best-attempt deduplication per challenge
            best_evals_by_challenge: Dict[int, Evaluation] = {}
            for eval_obj in user_evals:
                cid = (
                    getattr(eval_obj.submission, "challenge_id", None)
                    or getattr(getattr(eval_obj.submission, "challenge", None), "id", None)
                )
                if cid is None:
                    continue

                if cid not in best_evals_by_challenge:
                    best_evals_by_challenge[cid] = eval_obj
                else:
                    current_best = best_evals_by_challenge[cid]
                    current_score = getattr(current_best.submission, "score", 0) or 0
                    new_score = getattr(eval_obj.submission, "score", 0) or 0

                    if new_score > current_score:
                        best_evals_by_challenge[cid] = eval_obj
                    elif new_score == current_score:
                        cur_time = current_best.evaluated_at or current_best.created_at
                        new_time = eval_obj.evaluated_at or eval_obj.created_at
                        if cur_time and new_time and new_time > cur_time:
                            best_evals_by_challenge[cid] = eval_obj
                        elif cur_time == new_time and eval_obj.id > current_best.id:
                            best_evals_by_challenge[cid] = eval_obj

            selected_evals = list(best_evals_by_challenge.values())
            if not selected_evals:
                continue

            # Calculate metrics
            challenges_attempted = len(selected_evals)
            scores = [getattr(e.submission, "score", 0) or 0 for e in selected_evals]
            challenges_completed = sum(
                1 for e in selected_evals if getattr(e.submission, "status", None) == Submission.Status.PASSED
            )
            total_points = sum(scores)
            average_score = (
                round(total_points / challenges_attempted, 1)
                if challenges_attempted > 0
                else None
            )
            completion_percentage = (
                round((challenges_completed / challenges_attempted) * 100, 1)
                if challenges_attempted > 0
                else 0.0
            )

            skill_profile = SkillProfileService().calculate_profile_from_evaluations(selected_evals)
            overall_skill_score = skill_profile.get("overall_score")
            ach_count = achievement_counts.get(user_id, 0)

            # Check challenge types attempted
            attempted_types = {
                getattr(getattr(e.submission, "challenge", None), "challenge_type", "")
                for e in selected_evals
            }

            candidate_summary = {
                "user_id": user.id,
                "username": user.username,
                "overall_skill_score": overall_skill_score,
                "total_points": total_points,
                "challenges_completed": challenges_completed,
                "challenges_attempted": challenges_attempted,
                "average_score": average_score,
                "completion_percentage": completion_percentage,
                "achievements_count": ach_count,
                "_attempted_types": attempted_types,
            }

            candidates.append(candidate_summary)

        # 5. Apply Search & Filters
        filtered: List[Dict[str, Any]] = []
        for cand in candidates:
            # Username search
            if search and search.strip():
                if search.strip().lower() not in cand["username"].lower():
                    continue

            # Minimum skill score filter
            if min_skill_score is not None:
                score = cand["overall_skill_score"]
                if score is None or score < min_skill_score:
                    continue

            # Challenge type filter
            if challenge_type and challenge_type.strip():
                ctype_clean = challenge_type.strip().upper()
                if ctype_clean not in cand.get("_attempted_types", set()):
                    continue

            # Remove internal fields
            cand.pop("_attempted_types", None)
            filtered.append(cand)

        # 6. Deterministic Sorting:
        # overall_skill_score DESC (nulls last) -> total_points DESC -> challenges_completed DESC -> username ASC
        filtered.sort(
            key=lambda c: (
                1 if c["overall_skill_score"] is not None else 0,
                c["overall_skill_score"] or 0,
                c["total_points"],
                c["challenges_completed"],
                -c["user_id"],
            ),
            reverse=True,
        )

        return filtered

    def get_candidate_detail(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed, recruiter-safe engineering assessment for a candidate.
        Returns None if user does not exist.
        """
        if not username:
            return None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        # Fetch completed evaluations on active challenges
        evaluations_qs = (
            Evaluation.objects.filter(
                submission__user=user,
                status=Evaluation.Status.COMPLETED,
                submission__challenge__is_active=True,
            )
            .select_related("submission", "submission__challenge")
            .order_by("-submission__score", "-evaluated_at", "-id")
        )

        evaluations_list = list(evaluations_qs)

        # Deduplicate best attempt per challenge
        best_evals_by_challenge: Dict[int, Evaluation] = {}
        for eval_obj in evaluations_list:
            cid = (
                getattr(eval_obj.submission, "challenge_id", None)
                or getattr(getattr(eval_obj.submission, "challenge", None), "id", None)
            )
            if cid is None:
                continue

            if cid not in best_evals_by_challenge:
                best_evals_by_challenge[cid] = eval_obj
            else:
                current_best = best_evals_by_challenge[cid]
                current_score = getattr(current_best.submission, "score", 0) or 0
                new_score = getattr(eval_obj.submission, "score", 0) or 0

                if new_score > current_score:
                    best_evals_by_challenge[cid] = eval_obj
                elif new_score == current_score:
                    cur_time = current_best.evaluated_at or current_best.created_at
                    new_time = eval_obj.evaluated_at or eval_obj.created_at
                    if cur_time and new_time and new_time > cur_time:
                        best_evals_by_challenge[cid] = eval_obj
                    elif cur_time == new_time and eval_obj.id > current_best.id:
                        best_evals_by_challenge[cid] = eval_obj

        selected_evals = list(best_evals_by_challenge.values())

        challenges_attempted = len(selected_evals)
        scores = [getattr(e.submission, "score", 0) or 0 for e in selected_evals]
        challenges_completed = sum(
            1 for e in selected_evals if getattr(e.submission, "status", None) == Submission.Status.PASSED
        )
        total_points = sum(scores)
        average_score = (
            round(total_points / challenges_attempted, 1)
            if challenges_attempted > 0
            else None
        )
        completion_percentage = (
            round((challenges_completed / challenges_attempted) * 100, 1)
            if challenges_attempted > 0
            else 0.0
        )

        # Skill profile calculation
        skill_profile = SkillProfileService().calculate_profile_from_evaluations(selected_evals)
        overall_skill_score = skill_profile.get("overall_score")
        skills = skill_profile.get("skills", {})

        # Achievements
        achievements = AchievementService().get_user_achievements(user)

        # Recent challenge evidence (up to 10 latest evaluations on active challenges)
        recent_evals_qs = (
            Evaluation.objects.filter(
                submission__user=user,
                status=Evaluation.Status.COMPLETED,
                submission__challenge__is_active=True,
            )
            .select_related("submission", "submission__challenge")
            .order_by("-evaluated_at", "-id")[:10]
        )

        challenge_evidence: List[Dict[str, Any]] = []
        for eval_obj in recent_evals_qs:
            challenge = getattr(eval_obj.submission, "challenge", None)
            if not challenge:
                continue

            evaluated_at_str = (
                eval_obj.evaluated_at.isoformat()
                if eval_obj.evaluated_at
                else (eval_obj.created_at.isoformat() if eval_obj.created_at else None)
            )

            challenge_evidence.append({
                "challenge_id": challenge.id,
                "challenge_title": challenge.title,
                "challenge_type": challenge.challenge_type,
                "difficulty": challenge.difficulty,
                "score": getattr(eval_obj.submission, "score", 0) or 0,
                "status": getattr(eval_obj.submission, "status", "COMPLETED"),
                "evaluated_at": evaluated_at_str,
            })

        return {
            "username": user.username,
            "overall_skill_score": overall_skill_score,
            "skills": skills,
            "metrics": {
                "total_points": total_points,
                "challenges_completed": challenges_completed,
                "challenges_attempted": challenges_attempted,
                "average_score": average_score,
                "completion_percentage": completion_percentage,
            },
            "achievements": achievements,
            "challenge_evidence": challenge_evidence,
        }
