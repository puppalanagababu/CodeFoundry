from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.achievement_service import AchievementService
from app.services.skill_profile_service import SkillProfileService


class PublicProfileService:
    """
    Produces a safe, deterministic, read-only developer public profile.
    Aggregates evaluated challenge metrics using the established best-attempt rules.
    """

    def __init__(
        self,
        skill_profile_service: Optional[SkillProfileService] = None,
        achievement_service: Optional[AchievementService] = None,
    ):
        self.skill_profile_service = skill_profile_service or SkillProfileService()
        self.achievement_service = achievement_service or AchievementService()

    def get_public_profile(self, db: Session, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves and aggregates the public profile for the specified username.
        Returns None if user is not found.
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        # 1. Fetch all completed evaluations on active challenges for this user
        evaluations = (
            db.query(Evaluation)
            .join(Submission, Evaluation.submission_id == Submission.id)
            .join(Challenge, Submission.challenge_id == Challenge.id)
            .options(
                joinedload(Evaluation.submission).joinedload(Submission.challenge)
            )
            .filter(
                Submission.user_id == user.id,
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

        # 2. Deduplicate by challenge: select best attempt per active challenge
        best_evals_by_challenge: Dict[int, Evaluation] = {}
        for eval_obj in evaluations:
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

        # 3. Compute Metrics
        challenges_attempted = len(selected_evals)

        if challenges_attempted > 0:
            best_scores = [e.submission.score or 0 for e in selected_evals if e.submission]
            total_points = sum(best_scores)
            challenges_completed = sum(
                1 for e in selected_evals if e.submission and e.submission.status == SubmissionStatus.PASSED.value
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
        recent_evals = (
            db.query(Evaluation)
            .join(Submission, Evaluation.submission_id == Submission.id)
            .join(Challenge, Submission.challenge_id == Challenge.id)
            .options(
                joinedload(Evaluation.submission).joinedload(Submission.challenge)
            )
            .filter(
                Submission.user_id == user.id,
                Evaluation.status == EvaluationStatus.COMPLETED.value,
                Challenge.is_active == True,
            )
            .order_by(Evaluation.evaluated_at.desc(), Evaluation.id.desc())
            .limit(5)
            .all()
        )

        recent_activity: List[Dict[str, Any]] = []
        for eval_obj in recent_evals:
            sub = eval_obj.submission
            if not sub or not sub.challenge:
                continue

            evaluated_at_str = (
                eval_obj.evaluated_at.isoformat()
                if eval_obj.evaluated_at
                else (eval_obj.created_at.isoformat() if eval_obj.created_at else None)
            )

            recent_activity.append({
                "challenge_id": sub.challenge.id,
                "challenge_title": sub.challenge.title,
                "challenge_type": sub.challenge.challenge_type,
                "difficulty": sub.challenge.difficulty,
                "score": sub.score or 0,
                "status": sub.status or "COMPLETED",
                "evaluated_at": evaluated_at_str,
            })

        # 5. Fetch earned achievements via AchievementService
        earned_achievements = self.achievement_service.get_user_achievements(db, user.id)

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
