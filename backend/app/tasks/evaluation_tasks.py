import logging
from typing import Any, Dict
from app.celery_app import celery_app
from app.database import get_db_context
from app.models.submission import Submission, SubmissionStatus
from app.services.evaluation_service import EvaluationService

logger = logging.getLogger("app.tasks.evaluation")


@celery_app.task(name="evaluate_submission", bind=True)
def evaluate_submission(self, submission_id: int) -> Dict[str, Any]:
    """
    Asynchronously evaluates a submission using standalone SQLAlchemy database sessions.
    Executes test cases in Docker sandbox, calculates scores, skill breakdowns,
    and awards achievements. Runs independently of Django.
    """
    task_id = getattr(getattr(self, "request", None), "id", "sync")
    logger.info("Celery task started: task_id=%s, submission_id=%s", task_id, submission_id)

    with get_db_context() as db:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error("Celery task error: Submission with ID %s does not exist (task_id=%s)", submission_id, task_id)
            return {
                "error": f"Submission with ID {submission_id} not found.",
                "submission_id": submission_id,
            }

        try:
            evaluation_service = EvaluationService()
            evaluation = evaluation_service.evaluate(db, submission)

            logger.info(
                "Celery task completed: task_id=%s, submission_id=%s, evaluation_id=%s, challenge_id=%s, user_id=%s, submission_status=%s, evaluation_status=%s, score=%s",
                task_id,
                submission.id,
                evaluation.id,
                submission.challenge_id,
                submission.user_id,
                submission.status,
                evaluation.status,
                evaluation.score,
            )

            return {
                "submission_id": submission.id,
                "evaluation_id": evaluation.id,
                "status": submission.status,
                "score": submission.score,
            }
        except Exception as exc:
            logger.exception(
                "Celery task evaluation failed: task_id=%s, submission_id=%s, user_id=%s, error=%s",
                task_id,
                submission_id,
                getattr(submission, "user_id", None),
                exc,
            )
            submission.status = SubmissionStatus.ERROR.value
            db.commit()
            return {
                "error": str(exc),
                "submission_id": submission_id,
                "status": SubmissionStatus.ERROR.value,
            }
