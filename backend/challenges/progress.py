from collections import defaultdict
from typing import Any, Dict, List
from .models import Challenge
from submissions.models import Submission


class ChallengeProgressService:
    """
    Dynamically calculates student challenge progress and attempt aggregation.
    Avoids N+1 queries by pre-fetching active challenges and user submissions in batch.
    """

    def get_user_progress(self, user: Any) -> Dict[str, Any]:
        if not user or not getattr(user, "is_authenticated", True):
            return self._empty_progress()

        # 1. Fetch all active challenges in a single query
        active_challenges = list(
            Challenge.objects.filter(is_active=True).order_by("-created_at", "-id")
        )

        total_challenges = len(active_challenges)
        if total_challenges == 0:
            return {
                "summary": {
                    "total_challenges": 0,
                    "attempted_challenges": 0,
                    "completed_challenges": 0,
                    "completion_percentage": 0.0,
                },
                "challenges": [],
            }

        # 2. Fetch all user submissions for active challenges in a single query
        user_submissions = (
            Submission.objects.filter(
                user=user,
                challenge__is_active=True,
            )
            .order_by("-submitted_at", "-id")
        )

        # 3. Group submissions by challenge_id in memory
        submissions_by_challenge: Dict[int, List[Submission]] = defaultdict(list)
        for sub in user_submissions:
            challenge_id = (
                getattr(sub, "challenge_id", None)
                or getattr(getattr(sub, "challenge", None), "id", None)
            )
            if challenge_id is not None:
                submissions_by_challenge[challenge_id].append(sub)

        # 4. Compute per-challenge progress
        challenge_progress_list: List[Dict[str, Any]] = []
        attempted_challenges_count = 0
        completed_challenges_count = 0

        for challenge in active_challenges:
            subs = submissions_by_challenge.get(challenge.id, [])
            attempts_count = len(subs)

            if attempts_count == 0:
                status_str = "NOT_ATTEMPTED"
                best_score = None
                latest_attempt_at = None
            else:
                attempted_challenges_count += 1
                has_passed = any(s.status == Submission.Status.PASSED for s in subs)
                if has_passed:
                    status_str = "PASSED"
                    completed_challenges_count += 1
                else:
                    status_str = "FAILED"

                best_score = max(s.score for s in subs)
                latest_sub = subs[0]
                latest_attempt_at = (
                    latest_sub.submitted_at.isoformat()
                    if latest_sub.submitted_at
                    else None
                )

            challenge_progress_list.append(
                {
                    "challenge_id": challenge.id,
                    "title": challenge.title,
                    "difficulty": challenge.difficulty,
                    "challenge_type": challenge.challenge_type,
                    "programming_language": challenge.programming_language,
                    "status": status_str,
                    "best_score": best_score,
                    "attempts_count": attempts_count,
                    "latest_attempt_at": latest_attempt_at,
                    "points": challenge.points,
                }
            )

        # 5. Calculate summary metrics
        completion_percentage = (
            round((completed_challenges_count / total_challenges) * 100, 1)
            if total_challenges > 0
            else 0.0
        )

        return {
            "summary": {
                "total_challenges": total_challenges,
                "attempted_challenges": attempted_challenges_count,
                "completed_challenges": completed_challenges_count,
                "completion_percentage": completion_percentage,
            },
            "challenges": challenge_progress_list,
        }

    def _empty_progress(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_challenges": 0,
                "attempted_challenges": 0,
                "completed_challenges": 0,
                "completion_percentage": 0.0,
            },
            "challenges": [],
        }
