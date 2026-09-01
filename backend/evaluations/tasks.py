import logging
from celery import shared_task
from submissions.models import Submission
from .services import EvaluationService

logger = logging.getLogger(__name__)


@shared_task(name="evaluate_submission")
def evaluate_submission(submission_id: int):
    """
    Asynchronously evaluates a submission by delegating to EvaluationService.
    """
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        logger.error(f"Submission with ID {submission_id} does not exist.")
        return {
            "error": f"Submission with ID {submission_id} not found.",
            "submission_id": submission_id,
        }

    service = EvaluationService()
    evaluation = service.evaluate(submission)

    return {
        "submission_id": submission.id,
        "evaluation_id": getattr(evaluation, "id", None),
        "status": submission.status,
        "score": submission.score,
    }
