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
    def test_repository_submission_evaluation(self, mock_get_or_create, mock_filter):
        from challenges.models import ChallengeFile

        evaluation = Evaluation(submission=self.submission)
        evaluation.save = MagicMock()
        mock_get_or_create.return_value = (evaluation, True)

        mock_filter.return_value.order_by.return_value = [self.tc1]

        cf1 = ChallengeFile(path="app/calculator.py", content="def add(): pass")
        cf2 = ChallengeFile(path="tests/test_calc.py", content="assert True")

        mock_files = MagicMock()
        mock_files.exists.return_value = True
        mock_files.all.return_value = [cf1, cf2]

        with patch.object(Challenge, "files", mock_files):
            self.challenge.entrypoint = "app/calculator.py"
            self.submission.files = {"app/calculator.py": "def add(): print(5)"}

            mock_execution_service = MagicMock(spec=ExecutionService)
            mock_execution_service.execute.return_value = ExecutionResult(
                stdout="5\n", stderr="", exit_code=0, execution_time=0.2, memory_used=10.0
            )

            service = EvaluationService(execution_service=mock_execution_service)
            result_eval = service.evaluate(self.submission)

            self.assertEqual(result_eval.status, Evaluation.Status.COMPLETED)
            self.assertEqual(result_eval.score, 50)
            self.assertEqual(self.submission.status, Submission.Status.PASSED)
            mock_execution_service.execute.assert_called_once_with(
                files={"app/calculator.py": "def add(): print(5)", "tests/test_calc.py": "assert True"},
                entrypoint="app/calculator.py",
                language="Python",
                stdin_data=self.tc1.input_data,
                timeout=5,
            )



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



class SkillScoringServiceTests(SimpleTestCase):

    def setUp(self):
        from .skill_scoring import SkillScoringService
        self.service = SkillScoringService()

    def test_1_normal_challenge_problem_solving(self):
        challenge = Challenge(challenge_type="FEATURE", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=5,
            tests_passed=4,
            tests_failed=1,
            execution_time=0.5,
            memory_used=30.0,
        )
        self.assertEqual(breakdown["scores"]["problem_solving"], 80)
        self.assertEqual(breakdown["evidence"]["problem_solving"], "functional_tests")

    def test_2_bug_fix_challenge_debugging(self):
        challenge = Challenge(challenge_type="BUG_FIX", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=4,
            tests_passed=4,
            tests_failed=0,
            execution_time=0.2,
            memory_used=20.0,
        )
        self.assertEqual(breakdown["scores"]["problem_solving"], 100)
        self.assertEqual(breakdown["scores"]["debugging"], 100)
        self.assertEqual(breakdown["evidence"]["debugging"], "bug_fix_tests")

    def test_3_debugging_challenge_debugging(self):
        challenge = Challenge(challenge_type="DEBUGGING", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=4,
            tests_passed=3,
            tests_failed=1,
            execution_time=0.4,
            memory_used=25.0,
        )
        self.assertEqual(breakdown["scores"]["problem_solving"], 75)
        self.assertEqual(breakdown["scores"]["debugging"], 75)
        self.assertEqual(breakdown["evidence"]["debugging"], "bug_fix_tests")

    def test_4_security_challenge_security(self):
        challenge = Challenge(challenge_type="SECURITY", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=5,
            tests_passed=3,
            tests_failed=2,
            execution_time=0.3,
            memory_used=15.0,
        )
        self.assertEqual(breakdown["scores"]["problem_solving"], 60)
        self.assertEqual(breakdown["scores"]["security"], 60)
        self.assertEqual(breakdown["evidence"]["security"], "security_tests")

    def test_5_non_security_challenge_security_is_null(self):
        challenge = Challenge(challenge_type="FEATURE", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=5,
            tests_passed=5,
            tests_failed=0,
            execution_time=0.2,
            memory_used=10.0,
        )
        self.assertIsNone(breakdown["scores"]["security"])
        self.assertEqual(breakdown["evidence"]["security"], "not_measured")

    def test_6_non_bug_fix_challenge_debugging_is_null(self):
        challenge = Challenge(challenge_type="FEATURE", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=5,
            tests_passed=5,
            tests_failed=0,
            execution_time=0.2,
            memory_used=10.0,
        )
        self.assertIsNone(breakdown["scores"]["debugging"])
        self.assertEqual(breakdown["evidence"]["debugging"], "not_measured")

    def test_7_performance_score_within_range(self):
        challenge = Challenge(challenge_type="PERFORMANCE", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=2,
            tests_passed=2,
            tests_failed=0,
            execution_time=0.5,
            memory_used=50.0,
        )
        perf = breakdown["scores"]["performance"]
        self.assertIsNotNone(perf)
        self.assertTrue(0 <= perf <= 100)
        self.assertEqual(breakdown["evidence"]["performance"], "execution_metrics")

    def test_8_missing_metrics_performance_is_null(self):
        challenge = Challenge(challenge_type="FEATURE", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=2,
            tests_passed=2,
            tests_failed=0,
            execution_time=None,
            memory_used=None,
        )
        self.assertIsNone(breakdown["scores"]["performance"])
        self.assertEqual(breakdown["evidence"]["performance"], "not_measured")

    def test_9_zero_test_cases_problem_solving_is_null(self):
        challenge = Challenge(challenge_type="FEATURE", time_limit=5, memory_limit=256)
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=0,
            tests_passed=0,
            tests_failed=0,
            execution_time=0.0,
            memory_used=0.0,
        )
        self.assertIsNone(breakdown["scores"]["problem_solving"])
        self.assertEqual(breakdown["evidence"]["problem_solving"], "not_measured")

    def test_10_api_serializer_includes_skill_breakdown(self):
        from submissions.serializers import EvaluationSerializer
        breakdown = {
            "scores": {
                "problem_solving": 100,
                "debugging": None,
                "security": None,
                "performance": 95,
                "code_quality": None,
                "testing": None,
            },
            "evidence": {
                "problem_solving": "functional_tests",
                "debugging": "not_measured",
                "security": "not_measured",
                "performance": "execution_metrics",
                "code_quality": "not_measured",
                "testing": "not_measured",
            },
        }
        evaluation = Evaluation(
            id=1,
            status=Evaluation.Status.COMPLETED,
            score=100,
            skill_breakdown=breakdown,
        )
        serializer = EvaluationSerializer(evaluation)
        self.assertIn("skill_breakdown", serializer.data)
        self.assertEqual(serializer.data["skill_breakdown"]["scores"]["problem_solving"], 100)
        self.assertEqual(serializer.data["skill_breakdown"]["scores"]["performance"], 95)

    def test_11_performance_memory_mb_scaling(self):
        challenge = Challenge(challenge_type="PERFORMANCE", time_limit=10, memory_limit=256)
        # 1 test case, time: 1.0s (time_ratio = 1/10 = 0.1, time_score = 0.90)
        # memory: 25.6 MB (mem_ratio = 25.6/256 = 0.10, mem_score = 0.90)
        # combined: 0.7 * 0.90 + 0.3 * 0.90 = 0.90 -> 90%
        breakdown = self.service.calculate_skill_breakdown(
            challenge=challenge,
            tests_total=1,
            tests_passed=1,
            tests_failed=0,
            execution_time=1.0,
            memory_used=25.6,
        )
        self.assertEqual(breakdown["scores"]["performance"], 90)

    def test_12_docker_byte_to_mb_conversion(self):
        memory_bytes = 15728640  # 15 MB in bytes
        converted_mb = round(memory_bytes / (1024 * 1024), 2)
        self.assertEqual(converted_mb, 15.0)





