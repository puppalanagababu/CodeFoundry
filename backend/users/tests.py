from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegisterSerializer, UserSerializer
from .views import CurrentUserView, LoginView, RegisterView

User = get_user_model()


class UserRegistrationTests(SimpleTestCase):
    @patch("django.contrib.auth.get_user_model")
    def test_1_successful_registration_creates_student(self, mock_user_cls):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "student1"
        mock_user.email = "student1@example.com"
        mock_user.role = "STUDENT"

        mock_user_model = MagicMock()
        mock_user_model.Role.STUDENT = "STUDENT"
        mock_user_model.objects.filter.return_value.exists.return_value = False
        mock_user_model.objects.create_user.return_value = mock_user
        mock_user_cls.return_value = mock_user_model

        with patch("users.serializers.User", mock_user_model):
            serializer = UserRegisterSerializer(
                data={
                    "username": "student1",
                    "email": "student1@example.com",
                    "password": "StrongPassword123!",
                    "password2": "StrongPassword123!",
                }
            )
            self.assertTrue(serializer.is_valid(), serializer.errors)
            user = serializer.save()

            mock_user_model.objects.create_user.assert_called_once_with(
                username="student1",
                email="student1@example.com",
                password="StrongPassword123!",
                role="STUDENT",
            )
            self.assertEqual(user.role, "STUDENT")

    @patch("users.serializers.User.objects.filter")
    def test_2_mismatched_passwords_rejected(self, mock_filter):
        mock_filter.return_value.exists.return_value = False
        serializer = UserRegisterSerializer(
            data={
                "username": "student1",
                "email": "student1@example.com",
                "password": "Password1!",
                "password2": "Password2!",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


    @patch("users.serializers.User.objects.filter")
    def test_3_duplicate_username_rejected(self, mock_filter):
        mock_filter.return_value.exists.return_value = True

        serializer = UserRegisterSerializer(
            data={
                "username": "existinguser",
                "email": "user@example.com",
                "password": "Password123!",
                "password2": "Password123!",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)

    @patch("users.serializers.User")
    def test_4_registration_cannot_create_admin_or_trainer(self, mock_user_model):
        mock_user = MagicMock(id=1, username="hacker", email="h@h.com", role="STUDENT")
        mock_user_model.Role.STUDENT = "STUDENT"
        mock_user_model.objects.filter.return_value.exists.return_value = False
        mock_user_model.objects.create_user.return_value = mock_user

        serializer = UserRegisterSerializer(
            data={
                "username": "hacker",
                "email": "hacker@example.com",
                "password": "Password123!",
                "password2": "Password123!",
                "role": "ADMIN",
            }
        )
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        mock_user_model.objects.create_user.assert_called_once_with(
            username="hacker",
            email="hacker@example.com",
            password="Password123!",
            role="STUDENT",
        )


class AuthAPITests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.register_view = RegisterView.as_view()
        self.current_user_view = CurrentUserView.as_view()
        self.user = User(
            id=1,
            username="student1",
            email="student1@example.com",
            role="STUDENT",
        )

    def test_unauthenticated_me_endpoint_rejected(self):
        request = self.factory.get("/api/auth/me/")
        response = self.current_user_view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_authenticated_me_endpoint_returns_user_data(self):
        request = self.factory.get("/api/auth/me/")
        force_authenticate(request, user=self.user)
        response = self.current_user_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["username"], "student1")
        self.assertEqual(response.data["email"], "student1@example.com")
        self.assertEqual(response.data["role"], "STUDENT")
        self.assertNotIn("password", response.data)


class DashboardAPITests(SimpleTestCase):
    def setUp(self):
        from .views import DashboardView

        self.factory = APIRequestFactory()
        self.view = DashboardView.as_view()
        self.user = User(id=1, username="student1", email="student1@example.com", role="STUDENT")

    def test_unauthenticated_dashboard_rejected(self):
        request = self.factory.get("/api/dashboard/")
        response = self.view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("submissions.models.Submission.objects.filter")
    def test_authenticated_empty_dashboard(self, mock_filter):
        mock_qs = MagicMock()
        mock_qs.count.return_value = 0
        mock_qs.values.return_value.distinct.return_value.count.return_value = 0
        mock_qs.aggregate.return_value = {"score__avg": None}
        mock_qs.select_related.return_value.order_by.return_value = []
        mock_qs.filter.return_value = mock_qs

        mock_filter.return_value = mock_qs

        request = self.factory.get("/api/dashboard/")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["overview"]["challenges_attempted"], 0)
        self.assertEqual(response.data["overview"]["challenges_passed"], 0)
        self.assertEqual(response.data["overview"]["total_submissions"], 0)
        self.assertEqual(response.data["overview"]["average_score"], 0)
        self.assertEqual(response.data["recent_submissions"], [])
        self.assertEqual(len(response.data["difficulty_progress"]), 4)


class SkillProfileAPITests(SimpleTestCase):
    def setUp(self):
        from .views import SkillProfileView

        self.factory = APIRequestFactory()
        self.view = SkillProfileView.as_view()
        self.user_a = User(id=1, username="student_a", email="student_a@example.com", role="STUDENT")
        self.user_b = User(id=2, username="student_b", email="student_b@example.com", role="STUDENT")

    def test_1_unauthenticated_request_rejected(self):
        request = self.factory.get("/api/users/skill-profile/")
        response = self.view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("evaluations.skill_profile.SkillProfileService.get_user_profile")
    def test_2_authenticated_user_receives_http_200(self, mock_get_profile):
        mock_get_profile.return_value = {
            "overall_score": 88,
            "skills": {
                "problem_solving": {"score": 85, "sample_size": 4, "status": "measured"},
                "debugging": {"score": 100, "sample_size": 2, "status": "measured"},
                "security": {"score": None, "sample_size": 0, "status": "insufficient_data"},
                "performance": {"score": 92, "sample_size": 4, "status": "measured"},
                "code_quality": {"score": None, "sample_size": 0, "status": "not_measured"},
                "testing": {"score": None, "sample_size": 0, "status": "not_measured"},
            },
            "total_evaluations_analyzed": 4,
        }

        request = self.factory.get("/api/users/skill-profile/")
        force_authenticate(request, user=self.user_a)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["overall_score"], 88)
        self.assertEqual(response.data["total_evaluations_analyzed"], 4)
        expected_dims = {
            "problem_solving",
            "debugging",
            "security",
            "performance",
            "code_quality",
            "testing",
        }
        self.assertEqual(set(response.data["skills"].keys()), expected_dims)

    @patch("evaluations.skill_profile.SkillProfileService.get_user_profile")
    def test_3_user_isolation_passes_authenticated_user_only(self, mock_get_profile):
        mock_get_profile.return_value = {
            "overall_score": None,
            "skills": {},
            "total_evaluations_analyzed": 0,
        }

        request = self.factory.get("/api/users/skill-profile/?user_id=2")
        force_authenticate(request, user=self.user_a)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Service must be called with request.user (user_a), never client-supplied ID
        mock_get_profile.assert_called_once_with(self.user_a)

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_4_user_with_no_evaluations_full_flow(self, mock_filter):
        mock_filter.return_value.select_related.return_value.order_by.return_value = []

        request = self.factory.get("/api/users/skill-profile/")
        force_authenticate(request, user=self.user_a)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["overall_score"])
        self.assertEqual(response.data["total_evaluations_analyzed"], 0)
        self.assertEqual(response.data["skills"]["problem_solving"]["status"], "insufficient_data")
        self.assertEqual(response.data["skills"]["code_quality"]["status"], "not_measured")

    @patch("evaluations.skill_profile.Evaluation.objects.filter")
    def test_5_completed_evaluations_reflected_in_api(self, mock_filter):
        from challenges.models import Challenge
        from evaluations.models import Evaluation
        from submissions.models import Submission
        from datetime import datetime, timezone as dt_timezone

        c = Challenge(id=1, title="Two Sum", points=100)
        sub = Submission(id=10, user=self.user_a, challenge=c, score=100)
        sub.challenge_id = 1
        ev = Evaluation(
            id=20,
            submission=sub,
            status=Evaluation.Status.COMPLETED,
            score=100,
            skill_breakdown={
                "scores": {"problem_solving": 100, "performance": 90},
                "evidence": {"problem_solving": "functional_tests", "performance": "execution_metrics"},
            },
            evaluated_at=datetime(2026, 9, 2, 12, 0, tzinfo=dt_timezone.utc),
        )
        mock_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        request = self.factory.get("/api/users/skill-profile/")
        force_authenticate(request, user=self.user_a)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["overall_score"], 95)
        self.assertEqual(response.data["total_evaluations_analyzed"], 1)
        self.assertEqual(response.data["skills"]["problem_solving"]["score"], 100)
        self.assertEqual(response.data["skills"]["problem_solving"]["status"], "measured")
        self.assertEqual(response.data["skills"]["performance"]["score"], 90)
        self.assertEqual(response.data["skills"]["security"]["status"], "insufficient_data")


