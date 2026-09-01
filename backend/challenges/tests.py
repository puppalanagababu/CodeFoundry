from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
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

        self.assertEqual(len(SEED_DATA), 5)
        slugs = [c["slug"] for c in SEED_DATA]
        self.assertEqual(
            slugs,
            [
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
        self.assertEqual(mock_challenge_uoc.call_count, 5)
        self.assertEqual(mock_tc_uoc.call_count, 22)
        self.assertEqual(mock_file_uoc.call_count, 6)



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



