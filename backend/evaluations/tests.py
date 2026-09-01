from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from challenges.models import Challenge
from execution.runner import ExecutionResult
from execution.services import ExecutionService
from evaluations.models import Evaluation
from evaluations.services import EvaluationService
from submissions.models import Submission


class EvaluationServiceTests(SimpleTestCase):
    def setUp(self):
        from challenges.models import TestCase

        self.challenge = Challenge(
            id=1,
            title="Two Sum",
            slug="two-sum",
            points=100,
            time_limit=5,
        )

        self.tc1 = TestCase(
            id=1,
            challenge=self.challenge,
            name="Basic Addition",
            input_data="2 3",
            expected_output="5",
            points=50,
            is_active=True,
            is_hidden=False,
        )
        self.tc2 = TestCase(
            id=2,
            challenge=self.challenge,
            name="Large Numbers",
            input_data="100 200",
            expected_output="300",
            points=50,
            is_active=True,
            is_hidden=True,
        )

        self.submission = Submission(
            id=1,
            code="a, b = map(int, input().split())\nprint(a + b)",
            language="Python",
            challenge=self.challenge,
        )
        self.submission.save = MagicMock()

    @patch("evaluations.services.TestCase.objects.filter")
    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_all_test_cases_passing(self, mock_get_or_create, mock_filter):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_filter.return_value.order_by.return_value = [self.tc1, self.tc2]

        mock_execution_service = MagicMock(spec=ExecutionService)
        mock_execution_service.execute.side_effect = [
            ExecutionResult(stdout="5\n", stderr="", exit_code=0, execution_time=0.2, memory_used=10.0),
            ExecutionResult(stdout="300\n", stderr="", exit_code=0, execution_time=0.3, memory_used=12.0),
        ]

        service = EvaluationService(execution_service=mock_execution_service)
        result_eval = service.evaluate(self.submission)

        self.assertEqual(result_eval.status, Evaluation.Status.COMPLETED)
        self.assertEqual(result_eval.score, 100)
        self.assertEqual(result_eval.tests_total, 2)
        self.assertEqual(result_eval.tests_passed, 2)
        self.assertEqual(result_eval.tests_failed, 0)
        self.assertEqual(self.submission.status, Submission.Status.PASSED)
        self.assertEqual(self.submission.score, 100)
        self.assertEqual(len(result_eval.test_results), 2)
        self.assertTrue(result_eval.test_results[0]["passed"])
        self.assertTrue(result_eval.test_results[1]["passed"])

    @patch("evaluations.services.TestCase.objects.filter")
    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_partial_passing_test_cases(self, mock_get_or_create, mock_filter):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_filter.return_value.order_by.return_value = [self.tc1, self.tc2]

        mock_execution_service = MagicMock(spec=ExecutionService)
        mock_execution_service.execute.side_effect = [
            ExecutionResult(stdout="5\n", stderr="", exit_code=0, execution_time=0.2, memory_used=10.0),
            ExecutionResult(stdout="Wrong Output\n", stderr="", exit_code=0, execution_time=0.3, memory_used=12.0),
        ]

        service = EvaluationService(execution_service=mock_execution_service)
        result_eval = service.evaluate(self.submission)

        self.assertEqual(result_eval.status, Evaluation.Status.COMPLETED)
        self.assertEqual(result_eval.score, 50)
        self.assertEqual(result_eval.tests_total, 2)
        self.assertEqual(result_eval.tests_passed, 1)
        self.assertEqual(result_eval.tests_failed, 1)
        self.assertEqual(self.submission.status, Submission.Status.FAILED)
        self.assertEqual(self.submission.score, 50)
        self.assertEqual(len(result_eval.test_results), 2)
        self.assertTrue(result_eval.test_results[0]["passed"])
        self.assertFalse(result_eval.test_results[1]["passed"])

    @patch("evaluations.services.TestCase.objects.filter")
    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_zero_active_test_cases(self, mock_get_or_create, mock_filter):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_filter.return_value.order_by.return_value = []

        mock_execution_service = MagicMock(spec=ExecutionService)
        service = EvaluationService(execution_service=mock_execution_service)
        result_eval = service.evaluate(self.submission)

        self.assertEqual(result_eval.status, Evaluation.Status.FAILED)
        self.assertEqual(result_eval.score, 0)
        self.assertEqual(result_eval.tests_total, 0)
        self.assertEqual(self.submission.status, Submission.Status.FAILED)
        self.assertEqual(self.submission.score, 0)
        mock_execution_service.execute.assert_not_called()

    @patch("evaluations.services.TestCase.objects.filter")
    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_runtime_error_in_test_case(self, mock_get_or_create, mock_filter):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_filter.return_value.order_by.return_value = [self.tc1]

        mock_execution_service = MagicMock(spec=ExecutionService)
        mock_execution_service.execute.return_value = ExecutionResult(
            stdout="",
            stderr="ZeroDivisionError: division by zero",
            exit_code=1,
            execution_time=0.15,
            memory_used=8.0,
        )

        service = EvaluationService(execution_service=mock_execution_service)
        result_eval = service.evaluate(self.submission)

        self.assertEqual(result_eval.status, Evaluation.Status.COMPLETED)
        self.assertEqual(result_eval.score, 0)
        self.assertEqual(result_eval.tests_total, 1)
        self.assertEqual(result_eval.tests_passed, 0)
        self.assertEqual(result_eval.tests_failed, 1)
        self.assertEqual(self.submission.status, Submission.Status.FAILED)
        self.assertEqual(self.submission.score, 0)

    @patch("evaluations.services.TestCase.objects.filter")
    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_unexpected_exception_handles_safely(self, mock_get_or_create, mock_filter):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_filter.side_effect = RuntimeError("Database error")

        service = EvaluationService()
        result_eval = service.evaluate(self.submission)

        self.assertEqual(result_eval.status, Evaluation.Status.FAILED)
        self.assertIn("Database error", result_eval.stderr)
        self.assertEqual(self.submission.status, Submission.Status.ERROR)




class EvaluateSubmissionTaskTests(SimpleTestCase):
    def test_task_registration(self):
        from config.celery import app

        self.assertIn("evaluate_submission", app.tasks)

    @patch("evaluations.services.EvaluationService.evaluate")
    @patch("submissions.models.Submission.objects.get")
    def test_task_evaluates_submission(self, mock_submission_get, mock_evaluate):
        from evaluations.tasks import evaluate_submission

        challenge = Challenge(title="Two Sum", points=100)
        submission = Submission(id=42, code="print(1)", language="Python", challenge=challenge)
        submission.status = Submission.Status.PASSED
        submission.score = 100
        mock_submission_get.return_value = submission

        evaluation = Evaluation(id=10, status=Evaluation.Status.COMPLETED, score=100)
        mock_evaluate.return_value = evaluation

        result = evaluate_submission.apply(args=[42]).get()

        mock_submission_get.assert_called_once_with(id=42)
        mock_evaluate.assert_called_once_with(submission)
        self.assertEqual(
            result,
            {
                "submission_id": 42,
                "evaluation_id": 10,
                "status": "PASSED",
                "score": 100,
            },
        )

    @patch("submissions.models.Submission.objects.get")
    def test_task_handles_missing_submission(self, mock_submission_get):
        from evaluations.tasks import evaluate_submission

        mock_submission_get.side_effect = Submission.DoesNotExist

        result = evaluate_submission(9999)
        self.assertIn("error", result)
        self.assertEqual(result["submission_id"], 9999)



