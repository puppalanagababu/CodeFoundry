import logging
from typing import Any, Dict, List
from django.contrib.auth import get_user_model
from challenges.models import Challenge
from submissions.models import Submission
from .models import Achievement, Evaluation, UserAchievement

logger = logging.getLogger(__name__)
User = get_user_model()

SEED_ACHIEVEMENTS = [
    {
        "code": "BUG_SLAYER",
        "name": "Bug Slayer",
        "description": "Passed 3 Bug Fix challenges.",
        "icon": "🐛",
        "requirement_type": Achievement.RequirementType.BUG_FIX_COUNT,
        "requirement_value": 3,
    },
    {
        "code": "SECURITY_HUNTER",
        "name": "Security Hunter",
        "description": "Passed 3 Security challenges.",
        "icon": "🛡️",
        "requirement_type": Achievement.RequirementType.SECURITY_COUNT,
        "requirement_value": 3,
    },
    {
        "code": "PERFORMANCE_ENGINEER",
        "name": "Performance Engineer",
        "description": "Passed 3 Performance challenges.",
        "icon": "⚡",
        "requirement_type": Achievement.RequirementType.PERFORMANCE_COUNT,
        "requirement_value": 3,
    },
    {
        "code": "TEST_MASTER",
        "name": "Test Master",
        "description": "Passed 3 Testing challenges.",
        "icon": "🧪",
        "requirement_type": Achievement.RequirementType.TESTING_COUNT,
        "requirement_value": 3,
    },
    {
        "code": "PERFECT_RUN",
        "name": "Perfect Run",
        "description": "Achieved 100/100 on 5 distinct challenges.",
        "icon": "🎯",
        "requirement_type": Achievement.RequirementType.PERFECT_SCORE_COUNT,
        "requirement_value": 5,
    },
    {
        "code": "DEVFORGE_VETERAN",
        "name": "DevForge Veteran",
        "description": "Completed 10 distinct challenges.",
        "icon": "🎖️",
        "requirement_type": Achievement.RequirementType.TOTAL_COMPLETED_COUNT,
        "requirement_value": 10,
    },
]


def seed_achievements() -> None:
    """
    Seeds initial achievement definitions idempotently.
    """
    for ach_data in SEED_ACHIEVEMENTS:
        Achievement.objects.update_or_create(
            code=ach_data["code"],
            defaults={
                "name": ach_data["name"],
                "description": ach_data["description"],
                "icon": ach_data["icon"],
                "requirement_type": ach_data["requirement_type"],
                "requirement_value": ach_data["requirement_value"],
                "is_active": True,
            },
        )


class AchievementService:
    """
    Deterministic Achievement & Badge Engine for DevForge.
    Evaluates completed challenge evaluations, determines milestone eligibility,
    and automatically awards badges without duplicate awards.
    """

    def award_for_user(self, user: Any) -> List[UserAchievement]:
        """
        Evaluates and awards all earned achievements for a given user.
        Idempotent: Safe to call repeatedly.
        """
        if not user or not getattr(user, "id", None):
            return []

        try:
            # 1. Fetch active achievements
            active_achievements = list(Achievement.objects.filter(is_active=True))
            if not active_achievements:
                return []

            # 2. Fetch completed evaluations on active challenges for this user in a single bulk query
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

            # 3. Deduplicate by challenge: select single best attempt per active challenge
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

            # 4. Calculate metric aggregates across best attempts
            bug_fix_passed = 0
            security_passed = 0
            performance_passed = 0
            testing_passed = 0
            perfect_score_count = 0
            total_completed = 0

            for eval_obj in selected_evals:
                sub = eval_obj.submission
                challenge = getattr(sub, "challenge", None)
                if not challenge:
                    continue

                is_passed = (getattr(sub, "status", None) == Submission.Status.PASSED)
                score = getattr(sub, "score", 0) or 0
                ctype = getattr(challenge, "challenge_type", "")

                if is_passed:
                    total_completed += 1
                    if ctype == Challenge.ChallengeType.BUG_FIX:
                        bug_fix_passed += 1
                    elif ctype == Challenge.ChallengeType.SECURITY:
                        security_passed += 1
                    elif ctype == Challenge.ChallengeType.PERFORMANCE:
                        performance_passed += 1
                    elif ctype == Challenge.ChallengeType.TESTING:
                        testing_passed += 1

                if score == 100:
                    perfect_score_count += 1

            # 5. Evaluate eligibility against active achievement requirements
            awarded: List[UserAchievement] = []

            for ach in active_achievements:
                earned = False
                req_val = ach.requirement_value

                if ach.requirement_type == Achievement.RequirementType.BUG_FIX_COUNT:
                    earned = (bug_fix_passed >= req_val)
                elif ach.requirement_type == Achievement.RequirementType.SECURITY_COUNT:
                    earned = (security_passed >= req_val)
                elif ach.requirement_type == Achievement.RequirementType.PERFORMANCE_COUNT:
                    earned = (performance_passed >= req_val)
                elif ach.requirement_type == Achievement.RequirementType.TESTING_COUNT:
                    earned = (testing_passed >= req_val)
                elif ach.requirement_type == Achievement.RequirementType.PERFECT_SCORE_COUNT:
                    earned = (perfect_score_count >= req_val)
                elif ach.requirement_type == Achievement.RequirementType.TOTAL_COMPLETED_COUNT:
                    earned = (total_completed >= req_val)

                if earned:
                    ua, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=ach,
                    )
                    awarded.append(ua)

            return awarded
        except Exception as e:
            logger.exception("Error in AchievementService.award_for_user: %s", e)
            return []

    def get_user_achievements(self, user: Any) -> List[Dict[str, Any]]:
        """
        Returns serialized list of earned achievements for a given user.
        Sorted deterministically: earned_at DESC, then name ASC.
        """
        if not user or not getattr(user, "id", None):
            return []

        user_achievements_qs = (
            UserAchievement.objects.filter(user=user, achievement__is_active=True)
            .select_related("achievement")
            .order_by("-earned_at", "achievement__name")
        )

        results = []
        for ua in user_achievements_qs:
            ach = ua.achievement
            earned_at_str = ua.earned_at.isoformat() if ua.earned_at else None
            results.append({
                "code": ach.code,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "earned_at": earned_at_str,
            })

        return results
