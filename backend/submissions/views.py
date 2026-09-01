from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from evaluations.services import EvaluationService
from .serializers import SubmissionCreateSerializer


class SubmissionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(user=request.user)

        evaluation_service = EvaluationService()
        evaluation = evaluation_service.evaluate(submission)

        # Refresh submission from DB if persisted
        if hasattr(submission, "refresh_from_db"):
            try:
                submission.refresh_from_db()
            except Exception:
                pass

        response_data = {
            "submission_id": submission.id,
            "challenge": submission.challenge_id if hasattr(submission, "challenge_id") else getattr(submission.challenge, "id", None),
            "status": submission.status,
            "score": submission.score,
            "evaluation": {
                "status": evaluation.status,
                "score": evaluation.score,
                "tests_total": evaluation.tests_total,
                "tests_passed": evaluation.tests_passed,
                "tests_failed": evaluation.tests_failed,
                "stdout": evaluation.stdout,
                "stderr": evaluation.stderr,
                "execution_time": evaluation.execution_time,
                "memory_used": evaluation.memory_used,
            },
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

