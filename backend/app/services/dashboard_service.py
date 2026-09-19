from typing import Any, Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge, Difficulty
from app.models.submission import Submission, SubmissionStatus


class DashboardService:
    """
    Computes developer dashboard analytics, progress, and recent submission activity.
    Uses efficient aggregate and joined queries to avoid N+1 queries.
    """

    def get_dashboard(self, db: Session, user_id: int) -> Dict[str, Any]:
        user_subs_query = db.query(Submission).filter(Submission.user_id == user_id)

        # Overview calculations
        total_submissions = user_subs_query.count()

        challenges_attempted = (
            db.query(func.count(func.distinct(Submission.challenge_id)))
            .filter(Submission.user_id == user_id)
            .scalar()
            or 0
        )

        challenges_passed = (
            db.query(func.count(func.distinct(Submission.challenge_id)))
            .filter(
                Submission.user_id == user_id,
                Submission.status == SubmissionStatus.PASSED.value,
            )
            .scalar()
            or 0
        )

        avg_score_agg = (
            db.query(func.avg(Submission.score))
            .filter(Submission.user_id == user_id)
            .scalar()
        )
        average_score = round(avg_score_agg) if avg_score_agg is not None else 0

        # Recent Submissions (latest 5)
        recent_subs = (
            db.query(Submission)
            .options(joinedload(Submission.challenge))
            .filter(Submission.user_id == user_id)
            .order_by(Submission.submitted_at.desc(), Submission.id.desc())
            .limit(5)
            .all()
        )

        recent_submissions: List[Dict[str, Any]] = []
        for sub in recent_subs:
            recent_submissions.append(
                {
                    "id": sub.id,
                    "challenge": sub.challenge_id,
                    "challenge_title": sub.challenge.title if sub.challenge else "",
                    "status": sub.status,
                    "score": sub.score,
                    "language": sub.language,
                    "submitted_at": (
                        sub.submitted_at.isoformat()
                        if sub.submitted_at
                        else None
                    ),
                }
            )

        # Difficulty Progress
        difficulty_progress: List[Dict[str, Any]] = []
        for diff in Difficulty:
            diff_val = diff.value

            diff_attempted = (
                db.query(func.count(func.distinct(Submission.challenge_id)))
                .join(Challenge, Submission.challenge_id == Challenge.id)
                .filter(
                    Submission.user_id == user_id,
                    Challenge.difficulty == diff_val,
                )
                .scalar()
                or 0
            )

            diff_passed = (
                db.query(func.count(func.distinct(Submission.challenge_id)))
                .join(Challenge, Submission.challenge_id == Challenge.id)
                .filter(
                    Submission.user_id == user_id,
                    Submission.status == SubmissionStatus.PASSED.value,
                    Challenge.difficulty == diff_val,
                )
                .scalar()
                or 0
            )

            diff_avg = (
                db.query(func.avg(Submission.score))
                .join(Challenge, Submission.challenge_id == Challenge.id)
                .filter(
                    Submission.user_id == user_id,
                    Challenge.difficulty == diff_val,
                )
                .scalar()
            )
            diff_avg_score = round(diff_avg) if diff_avg is not None else 0

            difficulty_progress.append(
                {
                    "difficulty": diff_val,
                    "attempted": diff_attempted,
                    "passed": diff_passed,
                    "average_score": diff_avg_score,
                }
            )

        return {
            "overview": {
                "challenges_attempted": challenges_attempted,
                "challenges_passed": challenges_passed,
                "total_submissions": total_submissions,
                "average_score": average_score,
            },
            "recent_submissions": recent_submissions,
            "difficulty_progress": difficulty_progress,
        }
