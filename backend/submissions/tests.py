from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import serializers, status
from rest_framework.test import APIRequestFactory, force_authenticate
from challenges.models import Challenge
from evaluations.models import Evaluation
from submissions.models import Submission
from submissions.serializers import SubmissionCreateSerializer
from submissions.views import SubmissionCreateView, SubmissionDetailView


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

    @patch("submissions.views.evaluate_submission.delay")
    @patch("submissions.serializers.SubmissionCreateSerializer.save")
    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_2_authenticated_user_can_submit_valid_code(
        self, mock_pk_to_internal, mock_serializer_save, mock_delay
    ):
        mock_pk_to_internal.return_value = self.challenge

        submission = Submission(
            id=10,
            user=self.user,
            challenge=self.challenge,
            code="print(2 + 3)",
            language="Python",
            status=Submission.Status.PENDING,
            score=0,
        )
        submission.challenge_id = 1
        mock_serializer_save.return_value = submission

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
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.data["score"], 0)
        self.assertEqual(
            response.data["message"], "Submission queued for evaluation."
        )
        mock_delay.assert_called_once_with(10)

    @patch("submissions.views.evaluate_submission.delay")
    @patch("submissions.serializers.SubmissionCreateSerializer.save")
    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_3_user_is_automatically_assigned_from_request_user(
        self, mock_pk_to_internal, mock_serializer_save, mock_delay
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

    @patch("submissions.views.evaluate_submission.delay")
    @patch("submissions.serializers.SubmissionCreateSerializer.save")
    @patch("rest_framework.relations.PrimaryKeyRelatedField.to_internal_value")
    def test_7_celery_task_is_queued_after_submission_creation(
        self, mock_pk_to_internal, mock_serializer_save, mock_delay
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

        request = self.factory.post(
            "/api/submissions/",
            {"challenge": 1, "code": "print(1)"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_delay.assert_called_once_with(12)


class SubmissionDetailAPITests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = SubmissionDetailView.as_view()
        self.user = User(id=1, username="teststudent")
        self.other_user = User(id=2, username="attacker")
        self.challenge = Challenge(id=1, title="Test Challenge", points=100)

    def test_unauthenticated_user_receives_401(self):
        request = self.factory.get("/api/submissions/10/")
        response = self.view(request, pk=10)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("submissions.views.get_object_or_404")
    def test_authenticated_user_can_retrieve_their_own_submission(
        self, mock_get_object_or_404
    ):
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
        evaluation = Evaluation(
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
        submission.evaluation = evaluation
        mock_get_object_or_404.return_value = submission

        request = self.factory.get("/api/submissions/10/")
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=10)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
                "test_results": [],
            },
        )


    @patch("submissions.views.get_object_or_404")
    def test_user_cannot_retrieve_another_users_submission(
        self, mock_get_object_or_404
    ):
        from django.http import Http404

        mock_get_object_or_404.side_effect = Http404

        request = self.factory.get("/api/submissions/99/")
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=99)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("submissions.views.get_object_or_404")
    def test_nonexistent_submission_returns_404(
        self, mock_get_object_or_404
    ):
        from django.http import Http404

        mock_get_object_or_404.side_effect = Http404

        request = self.factory.get("/api/submissions/9999/")
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=9999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("submissions.views.get_object_or_404")
    def test_pending_submission_returns_null_evaluation(
        self, mock_get_object_or_404
    ):
        submission = Submission(
            id=15,
            user=self.user,
            challenge=self.challenge,
            code="print(1)",
            language="Python",
            status=Submission.Status.PENDING,
            score=0,
        )
        submission.challenge_id = 1
        # No evaluation created yet
        submission.evaluation = None
        mock_get_object_or_404.return_value = submission

        request = self.factory.get("/api/submissions/15/")
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=15)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["submission_id"], 15)
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.data["score"], 0)
        self.assertIsNone(response.data["evaluation"])

    @patch("submissions.views.get_object_or_404")
    def test_failed_submission_returns_correct_details(
        self, mock_get_object_or_404
    ):
        submission = Submission(
            id=20,
            user=self.user,
            challenge=self.challenge,
            code="print(undefined)",
            language="Python",
            status=Submission.Status.FAILED,
            score=0,
        )
        submission.challenge_id = 1
        evaluation = Evaluation(
            status=Evaluation.Status.COMPLETED,
            score=0,
            tests_total=1,
            tests_passed=0,
            tests_failed=1,
            stdout="",
            stderr="NameError: name 'undefined' is not defined",
            execution_time=0.18,
            memory_used=0.0,
        )
        submission.evaluation = evaluation
        mock_get_object_or_404.return_value = submission

        request = self.factory.get("/api/submissions/20/")
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=20)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["submission_id"], 20)
        self.assertEqual(response.data["status"], "FAILED")
        self.assertEqual(response.data["score"], 0)
        self.assertEqual(response.data["evaluation"]["status"], "COMPLETED")
        self.assertEqual(response.data["evaluation"]["tests_failed"], 1)

    @patch("submissions.views.get_object_or_404")
    def test_hidden_test_input_and_expected_output_not_exposed(
        self, mock_get_object_or_404
    ):
        submission = Submission(
            id=30,
            user=self.user,
            challenge=self.challenge,
            code="print(1)",
            language="Python",
            status=Submission.Status.PASSED,
            score=100,
        )
        submission.challenge_id = 1
        evaluation = Evaluation(
            status=Evaluation.Status.COMPLETED,
            score=100,
            tests_total=2,
            tests_passed=2,
            tests_failed=0,
            execution_time=0.4,
            memory_used=0.0,
            test_results=[
                {
                    "test_case_id": 1,
                    "name": "Public Case",
                    "passed": True,
                    "points": 50,
                    "max_points": 50,
                    "is_hidden": False,
                    "input_data": "2 3",
                    "expected_output": "5",
                    "stdout": "5\n",
                    "stderr": "",
                },
                {
                    "test_case_id": 2,
                    "name": "Secret Case",
                    "passed": True,
                    "points": 50,
                    "max_points": 50,
                    "is_hidden": True,
                    "input_data": "100 200",
                    "expected_output": "300",
                    "stdout": "300\n",
                    "stderr": "",
                },
            ],
        )
        submission.evaluation = evaluation
        mock_get_object_or_404.return_value = submission

        request = self.factory.get("/api/submissions/30/")
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=30)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["evaluation"]["test_results"]
        self.assertEqual(len(results), 2)

        # Public case should expose inputs/expected output
        self.assertEqual(results[0]["name"], "Public Case")
        self.assertEqual(results[0]["input_data"], "2 3")
        self.assertEqual(results[0]["expected_output"], "5")

        # Hidden case must NOT expose inputs/expected output
        self.assertEqual(results[1]["name"], "Secret Case")
        self.assertTrue(results[1]["is_hidden"])
        self.assertNotIn("input_data", results[1])
        self.assertNotIn("expected_output", results[1])
        self.assertNotIn("actual_output", results[1])


class SubmissionHistoryAPITests(SimpleTestCase):
    def setUp(self):
        from .views import (
            BestSubmissionsView,
            ChallengeSubmissionHistoryView,
            SubmissionListCreateView,
        )

        self.factory = APIRequestFactory()
        self.list_view = SubmissionListCreateView.as_view()
        self.best_view = BestSubmissionsView.as_view()
        self.ch_history_view = ChallengeSubmissionHistoryView.as_view()

        self.user_a = User(id=1, username="student_a")
        self.user_b = User(id=2, username="student_b")
        self.challenge_1 = Challenge(id=1, title="Add Two Numbers", slug="add-two-numbers", points=100)

        self.sub_1 = Submission(
            id=101,
            user=self.user_a,
            challenge=self.challenge_1,
            code="secret_code_a_1",
            language="Python",
            status="PASSED",
            score=100,
        )
        self.sub_1.challenge = self.challenge_1
        self.sub_1.challenge_id = 1

    def test_1_unauthenticated_user_cannot_list_submissions(self):
        request = self.factory.get("/api/submissions/")
        response = self.list_view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("submissions.models.Submission.objects.filter")
    def test_2_authenticated_user_can_list_own_submissions_paginated(
        self, mock_filter
    ):
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [self.sub_1]
        mock_qs.count.return_value = 1
        mock_qs.__len__.return_value = 1
        mock_qs.__getitem__.return_value = [self.sub_1]
        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/submissions/")
        force_authenticate(request, user=self.user_a)
        response = self.list_view(request)

        mock_filter.assert_called_once_with(user=self.user_a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        item = response.data["results"][0]
        self.assertEqual(item["id"], 101)
        self.assertEqual(item["challenge"], 1)
        self.assertEqual(item["challenge_title"], "Add Two Numbers")
        self.assertEqual(item["status"], "PASSED")
        self.assertEqual(item["score"], 100)
        # Verify source code is NOT exposed
        self.assertNotIn("code", item)

    @patch("submissions.models.Submission.objects.filter")
    def test_3_challenge_and_status_filters(self, mock_filter):
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = [self.sub_1]
        mock_qs.count.return_value = 1
        mock_qs.__len__.return_value = 1
        mock_qs.__getitem__.return_value = [self.sub_1]
        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/submissions/?challenge=1&status=PASSED")
        force_authenticate(request, user=self.user_a)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_4_invalid_status_filter_returns_400(self):
        request = self.factory.get("/api/submissions/?status=INVALID_STATUS")
        force_authenticate(request, user=self.user_a)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("submissions.models.Submission.objects.filter")
    def test_5_best_submissions_scoped_to_user(self, mock_filter):
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.values_list.return_value.distinct.return_value.order_by.return_value = [1]

        ch_qs = MagicMock()
        ch_qs.order_by.return_value = ch_qs
        ch_qs.first.return_value = self.sub_1
        ch_qs.aggregate.return_value = {"score__max": 100}
        ch_qs.count.return_value = 3
        mock_qs.filter.return_value = ch_qs

        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/submissions/best/")
        force_authenticate(request, user=self.user_a)
        response = self.best_view(request)

        mock_filter.assert_called_once_with(user=self.user_a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        best_item = response.data["results"][0]
        self.assertEqual(best_item["challenge"], 1)
        self.assertEqual(best_item["best_score"], 100)
        self.assertEqual(best_item["attempts"], 3)
        self.assertEqual(best_item["latest_status"], "PASSED")

    @patch("submissions.views.get_object_or_404")
    @patch("submissions.models.Submission.objects.filter")
    def test_6_challenge_specific_history(self, mock_filter, mock_get_404):
        mock_get_404.return_value = self.challenge_1
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [self.sub_1]
        mock_qs.count.return_value = 1
        mock_qs.__len__.return_value = 1
        mock_qs.__getitem__.return_value = [self.sub_1]
        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/challenges/1/submissions/")
        force_authenticate(request, user=self.user_a)
        response = self.ch_history_view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_filter.assert_called_once_with(user=self.user_a, challenge=self.challenge_1)






