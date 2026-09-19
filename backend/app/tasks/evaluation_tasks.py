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
    logger.info("Received evaluate_submission task for submission ID: %s", submission_id)

    with get_db_context() as db:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error("Submission with ID %s does not exist.", submission_id)
            return {
                "error": f"Submission with ID {submission_id} not found.",
                "submission_id": submission_id,
            }

        try:
            evaluation_service = EvaluationService()
            evaluation = evaluation_service.evaluate(db, submission)

            logger.info(
                "Evaluation completed for submission %s: status=%s, score=%s",
                submission.id,
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
            logger.exception("Task evaluation failed for submission ID %s: %s", submission_id, exc)
            submission.status = SubmissionStatus.ERROR.value
            db.commit()
            return {
                "error": str(exc),
                "submission_id": submission_id,
                "status": SubmissionStatus.ERROR.value,
            }
