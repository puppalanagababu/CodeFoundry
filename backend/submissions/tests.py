from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import serializers, status
from rest_framework.test import APIRequestFactory, force_authenticate
from challenges.models import Challenge
from evaluations.models import Evaluation
from submissions.models import Submission
from submissions.serializers import SubmissionCreateSerializer
from submissions.views import SubmissionCreateView

User = get_user_model()


class SubmissionAPITests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = SubmissionCreateView.as_view()
        self.user = User(id=1, username="teststudent")
        self.other_user = User(id=2, username="attacker")
        self.challenge = Challenge(id=1, title="Test Challenge", points=100)

    def test_1_unauthenticated_request_is_rejected(self):
        request = self.factory.post(
            "/api/submissions/",
            {"challenge": 1, "code": "print(1)"},
            format="json",
        )
        response = self.view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("submissions.views.EvaluationService.evaluate")
    @patch("submissions.serializers.SubmissionCreateSerializer.save")
    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_2_authenticated_user_can_submit_valid_code(
        self, mock_pk_to_internal, mock_serializer_save, mock_evaluate
    ):
        mock_pk_to_internal.return_value = self.challenge

        submission = Submission(
            id=10,
            user=self.user,
            challenge=self.challenge,
            code="print(2 + 3)",
            language="Python",
            status=Submission.Status.PASSED,
            score=100,
        )
        submission.challenge_id = 1
        submission.refresh_from_db = MagicMock()
        mock_serializer_save.return_value = submission

        mock_evaluation = Evaluation(
            status=Evaluation.Status.COMPLETED,
            score=100,
            tests_total=1,
            tests_passed=1,
            tests_failed=0,
            stdout="5\n",
            stderr="",
            execution_time=0.28,
            memory_used=0.0,
        )
        mock_evaluate.return_value = mock_evaluation

        request = self.factory.post(
            "/api/submissions/",
            {"challenge": 1, "code": "print(2 + 3)", "language": "Python"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["submission_id"], 10)
        self.assertEqual(response.data["challenge"], 1)
        self.assertEqual(response.data["status"], "PASSED")
        self.assertEqual(response.data["score"], 100)
        self.assertEqual(
            response.data["evaluation"],
            {
                "status": "COMPLETED",
                "score": 100,
                "tests_total": 1,
                "tests_passed": 1,
                "tests_failed": 0,
                "stdout": "5\n",
                "stderr": "",
                "execution_time": 0.28,
                "memory_used": 0.0,
            },
        )

    @patch("submissions.views.EvaluationService.evaluate")
    @patch("submissions.serializers.SubmissionCreateSerializer.save")
    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_3_user_is_automatically_assigned_from_request_user(
        self, mock_pk_to_internal, mock_serializer_save, mock_evaluate
    ):
        mock_pk_to_internal.return_value = self.challenge

        submission = Submission(
            id=11,
            user=self.user,
            challenge=self.challenge,
            code="print('Hello')",
        )
        submission.challenge_id = 1
        mock_serializer_save.return_value = submission
        mock_evaluate.return_value = Evaluation(status=Evaluation.Status.COMPLETED)

        request = self.factory.post(
            "/api/submissions/",
            {"challenge": 1, "code": "print('Hello')"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_serializer_save.assert_called_once_with(user=self.user)

    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_4_client_cannot_choose_another_user(self, mock_pk_to_internal):
        mock_pk_to_internal.return_value = self.challenge

        serializer = SubmissionCreateSerializer(
            data={
                "challenge": 1,
                "code": "print(1)",
                "user": self.other_user.id,
                "status": "PASSED",
                "score": 999,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertNotIn("user", serializer.validated_data)
        self.assertNotIn("status", serializer.validated_data)
        self.assertNotIn("score", serializer.validated_data)

    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_5_invalid_challenge_is_rejected(self, mock_pk_to_internal):
        mock_pk_to_internal.side_effect = serializers.ValidationError("Invalid pk \"9999\" - object does not exist.")

        request = self.factory.post(
            "/api/submissions/",
            {"challenge": 9999, "code": "print(1)"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("challenge", response.data)

    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_6_missing_code_is_rejected(self, mock_pk_to_internal):
        mock_pk_to_internal.return_value = self.challenge

        request = self.factory.post(
            "/api/submissions/",
            {"challenge": 1},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)


    @patch("submissions.views.EvaluationService.evaluate")
    @patch("submissions.serializers.SubmissionCreateSerializer.save")
    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_7_evaluation_service_is_called_after_submission_creation(
        self, mock_pk_to_internal, mock_serializer_save, mock_evaluate
    ):
        mock_pk_to_internal.return_value = self.challenge

        submission = Submission(
            id=12,
            user=self.user,
            challenge=self.challenge,
            code="print(1)",
        )
        submission.challenge_id = 1
        mock_serializer_save.return_value = submission
        mock_evaluate.return_value = Evaluation(status=Evaluation.Status.COMPLETED)

        request = self.factory.post(
            "/api/submissions/",
            {"challenge": 1, "code": "print(1)"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_evaluate.assert_called_once_with(submission)

