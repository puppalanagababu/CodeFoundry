from django.utils import timezone
from execution.services import ExecutionService
from submissions.models import Submission
from .models import Evaluation


class EvaluationService:
    def __init__(self, execution_service=None):
        self.execution_service = execution_service or ExecutionService()

    def evaluate(self, submission: Submission) -> Evaluation:
        evaluation, _ = Evaluation.objects.get_or_create(submission=submission)

        evaluation.status = Evaluation.Status.RUNNING
        evaluation.save()

        submission.status = Submission.Status.RUNNING
        submission.save()

        try:
            result = self.execution_service.execute(
                code=submission.code,
                language=submission.language,
            )

            is_success = result.exit_code == 0
            points = submission.challenge.points if is_success else 0
            tests_total = 1
            tests_passed = 1 if is_success else 0
            tests_failed = 0 if is_success else 1

            # Update Evaluation
            evaluation.status = Evaluation.Status.COMPLETED
            evaluation.score = points
            evaluation.tests_total = tests_total
            evaluation.tests_passed = tests_passed
            evaluation.tests_failed = tests_failed
            evaluation.execution_time = result.execution_time
            evaluation.memory_used = result.memory_used
            evaluation.stdout = result.stdout
            evaluation.stderr = result.stderr
            evaluation.evaluated_at = timezone.now()
            evaluation.save()

            # Update Submission
            submission.status = (
                Submission.Status.PASSED if is_success else Submission.Status.FAILED
            )
            submission.score = points
            submission.execution_time = result.execution_time
            submission.memory_used = result.memory_used
            submission.test_results = {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
                "memory_used": result.memory_used,
                "tests_total": tests_total,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
            }
            submission.save()

        except Exception as e:
            evaluation.status = Evaluation.Status.FAILED
            evaluation.stderr = f"Evaluation error: {str(e)}"
            evaluation.evaluated_at = timezone.now()
            evaluation.save()

            submission.status = Submission.Status.ERROR
            submission.save()

        return evaluation
