from collections import defaultdict
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge
from app.models.evaluation import Achievement, Evaluation, EvaluationStatus, UserAchievement
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.achievement_service import AchievementService
from app.services.skill_profile_service import SkillProfileService

logger = logging.getLogger("app.services.recruiter")


class RecruiterDashboardService:
    """
    Service layer providing authorized recruiters with safe, deterministic
    candidate engineering assessments derived from evaluated challenges.
    """

    def __init__(
        self,
        skill_profile_service: Optional[SkillProfileService] = None,
        achievement_service: Optional[AchievementService] = None,
    ):
        self.skill_profile_service = skill_profile_service or SkillProfileService()
        self.achievement_service = achievement_service or AchievementService()

    def get_candidates(
        self,
        db: Session,
        search: str = "",
        min_skill_score: Optional[int] = None,
        challenge_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves candidate summaries for developers who have completed evaluations.
        Applies filtering, best-attempt deduplication, deterministic sorting, and privacy data minimization.
        """
        # 1. Fetch all completed evaluations on active challenges in a single bulk query
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
                Submission.score.desc(),
                Evaluation.evaluated_at.desc(),
                Evaluation.id.desc(),
            )
            .all()
        )

        if not evaluations:
            return []

        # 2. Bulk load achievement counts per user in a single query
        ach_counts_query = (
            db.query(UserAchievement.user_id, func.count(UserAchievement.id))
            .join(Achievement, UserAchievement.achievement_id == Achievement.id)
            .filter(Achievement.is_active == True)
            .group_by(UserAchievement.user_id)
            .all()
        )
        achievement_counts = {u_id: count for u_id, count in ach_counts_query}

        # 3. Group evaluations by user
        evals_by_user: Dict[int, List[Evaluation]] = defaultdict(list)
        users_by_id: Dict[int, User] = {}

        for eval_obj in evaluations:
            sub = eval_obj.submission
            if not sub or not sub.user_id:
                continue
            u_id = sub.user_id
            users_by_id[u_id] = sub.user
            evals_by_user[u_id].append(eval_obj)

        candidates: List[Dict[str, Any]] = []

        # 4. Process each candidate with best-attempt deduplication
        for user_id, user_evals in evals_by_user.items():
            user = users_by_id[user_id]

            # Best-attempt deduplication per challenge
            best_evals_by_challenge: Dict[int, Evaluation] = {}
            for eval_obj in user_evals:
                cid = eval_obj.submission.challenge_id if eval_obj.submission else None
                if cid is None:
                    continue

                if cid not in best_evals_by_challenge:
                    best_evals_by_challenge[cid] = eval_obj
                else:
                    current_best = best_evals_by_challenge[cid]
                    current_score = current_best.submission.score if current_best.submission else 0
                    new_score = eval_obj.submission.score if eval_obj.submission else 0

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
            scores = [e.submission.score or 0 for e in selected_evals if e.submission]
            challenges_completed = sum(
                1 for e in selected_evals if e.submission and e.submission.status == SubmissionStatus.PASSED.value
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

            skill_profile = self.skill_profile_service.calculate_profile_from_evaluations(selected_evals)
            overall_skill_score = skill_profile.get("overall_score")
            ach_count = achievement_counts.get(user_id, 0)

            # Check challenge types attempted
            attempted_types = {
                e.submission.challenge.challenge_type
                for e in selected_evals
                if e.submission and e.submission.challenge
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

    def get_candidate_detail(self, db: Session, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed, recruiter-safe engineering assessment for a candidate.
        Returns None if user does not exist.
        """
        if not username:
            return None

        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        # Fetch completed evaluations on active challenges
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
                Submission.score.desc(),
                Evaluation.evaluated_at.desc(),
                Evaluation.id.desc(),
            )
            .all()
        )

        # Deduplicate best attempt per challenge
        best_evals_by_challenge: Dict[int, Evaluation] = {}
        for eval_obj in evaluations:
            cid = eval_obj.submission.challenge_id if eval_obj.submission else None
            if cid is None:
                continue

            if cid not in best_evals_by_challenge:
                best_evals_by_challenge[cid] = eval_obj
            else:
                current_best = best_evals_by_challenge[cid]
                current_score = current_best.submission.score if current_best.submission else 0
                new_score = eval_obj.submission.score if eval_obj.submission else 0

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
        scores = [e.submission.score or 0 for e in selected_evals if e.submission]
        challenges_completed = sum(
            1 for e in selected_evals if e.submission and e.submission.status == SubmissionStatus.PASSED.value
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
        skill_profile = self.skill_profile_service.calculate_profile_from_evaluations(selected_evals)
        overall_skill_score = skill_profile.get("overall_score")
        skills = skill_profile.get("skills", {})

        # Achievements
        achievements = self.achievement_service.get_user_achievements(db, user.id)

        # Recent challenge evidence (up to 10 latest evaluations on active challenges)
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
            .limit(10)
            .all()
        )

        challenge_evidence: List[Dict[str, Any]] = []
        for eval_obj in recent_evals:
            sub = eval_obj.submission
            if not sub or not sub.challenge:
                continue

            evaluated_at_str = (
                eval_obj.evaluated_at.isoformat()
                if eval_obj.evaluated_at
                else (eval_obj.created_at.isoformat() if eval_obj.created_at else None)
            )

            challenge_evidence.append({
                "challenge_id": sub.challenge.id,
                "challenge_title": sub.challenge.title,
                "challenge_type": sub.challenge.challenge_type,
                "difficulty": sub.challenge.difficulty,
                "score": sub.score or 0,
                "status": sub.status or "COMPLETED",
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

    def compare_candidates(self, db: Session, usernames: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves detailed assessments for 2 to 5 candidates for side-by-side comparison.
        """
        results: List[Dict[str, Any]] = []
        for uname in usernames:
            detail = self.get_candidate_detail(db, uname.strip())
            if detail:
                results.append(detail)
        return results
