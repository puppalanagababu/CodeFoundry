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
        self.challenge = Challenge(
            title="Two Sum",
            slug="two-sum",
            points=100,
        )

        self.submission = Submission(
            code="print('Hello World')",
            language="Python",
            challenge=self.challenge,
        )
        self.submission.save = MagicMock()


    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_successful_execution(self, mock_get_or_create):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_execution_service = MagicMock(spec=ExecutionService)
        mock_execution_service.execute.return_value = ExecutionResult(
            stdout="Hello World\n",
            stderr="",
            exit_code=0,
            execution_time=0.25,
            memory_used=12.0,
        )

        service = EvaluationService(execution_service=mock_execution_service)
        result_eval = service.evaluate(self.submission)

        # Verify execution service called with correct arguments
        mock_execution_service.execute.assert_called_once_with(
            code="print('Hello World')",
            language="Python",
        )

        # Verify Evaluation fields
        self.assertEqual(result_eval, evaluation)
        self.assertEqual(evaluation.status, Evaluation.Status.COMPLETED)
        self.assertEqual(evaluation.score, 100)
        self.assertEqual(evaluation.tests_total, 1)
        self.assertEqual(evaluation.tests_passed, 1)
        self.assertEqual(evaluation.tests_failed, 0)
        self.assertEqual(evaluation.stdout, "Hello World\n")
        self.assertEqual(evaluation.stderr, "")
        self.assertEqual(evaluation.execution_time, 0.25)
        self.assertEqual(evaluation.memory_used, 12.0)
        self.assertIsNotNone(evaluation.evaluated_at)

        # Verify Submission fields
        self.assertEqual(self.submission.status, Submission.Status.PASSED)
        self.assertEqual(self.submission.score, 100)
        self.assertEqual(self.submission.execution_time, 0.25)
        self.assertEqual(self.submission.memory_used, 12.0)
        self.assertEqual(
            self.submission.test_results,
            {
                "exit_code": 0,
                "stdout": "Hello World\n",
                "stderr": "",
                "execution_time": 0.25,
                "memory_used": 12.0,
                "tests_total": 1,
                "tests_passed": 1,
                "tests_failed": 0,
            },
        )
        self.assertEqual(self.submission.save.call_count, 2)
        self.assertEqual(evaluation.save.call_count, 2)

    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_failed_execution(self, mock_get_or_create):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

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

        # Verify Evaluation fields
        self.assertEqual(result_eval, evaluation)
        self.assertEqual(evaluation.status, Evaluation.Status.COMPLETED)
        self.assertEqual(evaluation.score, 0)
        self.assertEqual(evaluation.tests_total, 1)
        self.assertEqual(evaluation.tests_passed, 0)
        self.assertEqual(evaluation.tests_failed, 1)
        self.assertEqual(evaluation.stdout, "")
        self.assertEqual(evaluation.stderr, "ZeroDivisionError: division by zero")
        self.assertEqual(evaluation.execution_time, 0.15)
        self.assertEqual(evaluation.memory_used, 8.0)
        self.assertIsNotNone(evaluation.evaluated_at)

        # Verify Submission fields
        self.assertEqual(self.submission.status, Submission.Status.FAILED)
        self.assertEqual(self.submission.score, 0)
        self.assertEqual(self.submission.execution_time, 0.15)
        self.assertEqual(self.submission.memory_used, 8.0)
        self.assertEqual(
            self.submission.test_results,
            {
                "exit_code": 1,
                "stdout": "",
                "stderr": "ZeroDivisionError: division by zero",
                "execution_time": 0.15,
                "memory_used": 8.0,
                "tests_total": 1,
                "tests_passed": 0,
                "tests_failed": 1,
            },
        )

    @patch("evaluations.services.Evaluation.objects.get_or_create")
    def test_unexpected_exception(self, mock_get_or_create):
        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_execution_service = MagicMock(spec=ExecutionService)
        mock_execution_service.execute.side_effect = RuntimeError("Docker daemon unavailable")

        service = EvaluationService(execution_service=mock_execution_service)
        result_eval = service.evaluate(self.submission)

        # Verify Evaluation fields
        self.assertEqual(result_eval, evaluation)
        self.assertEqual(evaluation.status, Evaluation.Status.FAILED)
        self.assertIn("Docker daemon unavailable", evaluation.stderr)
        self.assertIsNotNone(evaluation.evaluated_at)

        # Verify Submission fields
        self.assertEqual(self.submission.status, Submission.Status.ERROR)


