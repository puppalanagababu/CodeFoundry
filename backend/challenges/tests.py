from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from challenges.models import Challenge
from challenges.views import ChallengeDetailView, ChallengeListView

User = get_user_model()


class ChallengeAPITests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.list_view = ChallengeListView.as_view()
        self.detail_view = ChallengeDetailView.as_view()
        self.user = User(id=1, username="teststudent")

        self.active_challenge = Challenge(
            id=1,
            title="Add Two Numbers",
            slug="add-two-numbers",
            description="Write a function to add two numbers.",
            difficulty="BEGINNER",
            challenge_type="BUG_FIX",
            programming_language="Python",
            starter_code="def add(a, b):\n    pass",
            time_limit=5,
            memory_limit=128,
            points=100,
            is_active=True,
        )

        self.inactive_challenge = Challenge(
            id=2,
            title="Hidden Challenge",
            slug="hidden-challenge",
            description="Inactive challenge description.",
            difficulty="ADVANCED",
            challenge_type="SECURITY",
            programming_language="Python",
            starter_code="",
            time_limit=10,
            memory_limit=256,
            points=200,
            is_active=False,
        )

    def test_1_unauthenticated_user_cannot_list_challenges(self):
        request = self.factory.get("/api/challenges/")
        response = self.list_view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("challenges.models.Challenge.objects.filter")
    def test_2_authenticated_user_can_list_active_challenges_paginated(
        self, mock_filter
    ):
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = [self.active_challenge]
        mock_qs.__len__.return_value = 1
        mock_qs.__getitem__.return_value = [self.active_challenge]
        mock_qs.count.return_value = 1
        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/challenges/")
        force_authenticate(request, user=self.user)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Add Two Numbers")
        self.assertNotIn("starter_code", response.data["results"][0])

    @patch("challenges.models.Challenge.objects.filter")
    def test_3_search_by_title_or_slug_or_description(self, mock_filter):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = [self.active_challenge]
        mock_qs.count.return_value = 1
        mock_qs.__len__.return_value = 1
        mock_qs.__getitem__.return_value = [self.active_challenge]
        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/challenges/?search=numbers")
        force_authenticate(request, user=self.user)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    @patch("challenges.models.Challenge.objects.filter")
    def test_4_difficulty_filter(self, mock_filter):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = [self.active_challenge]
        mock_qs.count.return_value = 1
        mock_qs.__len__.return_value = 1
        mock_qs.__getitem__.return_value = [self.active_challenge]
        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/challenges/?difficulty=BEGINNER")
        force_authenticate(request, user=self.user)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_5_invalid_difficulty_returns_400(self):
        request = self.factory.get("/api/challenges/?difficulty=INVALID_LEVEL")
        force_authenticate(request, user=self.user)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_6_invalid_challenge_type_returns_400(self):
        request = self.factory.get("/api/challenges/?challenge_type=NOT_A_TYPE")
        force_authenticate(request, user=self.user)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("challenges.views.get_object_or_404")
    def test_7_authenticated_user_can_retrieve_active_challenge_detail(
        self, mock_get_object_or_404
    ):
        mock_get_object_or_404.return_value = self.active_challenge

        request = self.factory.get("/api/challenges/1/")
        force_authenticate(request, user=self.user)
        response = self.detail_view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["title"], "Add Two Numbers")
        self.assertEqual(response.data["slug"], "add-two-numbers")
        self.assertEqual(
            response.data["starter_code"], "def add(a, b):\n    pass"
        )
        self.assertEqual(response.data["time_limit"], 5)
        self.assertEqual(response.data["memory_limit"], 128)
        self.assertEqual(response.data["points"], 100)

    def test_8_unauthenticated_user_cannot_retrieve_challenge_detail(self):
        request = self.factory.get("/api/challenges/1/")
        response = self.detail_view(request, pk=1)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("challenges.views.get_object_or_404")
    def test_9_inactive_challenge_detail_returns_404(
        self, mock_get_object_or_404
    ):
        from django.http import Http404

        mock_get_object_or_404.side_effect = Http404

        request = self.factory.get("/api/challenges/2/")
        force_authenticate(request, user=self.user)
        response = self.detail_view(request, pk=2)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("challenges.views.get_object_or_404")
    def test_10_nonexistent_challenge_returns_404(
        self, mock_get_object_or_404
    ):
        from django.http import Http404

        mock_get_object_or_404.side_effect = Http404

        request = self.factory.get("/api/challenges/9999/")
        force_authenticate(request, user=self.user)
        response = self.detail_view(request, pk=9999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)




class TestCaseModelTests(SimpleTestCase):
    def test_testcase_creation_and_fields(self):
        from challenges.models import TestCase

        challenge = Challenge(id=1, title="Two Sum", points=100)
        tc = TestCase(
            id=1,
            challenge=challenge,
            name="Basic Addition",
            input_data="2 3",
            expected_output="5",
            is_hidden=False,
            points=20,
            is_active=True,
        )
        self.assertEqual(tc.challenge, challenge)
        self.assertEqual(tc.name, "Basic Addition")
        self.assertEqual(tc.input_data, "2 3")
        self.assertEqual(tc.expected_output, "5")
        self.assertFalse(tc.is_hidden)
        self.assertEqual(tc.points, 20)
        self.assertTrue(tc.is_active)
        self.assertIn("Two Sum - Basic Addition", str(tc))

    def test_multiple_test_cases_belong_to_challenge(self):
        from challenges.models import TestCase

        challenge = Challenge(id=1, title="Two Sum", points=100)
        tc1 = TestCase(id=1, challenge=challenge, name="TC 1", points=50)
        tc2 = TestCase(id=2, challenge=challenge, name="TC 2", points=50)
        self.assertEqual(tc1.challenge_id, tc2.challenge_id)


class SeedChallengesCommandTests(SimpleTestCase):
    def test_seed_data_configuration(self):
        from challenges.management.commands.seed_challenges import SEED_DATA

        self.assertEqual(len(SEED_DATA), 9)
        slugs = [c["slug"] for c in SEED_DATA]
        self.assertEqual(
            slugs,
            [
                "fix-the-broken-calculator",
                "the-missing-api-data",
                "the-exposed-admin-endpoint",
                "the-slow-report-generator",
                "add-two-numbers",
                "password-validator",
                "api-response-parser",
                "duplicate-transaction-detector",
                "slow-search-function",
            ],
        )

        for c in SEED_DATA:
            self.assertTrue(c["title"])
            self.assertTrue(c["description"])
            self.assertTrue(c["starter_code"])
            self.assertEqual(c["points"], 100)
            self.assertGreater(len(c["test_cases"]), 0)

            # Validate test cases point sum equals 100
            tc_points = sum(tc["points"] for tc in c["test_cases"])
            self.assertEqual(
                tc_points,
                100,
                f"Challenge '{c['title']}' test cases point sum ({tc_points}) does not equal 100.",
            )

            # Validate each test case has deterministic outputs and names
            for tc in c["test_cases"]:
                self.assertTrue(tc["name"])
                self.assertIsNotNone(tc.get("input_data"))
                self.assertTrue(tc.get("expected_output"))

    @patch("challenges.models.ChallengeFile.objects.update_or_create")
    @patch("challenges.models.TestCase.objects.update_or_create")
    @patch("challenges.models.Challenge.objects.update_or_create")
    @patch("django.db.transaction.atomic")
    def test_seed_command_execution(
        self, mock_atomic, mock_challenge_uoc, mock_tc_uoc, mock_file_uoc
    ):
        from io import StringIO
        from django.core.management import call_command

        mock_challenge = Challenge(id=1, title="Test", slug="test")
        mock_challenge_uoc.return_value = (mock_challenge, True)
        mock_tc_uoc.return_value = (MagicMock(), True)
        mock_file_uoc.return_value = (MagicMock(), True)

        out = StringIO()
        call_command("seed_challenges", stdout=out)

        output = out.getvalue()
        self.assertIn("CodeFoundry challenge seeding complete.", output)
        self.assertEqual(mock_challenge_uoc.call_count, 9)
        self.assertEqual(mock_tc_uoc.call_count, 42)
        self.assertEqual(mock_file_uoc.call_count, 40)




class ChallengeFileModelAndAPITests(SimpleTestCase):
    def test_1_challenge_file_creation_and_fields(self):
        from challenges.models import ChallengeFile

        challenge = Challenge(id=1, title="Two Sum", points=100)
        cf = ChallengeFile(
            id=1,
            challenge=challenge,
            path="src/main.py",
            content="print('hello')",
            is_test=False,
            is_readonly=False,
        )
        self.assertEqual(cf.challenge, challenge)
        self.assertEqual(cf.path, "src/main.py")
        self.assertEqual(cf.content, "print('hello')")
        self.assertFalse(cf.is_test)
        self.assertFalse(cf.is_readonly)
        self.assertIn("Two Sum - src/main.py", str(cf))

    def test_2_invalid_path_traversal_rejected(self):
        from django.core.exceptions import ValidationError
        from challenges.models import ChallengeFile

        challenge = Challenge(id=1, title="Two Sum", points=100)
        invalid_paths = [
            "../secret.txt",
            "/absolute/path.py",
            "app/../../etc/passwd",
            "",
            "   ",
        ]
        for p in invalid_paths:
            cf = ChallengeFile(challenge=challenge, path=p, content="")
            with self.assertRaises(ValidationError):
                cf.clean()

    def test_3_repository_serialization_masks_test_content(self):
        from challenges.models import ChallengeFile
        from challenges.serializers import ChallengeDetailSerializer

        challenge = Challenge(
            id=1,
            title="Add Two Numbers",
            slug="add-two-numbers",
            description="Add numbers",
            difficulty=Challenge.Difficulty.BEGINNER,
            challenge_type=Challenge.ChallengeType.BUG_FIX,
            programming_language="Python",
            points=100,
            time_limit=5,
            memory_limit=128,
        )
        readme = ChallengeFile(
            challenge=challenge,
            path="README.md",
            content="# Info",
            is_test=False,
            is_readonly=True,
        )
        test_file = ChallengeFile(
            challenge=challenge,
            path="tests/test_add.py",
            content="assert add(2, 3) == 5",
            is_test=True,
            is_readonly=True,
        )

        with patch.object(Challenge, "files", create=True) as mock_files:
            mock_files.all.return_value = [readme, test_file]
            mock_files.exists.return_value = True

            serializer = ChallengeDetailSerializer(challenge)
            data = serializer.data

            self.assertIn("repository", data)
            self.assertIsNotNone(data["repository"])
            files = data["repository"]["files"]
            self.assertEqual(len(files), 2)

            # Public file contains content
            self.assertEqual(files[0]["path"], "README.md")
            self.assertEqual(files[0]["content"], "# Info")
            self.assertTrue(files[0]["is_readonly"])
            self.assertFalse(files[0]["is_test"])

            # Test file MUST NOT contain content (None)
            self.assertEqual(files[1]["path"], "tests/test_add.py")
            self.assertIsNone(files[1]["content"])
            self.assertTrue(files[1]["is_test"])
            self.assertTrue(files[1]["is_readonly"])


class ChallengeProgressAPITests(SimpleTestCase):
    def setUp(self):
        from datetime import datetime, timezone as dt_timezone
        from .views import ChallengeProgressView
        from .progress import ChallengeProgressService
        from submissions.models import Submission

        self.service = ChallengeProgressService()
        self.factory = APIRequestFactory()
        self.view = ChallengeProgressView.as_view()

        self.user_a = User(id=1, username="student_a", email="a@example.com")
        self.user_b = User(id=2, username="student_b", email="b@example.com")

        self.c1 = Challenge(
            id=1,
            title="Two Sum",
            slug="two-sum",
            difficulty="BEGINNER",
            challenge_type="FEATURE",
            programming_language="Python",
            points=100,
            is_active=True,
        )
        self.c2 = Challenge(
            id=2,
            title="Fix Calculator Bug",
            slug="fix-calculator-bug",
            difficulty="INTERMEDIATE",
            challenge_type="BUG_FIX",
            programming_language="Python",
            points=150,
            is_active=True,
        )
        self.c_inactive = Challenge(
            id=99,
            title="Draft Challenge",
            slug="draft-chal",
            difficulty="EXPERT",
            challenge_type="SECURITY",
            programming_language="Python",
            points=200,
            is_active=False,
        )

        self.dt1 = datetime(2026, 9, 2, 8, 0, tzinfo=dt_timezone.utc)
        self.dt2 = datetime(2026, 9, 2, 8, 30, tzinfo=dt_timezone.utc)
        self.dt3 = datetime(2026, 9, 2, 9, 0, tzinfo=dt_timezone.utc)

    def test_1_unauthenticated_request_rejected(self):
        request = self.factory.get("/api/challenges/progress/")
        response = self.view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_2_new_user_no_submissions(self, mock_ch_filter, mock_sub_filter):
        mock_ch_filter.return_value.order_by.return_value = [self.c1, self.c2]
        mock_sub_filter.return_value.order_by.return_value = []

        request = self.factory.get("/api/challenges/progress/")
        force_authenticate(request, user=self.user_a)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["summary"]["total_challenges"], 2)
        self.assertEqual(data["summary"]["attempted_challenges"], 0)
        self.assertEqual(data["summary"]["completed_challenges"], 0)
        self.assertEqual(data["summary"]["completion_percentage"], 0.0)

        self.assertEqual(len(data["challenges"]), 2)
        for ch in data["challenges"]:
            self.assertEqual(ch["status"], "NOT_ATTEMPTED")
            self.assertIsNone(ch["best_score"])
            self.assertEqual(ch["attempts_count"], 0)
            self.assertIsNone(ch["latest_attempt_at"])

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_3_inactive_challenges_are_excluded(self, mock_ch_filter, mock_sub_filter):
        mock_ch_filter.return_value.order_by.return_value = [self.c1]
        mock_sub_filter.return_value.order_by.return_value = []

        progress = self.service.get_user_progress(self.user_a)
        self.assertEqual(progress["summary"]["total_challenges"], 1)
        self.assertEqual(len(progress["challenges"]), 1)
        self.assertEqual(progress["challenges"][0]["challenge_id"], 1)

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_4_one_failed_submission(self, mock_ch_filter, mock_sub_filter):
        from submissions.models import Submission

        mock_ch_filter.return_value.order_by.return_value = [self.c1]
        sub = Submission(
            id=101,
            user=self.user_a,
            challenge=self.c1,
            status=Submission.Status.FAILED,
            score=45,
            submitted_at=self.dt1,
        )
        sub.challenge_id = 1
        mock_sub_filter.return_value.order_by.return_value = [sub]

        progress = self.service.get_user_progress(self.user_a)
        self.assertEqual(progress["summary"]["attempted_challenges"], 1)
        self.assertEqual(progress["summary"]["completed_challenges"], 0)
        self.assertEqual(progress["summary"]["completion_percentage"], 0.0)

        ch_data = progress["challenges"][0]
        self.assertEqual(ch_data["status"], "FAILED")
        self.assertEqual(ch_data["attempts_count"], 1)
        self.assertEqual(ch_data["best_score"], 45)
        self.assertEqual(ch_data["latest_attempt_at"], self.dt1.isoformat())

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_5_one_passed_submission(self, mock_ch_filter, mock_sub_filter):
        from submissions.models import Submission

        mock_ch_filter.return_value.order_by.return_value = [self.c1]
        sub = Submission(
            id=102,
            user=self.user_a,
            challenge=self.c1,
            status=Submission.Status.PASSED,
            score=100,
            submitted_at=self.dt2,
        )
        sub.challenge_id = 1
        mock_sub_filter.return_value.order_by.return_value = [sub]

        progress = self.service.get_user_progress(self.user_a)
        self.assertEqual(progress["summary"]["attempted_challenges"], 1)
        self.assertEqual(progress["summary"]["completed_challenges"], 1)
        self.assertEqual(progress["summary"]["completion_percentage"], 100.0)

        ch_data = progress["challenges"][0]
        self.assertEqual(ch_data["status"], "PASSED")
        self.assertEqual(ch_data["attempts_count"], 1)
        self.assertEqual(ch_data["best_score"], 100)

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_6_multiple_attempts_on_same_challenge(self, mock_ch_filter, mock_sub_filter):
        from submissions.models import Submission

        mock_ch_filter.return_value.order_by.return_value = [self.c1]
        sub1 = Submission(id=1, user=self.user_a, challenge=self.c1, status=Submission.Status.FAILED, score=40, submitted_at=self.dt1)
        sub2 = Submission(id=2, user=self.user_a, challenge=self.c1, status=Submission.Status.FAILED, score=70, submitted_at=self.dt2)
        sub3 = Submission(id=3, user=self.user_a, challenge=self.c1, status=Submission.Status.PASSED, score=100, submitted_at=self.dt3)
        sub1.challenge_id = sub2.challenge_id = sub3.challenge_id = 1

        mock_sub_filter.return_value.order_by.return_value = [sub3, sub2, sub1]

        progress = self.service.get_user_progress(self.user_a)
        ch_data = progress["challenges"][0]
        self.assertEqual(ch_data["attempts_count"], 3)
        self.assertEqual(ch_data["best_score"], 100)
        self.assertEqual(ch_data["status"], "PASSED")
        self.assertEqual(ch_data["latest_attempt_at"], self.dt3.isoformat())

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_7_best_score_differs_from_latest_score(self, mock_ch_filter, mock_sub_filter):
        from submissions.models import Submission

        mock_ch_filter.return_value.order_by.return_value = [self.c1]
        # Older attempt had 100, newer attempt had 60
        sub_older = Submission(id=1, user=self.user_a, challenge=self.c1, status=Submission.Status.PASSED, score=100, submitted_at=self.dt1)
        sub_newer = Submission(id=2, user=self.user_a, challenge=self.c1, status=Submission.Status.FAILED, score=60, submitted_at=self.dt2)
        sub_older.challenge_id = sub_newer.challenge_id = 1

        mock_sub_filter.return_value.order_by.return_value = [sub_newer, sub_older]

        progress = self.service.get_user_progress(self.user_a)
        ch_data = progress["challenges"][0]
        self.assertEqual(ch_data["best_score"], 100)
        self.assertEqual(ch_data["status"], "PASSED")
        self.assertEqual(ch_data["latest_attempt_at"], self.dt2.isoformat())

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_8_multiple_challenges_counts_distinct_challenges(self, mock_ch_filter, mock_sub_filter):
        from submissions.models import Submission

        mock_ch_filter.return_value.order_by.return_value = [self.c1, self.c2]
        # 3 submissions on c1, 2 on c2
        s1 = Submission(id=1, user=self.user_a, challenge=self.c1, status=Submission.Status.PASSED, score=100, submitted_at=self.dt1)
        s2 = Submission(id=2, user=self.user_a, challenge=self.c1, status=Submission.Status.FAILED, score=50, submitted_at=self.dt2)
        s3 = Submission(id=3, user=self.user_a, challenge=self.c1, status=Submission.Status.FAILED, score=40, submitted_at=self.dt3)
        s4 = Submission(id=4, user=self.user_a, challenge=self.c2, status=Submission.Status.FAILED, score=70, submitted_at=self.dt1)
        s5 = Submission(id=5, user=self.user_a, challenge=self.c2, status=Submission.Status.FAILED, score=80, submitted_at=self.dt2)
        s1.challenge_id = s2.challenge_id = s3.challenge_id = 1
        s4.challenge_id = s5.challenge_id = 2

        mock_sub_filter.return_value.order_by.return_value = [s3, s2, s5, s1, s4]

        progress = self.service.get_user_progress(self.user_a)
        self.assertEqual(progress["summary"]["total_challenges"], 2)
        self.assertEqual(progress["summary"]["attempted_challenges"], 2)
        self.assertEqual(progress["summary"]["completed_challenges"], 1)
        self.assertEqual(progress["summary"]["completion_percentage"], 50.0)

    @patch("submissions.models.Submission.objects.filter")
    @patch("challenges.models.Challenge.objects.filter")
    def test_9_user_isolation(self, mock_ch_filter, mock_sub_filter):
        mock_ch_filter.return_value.order_by.return_value = [self.c1]
        mock_sub_filter.return_value.order_by.return_value = []

        request = self.factory.get("/api/challenges/progress/?user_id=99")
        force_authenticate(request, user=self.user_a)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure query strictly filtered by request.user
        mock_sub_filter.assert_called_once_with(user=self.user_a, challenge__is_active=True)

    @patch("challenges.models.Challenge.objects.filter")
    def test_10_zero_active_challenges(self, mock_ch_filter):
        mock_ch_filter.return_value.order_by.return_value = []

        progress = self.service.get_user_progress(self.user_a)
        self.assertEqual(progress["summary"]["total_challenges"], 0)
        self.assertEqual(progress["summary"]["completion_percentage"], 0.0)
        self.assertEqual(progress["challenges"], [])


class FixTheBrokenCalculatorChallengeTests(SimpleTestCase):
    def test_challenge_seed_structure(self):
        from challenges.management.commands.seed_challenges import SEED_DATA

        calc_seed = next((c for c in SEED_DATA if c["slug"] == "fix-the-broken-calculator"), None)
        self.assertIsNotNone(calc_seed)
        self.assertEqual(calc_seed["title"], "Fix the Broken Calculator")
        self.assertEqual(calc_seed["difficulty"], "BEGINNER")
        self.assertEqual(calc_seed["challenge_type"], "BUG_FIX")
        self.assertEqual(calc_seed["points"], 100)
        self.assertEqual(calc_seed["entrypoint"], "app/main.py")

        # Test cases
        test_cases = calc_seed.get("test_cases", [])
        self.assertEqual(len(test_cases), 5)
        public_tcs = [tc for tc in test_cases if not tc.get("is_hidden", False)]
        hidden_tcs = [tc for tc in test_cases if tc.get("is_hidden", False)]
        self.assertEqual(len(public_tcs), 2)
        self.assertEqual(len(hidden_tcs), 3)

        # Files
        files = calc_seed.get("files", [])
        self.assertEqual(len(files), 7)
        paths = {f["path"] for f in files}
        self.assertIn("README.md", paths)
        self.assertIn("app/calculator.py", paths)
        self.assertIn("app/main.py", paths)
        self.assertIn("tests/test_calculator.py", paths)

        readme = next(f for f in files if f["path"] == "README.md")
        self.assertTrue(readme["is_readonly"])

        test_file = next(f for f in files if f["path"] == "tests/test_calculator.py")
        self.assertTrue(test_file["is_test"])
        self.assertTrue(test_file["is_readonly"])


class TheMissingAPIDataChallengeTests(SimpleTestCase):
    def test_challenge_seed_structure(self):
        from challenges.management.commands.seed_challenges import SEED_DATA

        api_seed = next((c for c in SEED_DATA if c["slug"] == "the-missing-api-data"), None)
        self.assertIsNotNone(api_seed)
        self.assertEqual(api_seed["title"], "The Missing API Data")
        self.assertEqual(api_seed["difficulty"], "INTERMEDIATE")
        self.assertEqual(api_seed["challenge_type"], "API")
        self.assertEqual(api_seed["points"], 100)
        self.assertEqual(api_seed["entrypoint"], "app/main.py")

        # Test cases
        test_cases = api_seed.get("test_cases", [])
        self.assertEqual(len(test_cases), 5)
        public_tcs = [tc for tc in test_cases if not tc.get("is_hidden", False)]
        hidden_tcs = [tc for tc in test_cases if tc.get("is_hidden", False)]
        self.assertEqual(len(public_tcs), 2)
        self.assertEqual(len(hidden_tcs), 3)

        # Files
        files = api_seed.get("files", [])
        self.assertEqual(len(files), 9)
        paths = {f["path"] for f in files}
        self.assertIn("README.md", paths)
        self.assertIn("app/models.py", paths)
        self.assertIn("app/responses.py", paths)
        self.assertIn("app/service.py", paths)
        self.assertIn("app/main.py", paths)
        self.assertIn("tests/test_api.py", paths)

        readme = next(f for f in files if f["path"] == "README.md")
        self.assertTrue(readme["is_readonly"])

        test_file = next(f for f in files if f["path"] == "tests/test_api.py")
        self.assertTrue(test_file["is_test"])
        self.assertTrue(test_file["is_readonly"])


class TheExposedAdminEndpointChallengeTests(SimpleTestCase):
    def test_challenge_seed_structure(self):
        from challenges.management.commands.seed_challenges import SEED_DATA

        admin_seed = next((c for c in SEED_DATA if c["slug"] == "the-exposed-admin-endpoint"), None)
        self.assertIsNotNone(admin_seed)
        self.assertEqual(admin_seed["title"], "The Exposed Admin Endpoint")
        self.assertEqual(admin_seed["difficulty"], "INTERMEDIATE")
        self.assertEqual(admin_seed["challenge_type"], "SECURITY")
        self.assertEqual(admin_seed["points"], 100)
        self.assertEqual(admin_seed["entrypoint"], "app/main.py")

        # Test cases
        test_cases = admin_seed.get("test_cases", [])
        self.assertEqual(len(test_cases), 5)
        public_tcs = [tc for tc in test_cases if not tc.get("is_hidden", False)]
        hidden_tcs = [tc for tc in test_cases if tc.get("is_hidden", False)]
        self.assertEqual(len(public_tcs), 2)
        self.assertEqual(len(hidden_tcs), 3)

        # Files
        files = admin_seed.get("files", [])
        self.assertEqual(len(files), 10)
        paths = {f["path"] for f in files}
        self.assertIn("README.md", paths)
        self.assertIn("app/models.py", paths)
        self.assertIn("app/auth.py", paths)
        self.assertIn("app/responses.py", paths)
        self.assertIn("app/service.py", paths)
        self.assertIn("app/main.py", paths)
        self.assertIn("tests/test_access.py", paths)

        readme = next(f for f in files if f["path"] == "README.md")
        self.assertTrue(readme["is_readonly"])

        test_file = next(f for f in files if f["path"] == "tests/test_access.py")
        self.assertTrue(test_file["is_test"])
        self.assertTrue(test_file["is_readonly"])


class TheSlowReportGeneratorChallengeTests(SimpleTestCase):
    def test_challenge_seed_structure(self):
        from challenges.management.commands.seed_challenges import SEED_DATA

        perf_seed = next((c for c in SEED_DATA if c["slug"] == "the-slow-report-generator"), None)
        self.assertIsNotNone(perf_seed)
        self.assertEqual(perf_seed["title"], "The Slow Report Generator")
        self.assertEqual(perf_seed["difficulty"], "INTERMEDIATE")
        self.assertEqual(perf_seed["challenge_type"], "PERFORMANCE")
        self.assertEqual(perf_seed["points"], 100)
        self.assertEqual(perf_seed["entrypoint"], "app/main.py")

        # Test cases
        test_cases = perf_seed.get("test_cases", [])
        self.assertEqual(len(test_cases), 5)
        public_tcs = [tc for tc in test_cases if not tc.get("is_hidden", False)]
        hidden_tcs = [tc for tc in test_cases if tc.get("is_hidden", False)]
        self.assertEqual(len(public_tcs), 2)
        self.assertEqual(len(hidden_tcs), 3)

        # Files
        files = perf_seed.get("files", [])
        self.assertEqual(len(files), 8)
        paths = {f["path"] for f in files}
        self.assertIn("README.md", paths)
        self.assertIn("app/models.py", paths)
        self.assertIn("app/generator.py", paths)
        self.assertIn("app/main.py", paths)
        self.assertIn("tests/test_generator.py", paths)

        readme = next(f for f in files if f["path"] == "README.md")
        self.assertTrue(readme["is_readonly"])

        test_file = next(f for f in files if f["path"] == "tests/test_generator.py")
        self.assertTrue(test_file["is_test"])
        self.assertTrue(test_file["is_readonly"])
