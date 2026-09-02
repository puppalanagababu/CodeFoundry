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


from datetime import datetime, timezone as dt_timezone
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

User = get_user_model()


class SkillProfileServiceTests(SimpleTestCase):
    def setUp(self):
        from .skill_profile import SkillProfileService
        self.service = SkillProfileService()
        self.user = User(id=42, username="student_tester", email="student@example.com")
        self.other_user = User(id=99, username="other_student", email="other@example.com")

        self.c1 = Challenge(id=1, title="Challenge 1", slug="chal-1", challenge_type="FEATURE", points=100)
        self.c2 = Challenge(id=2, title="Challenge 2", slug="chal-2", challenge_type="BUG_FIX", points=100)
        self.c3 = Challenge(id=3, title="Challenge 3", slug="chal-3", challenge_type="SECURITY", points=100)

    def _mock_eval(self, challenge, score, skill_breakdown, evaluated_at=None, user=None):
        sub = Submission(
            id=10,
            user=user or self.user,
            challenge=challenge,
            score=score,
        )
        sub.challenge_id = challenge.id
        ev = Evaluation(
            id=20,
            submission=sub,
            status=Evaluation.Status.COMPLETED,
            score=score,
            skill_breakdown=skill_breakdown,
            evaluated_at=evaluated_at or datetime(2026, 9, 2, 12, 0, tzinfo=dt_timezone.utc),
        )
        return ev


    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_1_user_with_no_evaluations(self, mock_filter):
        mock_filter.return_value.select_related.return_value.order_by.return_value = []
        profile = self.service.get_user_profile(self.user)
        self.assertIsNone(profile["overall_score"])
        self.assertEqual(profile["total_evaluations_analyzed"], 0)
        self.assertEqual(len(profile["skills"]), 6)
        self.assertEqual(profile["skills"]["problem_solving"]["status"], "insufficient_data")
        self.assertEqual(profile["skills"]["code_quality"]["status"], "not_measured")

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_2_user_with_only_non_completed_evaluations(self, mock_filter):
        mock_filter.return_value.select_related.return_value.order_by.return_value = []
        profile = self.service.get_user_profile(self.user)
        self.assertIsNone(profile["overall_score"])
        self.assertEqual(profile["total_evaluations_analyzed"], 0)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_3_one_completed_evaluation(self, mock_filter):
        ev = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={
                "scores": {
                    "problem_solving": 100,
                    "debugging": None,
                    "security": None,
                    "performance": 90,
                    "code_quality": None,
                    "testing": None,
                },
                "evidence": {
                    "problem_solving": "functional_tests",
                    "performance": "execution_metrics",
                },
            },
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["total_evaluations_analyzed"], 1)
        self.assertEqual(profile["skills"]["problem_solving"]["score"], 100)
        self.assertEqual(profile["skills"]["problem_solving"]["sample_size"], 1)
        self.assertEqual(profile["skills"]["problem_solving"]["status"], "measured")
        self.assertEqual(profile["skills"]["performance"]["score"], 90)
        self.assertEqual(profile["skills"]["debugging"]["status"], "insufficient_data")
        self.assertEqual(profile["overall_score"], 95)  # round((100 + 90)/2) = 95

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_4_multiple_completed_evaluations_across_different_challenges(self, mock_filter):
        ev1 = self._mock_eval(
            self.c1,
            score=80,
            skill_breakdown={"scores": {"problem_solving": 80, "performance": 80}},
        )
        ev2 = self._mock_eval(
            self.c2,
            score=100,
            skill_breakdown={"scores": {"problem_solving": 100, "debugging": 100, "performance": 90}},
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev1, ev2]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["total_evaluations_analyzed"], 2)
        # problem_solving: (80 + 100)/2 = 90
        self.assertEqual(profile["skills"]["problem_solving"]["score"], 90)
        self.assertEqual(profile["skills"]["problem_solving"]["sample_size"], 2)
        # debugging: 100 (1 sample)
        self.assertEqual(profile["skills"]["debugging"]["score"], 100)
        self.assertEqual(profile["skills"]["debugging"]["sample_size"], 1)
        # performance: (80 + 90)/2 = 85
        self.assertEqual(profile["skills"]["performance"]["score"], 85)
        # overall: round((90 + 100 + 85)/3) = 92
        self.assertEqual(profile["overall_score"], 92)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_5_multiple_attempts_on_same_challenge_deduplicated(self, mock_filter):
        now = datetime(2026, 9, 2, 12, 0, tzinfo=dt_timezone.utc)
        ev_low = self._mock_eval(
            self.c1,
            score=40,
            skill_breakdown={"scores": {"problem_solving": 40, "performance": 40}},
            evaluated_at=datetime(2026, 9, 1, 12, 0, tzinfo=dt_timezone.utc),
        )
        ev_high = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={"scores": {"problem_solving": 100, "performance": 90}},
            evaluated_at=now,
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev_high, ev_low]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["total_evaluations_analyzed"], 1)
        self.assertEqual(profile["skills"]["problem_solving"]["score"], 100)
        self.assertEqual(profile["skills"]["problem_solving"]["sample_size"], 1)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_6_best_attempt_selection_by_highest_score(self, mock_filter):
        now = datetime(2026, 9, 2, 12, 0, tzinfo=dt_timezone.utc)
        ev_high = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={"scores": {"problem_solving": 100}},
            evaluated_at=datetime(2026, 9, 2, 10, 0, tzinfo=dt_timezone.utc),
        )
        ev_low = self._mock_eval(
            self.c1,
            score=60,
            skill_breakdown={"scores": {"problem_solving": 60}},
            evaluated_at=now,
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev_high, ev_low]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["total_evaluations_analyzed"], 1)
        self.assertEqual(profile["skills"]["problem_solving"]["score"], 100)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_7_tie_on_score_selects_newest_evaluated_at(self, mock_filter):
        t1 = datetime(2026, 9, 2, 10, 0, tzinfo=dt_timezone.utc)
        t2 = datetime(2026, 9, 2, 12, 0, tzinfo=dt_timezone.utc)

        ev_older = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={"scores": {"problem_solving": 100, "performance": 70}},
            evaluated_at=t1,
        )
        ev_newer = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={"scores": {"problem_solving": 100, "performance": 95}},
            evaluated_at=t2,
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev_newer, ev_older]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["total_evaluations_analyzed"], 1)
        self.assertEqual(profile["skills"]["performance"]["score"], 95)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_8_null_skill_dimensions_are_ignored(self, mock_filter):
        ev = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={
                "scores": {
                    "problem_solving": 80,
                    "debugging": None,
                    "security": None,
                    "performance": None,
                }
            },
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["skills"]["problem_solving"]["score"], 80)
        self.assertIsNone(profile["skills"]["debugging"]["score"])
        self.assertEqual(profile["skills"]["debugging"]["status"], "insufficient_data")
        self.assertEqual(profile["overall_score"], 80)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_9_mixed_measured_unmeasured_dimensions(self, mock_filter):
        ev = self._mock_eval(
            self.c3,
            score=80,
            skill_breakdown={
                "scores": {
                    "problem_solving": 80,
                    "security": 80,
                    "performance": 90,
                }
            },
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["skills"]["security"]["status"], "measured")
        self.assertEqual(profile["skills"]["security"]["score"], 80)
        self.assertEqual(profile["skills"]["code_quality"]["status"], "not_measured")

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_10_code_quality_and_testing_not_measured(self, mock_filter):
        mock_filter.return_value.select_related.return_value.order_by.return_value = []
        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["skills"]["code_quality"]["status"], "not_measured")
        self.assertEqual(profile["skills"]["testing"]["status"], "not_measured")
        self.assertIsNone(profile["skills"]["code_quality"]["score"])
        self.assertIsNone(profile["skills"]["testing"]["score"])

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_11_insufficient_data_behavior(self, mock_filter):
        ev = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={"scores": {"problem_solving": 100}},
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["skills"]["security"]["status"], "insufficient_data")
        self.assertEqual(profile["skills"]["debugging"]["status"], "insufficient_data")

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_12_overall_score_excludes_null_dimensions(self, mock_filter):
        ev = self._mock_eval(
            self.c1,
            score=80,
            skill_breakdown={
                "scores": {
                    "problem_solving": 70,
                    "performance": 90,
                    "debugging": None,
                    "security": None,
                }
            },
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        profile = self.service.get_user_profile(self.user)
        # Only problem_solving (70) and performance (90) count -> (70+90)/2 = 80
        self.assertEqual(profile["overall_score"], 80)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_13_overall_score_with_no_measured_dimensions_returns_null(self, mock_filter):
        ev = self._mock_eval(
            self.c1,
            score=0,
            skill_breakdown={
                "scores": {
                    "problem_solving": None,
                    "performance": None,
                }
            },
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        profile = self.service.get_user_profile(self.user)
        self.assertIsNone(profile["overall_score"])

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_14_scores_remain_bounded_0_to_100(self, mock_filter):
        ev = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={
                "scores": {
                    "problem_solving": 150,  # malformed overflow
                    "performance": -20,     # malformed underflow
                }
            },
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["skills"]["problem_solving"]["score"], 100)
        self.assertEqual(profile["skills"]["performance"]["score"], 0)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_15_malformed_skill_breakdown_does_not_crash(self, mock_filter):
        ev1 = self._mock_eval(
            self.c1,
            score=50,
            skill_breakdown="not-a-dict",  # invalid JSON
        )
        ev2 = self._mock_eval(
            self.c2,
            score=50,
            skill_breakdown={"scores": "not-a-dict"},
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev1, ev2]

        profile = self.service.get_user_profile(self.user)
        self.assertEqual(profile["total_evaluations_analyzed"], 2)
        self.assertIsNone(profile["overall_score"])

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_16_different_users_evaluations_isolated(self, mock_filter):
        ev_other = self._mock_eval(
            self.c1,
            score=100,
            skill_breakdown={"scores": {"problem_solving": 100}},
            user=self.other_user,
        )

        def side_effect(*args, **kwargs):
            user_arg = kwargs.get("submission__user")
            mock_res = MagicMock()
            if user_arg == self.user:
                mock_res.select_related.return_value.order_by.return_value = []
            else:
                mock_res.select_related.return_value.order_by.return_value = [ev_other]
            return mock_res

        mock_filter.side_effect = side_effect

        profile_user = self.service.get_user_profile(self.user)
        self.assertEqual(profile_user["total_evaluations_analyzed"], 0)
        self.assertIsNone(profile_user["overall_score"])

        profile_other = self.service.get_user_profile(self.other_user)
        self.assertEqual(profile_other["total_evaluations_analyzed"], 1)
        self.assertEqual(profile_other["skills"]["problem_solving"]["score"], 100)


    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_17_all_six_dimensions_always_returned(self, mock_filter):
        mock_filter.return_value.select_related.return_value.order_by.return_value = []
        profile = self.service.get_user_profile(self.user)
        expected_dims = {
            "problem_solving",
            "debugging",
            "security",
            "performance",
            "code_quality",
            "testing",
        }
        self.assertEqual(set(profile["skills"].keys()), expected_dims)
        for dim, data in profile["skills"].items():
            self.assertIn("score", data)
            self.assertIn("sample_size", data)
            self.assertIn("status", data)






