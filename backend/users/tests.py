from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from submissions.models import Submission
from .serializers import UserRegisterSerializer, UserSerializer
from .views import CurrentUserView, LoginView, LogoutView, RegisterView

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


class PublicProfileServiceTests(SimpleTestCase):
    def setUp(self):
        from users.profile_service import PublicProfileService
        from challenges.models import Challenge
        from evaluations.models import Evaluation
        from submissions.models import Submission
        from datetime import datetime, timezone as dt_timezone

        self.service = PublicProfileService()
        self.user = User(id=1, username="testdev", email="dev@example.com")
        self.c1 = Challenge(id=1, title="Fix Calculator", difficulty="BEGINNER", challenge_type="BUG_FIX", points=100, is_active=True)
        self.c2 = Challenge(id=2, title="Secure API", difficulty="INTERMEDIATE", challenge_type="SECURITY", points=100, is_active=True)
        self.c_inactive = Challenge(id=3, title="Old Task", difficulty="BEGINNER", challenge_type="BUG_FIX", points=100, is_active=False)

    def _mock_eval(self, challenge, score=100, status_sub=Submission.Status.PASSED, eval_id=1, evaluated_at=None, skill_breakdown=None):
        from datetime import datetime, timezone as dt_timezone
        from evaluations.models import Evaluation
        from submissions.models import Submission

        evaluated_at = evaluated_at or datetime(2026, 9, 1, 12, 0, tzinfo=dt_timezone.utc)
        sub = Submission(
            id=eval_id * 10,
            user=self.user,
            challenge=challenge,
            score=score,
            status=status_sub,
        )
        sub.challenge_id = challenge.id
        sub.user_id = self.user.id
        ev = Evaluation(
            id=eval_id,
            submission=sub,
            status=Evaluation.Status.COMPLETED,
            score=score,
            evaluated_at=evaluated_at,
            skill_breakdown=(
                skill_breakdown
                if skill_breakdown is not None
                else {"scores": {"problem_solving": score}}
            ),
        )
        return ev

    @patch("users.profile_service.User.objects.get")
    def test_1_unknown_username_returns_none(self, mock_user_get):
        mock_user_get.side_effect = User.DoesNotExist
        result = self.service.get_public_profile("nonexistent")
        self.assertIsNone(result)

    @patch("evaluations.achievements.AchievementService.get_user_achievements", return_value=[])
    @patch("users.profile_service.Evaluation.objects.filter")
    @patch("users.profile_service.User.objects.get")
    def test_2_new_user_with_no_activity_returns_zero_profile(self, mock_user_get, mock_eval_filter, mock_ach):
        mock_user_get.return_value = self.user
        mock_eval_filter.return_value.select_related.return_value.order_by.return_value = []

        result = self.service.get_public_profile("testdev")
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "testdev")
        self.assertIsNone(result["overall_skill_score"])
        self.assertEqual(result["challenges_completed"], 0)
        self.assertEqual(result["challenges_attempted"], 0)
        self.assertEqual(result["completion_percentage"], 0.0)
        self.assertIsNone(result["average_score"])
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["achievements"], [])
        self.assertEqual(result["recent_activity"], [])
        self.assertIn("problem_solving", result["skill_breakdown"])
        self.assertEqual(result["skill_breakdown"]["problem_solving"]["status"], "insufficient_data")

    @patch("evaluations.achievements.AchievementService.get_user_achievements", return_value=[])
    @patch("users.profile_service.Evaluation.objects.filter")
    @patch("users.profile_service.User.objects.get")
    def test_3_completed_challenges_and_deduplication(self, mock_user_get, mock_eval_filter, mock_ach):
        from submissions.models import Submission
        from datetime import datetime, timezone as dt_timezone

        mock_user_get.return_value = self.user

        # 2 attempts on Challenge 1 (40 then 100), 1 attempt on Challenge 2 (100)
        ev1_low = self._mock_eval(self.c1, score=40, status_sub=Submission.Status.FAILED, eval_id=1, evaluated_at=datetime(2026, 9, 1, 10, 0, tzinfo=dt_timezone.utc))
        ev1_high = self._mock_eval(self.c1, score=100, status_sub=Submission.Status.PASSED, eval_id=2, evaluated_at=datetime(2026, 9, 1, 11, 0, tzinfo=dt_timezone.utc))
        ev2 = self._mock_eval(self.c2, score=100, status_sub=Submission.Status.PASSED, eval_id=3, evaluated_at=datetime(2026, 9, 1, 12, 0, tzinfo=dt_timezone.utc))

        mock_eval_filter.return_value.select_related.return_value.order_by.return_value = [ev1_high, ev1_low, ev2]

        result = self.service.get_public_profile("testdev")
        self.assertEqual(result["challenges_attempted"], 2)
        self.assertEqual(result["challenges_completed"], 2)
        self.assertEqual(result["completion_percentage"], 100.0)
        self.assertEqual(result["total_points"], 200)
        self.assertEqual(result["average_score"], 100.0)
        self.assertEqual(result["overall_skill_score"], 100)

    @patch("evaluations.achievements.AchievementService.get_user_achievements", return_value=[])
    @patch("users.profile_service.Evaluation.objects.filter")
    @patch("users.profile_service.User.objects.get")
    def test_4_privacy_no_sensitive_fields(self, mock_user_get, mock_eval_filter, mock_ach):
        mock_user_get.return_value = self.user
        ev = self._mock_eval(self.c1, score=100)
        mock_eval_filter.return_value.select_related.return_value.order_by.return_value = [ev]

        result = self.service.get_public_profile("testdev")
        self.assertNotIn("email", result)
        self.assertNotIn("password", result)
        self.assertNotIn("password_hash", result)
        self.assertNotIn("tokens", result)
        self.assertNotIn("code", result)

    @patch("evaluations.achievements.AchievementService.get_user_achievements", return_value=[])
    @patch("users.profile_service.Evaluation.objects.filter")
    @patch("users.profile_service.User.objects.get")
    def test_5_recent_activity_limit_and_safe_fields(self, mock_user_get, mock_eval_filter, mock_ach):
        from datetime import datetime, timezone as dt_timezone
        mock_user_get.return_value = self.user

        evs = [
            self._mock_eval(self.c1, score=100, eval_id=i, evaluated_at=datetime(2026, 9, 1, i, 0, tzinfo=dt_timezone.utc))
            for i in range(1, 8)
        ]

        def filter_side_effect(*args, **kwargs):
            mock_res = MagicMock()
            # If sliced to 5 in view, return 5
            mock_res.select_related.return_value.order_by.return_value.__getitem__.return_value = evs[:5]
            mock_res.select_related.return_value.order_by.return_value = evs
            return mock_res

        mock_eval_filter.side_effect = filter_side_effect

        result = self.service.get_public_profile("testdev")
        self.assertLessEqual(len(result["recent_activity"]), 5)
        for act in result["recent_activity"]:
            self.assertIn("challenge_id", act)
            self.assertIn("challenge_title", act)
            self.assertIn("challenge_type", act)
            self.assertIn("difficulty", act)
            self.assertIn("score", act)
            self.assertIn("status", act)
            self.assertIn("evaluated_at", act)
            self.assertNotIn("code", act)
            self.assertNotIn("stdout", act)
            self.assertNotIn("stderr", act)


class PublicProfileAPITests(SimpleTestCase):
    def setUp(self):
        from rest_framework.test import APIRequestFactory
        from users.views import PublicProfileView

        self.factory = APIRequestFactory()
        self.view = PublicProfileView.as_view()

    @patch("users.profile_service.PublicProfileService.get_public_profile")
    def test_1_public_profile_accessible_without_authentication(self, mock_get_profile):
        mock_get_profile.return_value = {
            "username": "developer1",
            "overall_skill_score": 94,
            "skill_breakdown": {},
            "challenges_completed": 5,
            "challenges_attempted": 7,
            "completion_percentage": 71.4,
            "average_score": 91.8,
            "total_points": 500,
            "achievements": [],
            "recent_activity": [],
        }

        request = self.factory.get("/api/users/profile/developer1/")
        response = self.view(request, username="developer1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "developer1")
        self.assertEqual(response.data["total_points"], 500)
        self.assertEqual(response.data["completion_percentage"], 71.4)

    @patch("users.profile_service.PublicProfileService.get_public_profile")
    def test_2_unknown_user_returns_404(self, mock_get_profile):
        mock_get_profile.return_value = None

        request = self.factory.get("/api/users/profile/ghost/")
        response = self.view(request, username="ghost")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "User not found.")


class RecruiterDashboardServiceTests(SimpleTestCase):
    def setUp(self):
        from users.recruiter_service import RecruiterDashboardService
        from challenges.models import Challenge
        from datetime import datetime, timezone as dt_timezone

        self.service = RecruiterDashboardService()
        self.dev1 = User(id=10, username="dev1", email="dev1@example.com", role=User.Role.STUDENT)
        self.dev2 = User(id=20, username="dev2", email="dev2@example.com", role=User.Role.STUDENT)

        self.c1 = Challenge(id=1, title="Fix Calc", difficulty="BEGINNER", challenge_type=Challenge.ChallengeType.BUG_FIX, points=100, is_active=True)
        self.c2 = Challenge(id=2, title="Secure API", difficulty="INTERMEDIATE", challenge_type=Challenge.ChallengeType.SECURITY, points=100, is_active=True)

    def _mock_eval(self, user, challenge, score=100, status_sub=Submission.Status.PASSED, eval_id=1, evaluated_at=None):
        from datetime import datetime, timezone as dt_timezone
        from evaluations.models import Evaluation
        from submissions.models import Submission

        evaluated_at = evaluated_at or datetime(2026, 9, 1, 12, 0, tzinfo=dt_timezone.utc)
        sub = Submission(
            id=eval_id * 10,
            user=user,
            challenge=challenge,
            score=score,
            status=status_sub,
        )
        sub.challenge_id = challenge.id
        sub.user_id = user.id
        ev = Evaluation(
            id=eval_id,
            submission=sub,
            status=Evaluation.Status.COMPLETED,
            score=score,
            evaluated_at=evaluated_at,
            skill_breakdown={"scores": {"problem_solving": score}},
        )
        return ev

    @patch("users.recruiter_service.UserAchievement.objects.filter")
    @patch("users.recruiter_service.Evaluation.objects.filter")
    def test_1_get_candidates_summary_and_exclusion_of_empty_users(self, mock_eval_filter, mock_ua_filter):
        mock_ua_filter.return_value.values.return_value.annotate.return_value = [{"user_id": 10, "count": 2}]

        ev1 = self._mock_eval(self.dev1, self.c1, score=100, status_sub=Submission.Status.PASSED, eval_id=1)
        mock_eval_filter.return_value.select_related.return_value.order_by.return_value = [ev1]

        candidates = self.service.get_candidates()
        self.assertEqual(len(candidates), 1)
        cand = candidates[0]
        self.assertEqual(cand["user_id"], 10)
        self.assertEqual(cand["username"], "dev1")
        self.assertEqual(cand["total_points"], 100)
        self.assertEqual(cand["challenges_completed"], 1)
        self.assertEqual(cand["challenges_attempted"], 1)
        self.assertEqual(cand["achievements_count"], 2)
        self.assertNotIn("email", cand)
        self.assertNotIn("password", cand)

    @patch("users.recruiter_service.UserAchievement.objects.filter")
    @patch("users.recruiter_service.Evaluation.objects.filter")
    def test_2_candidates_filtering_and_sorting(self, mock_eval_filter, mock_ua_filter):
        mock_ua_filter.return_value.values.return_value.annotate.return_value = []

        ev1 = self._mock_eval(self.dev1, self.c1, score=100, eval_id=1)
        ev2 = self._mock_eval(self.dev2, self.c2, score=70, eval_id=2)
        mock_eval_filter.return_value.select_related.return_value.order_by.return_value = [ev1, ev2]

        # Search filter
        results_search = self.service.get_candidates(search="dev1")
        self.assertEqual(len(results_search), 1)
        self.assertEqual(results_search[0]["username"], "dev1")

        # Min score filter
        results_min_score = self.service.get_candidates(min_skill_score=80)
        self.assertEqual(len(results_min_score), 1)
        self.assertEqual(results_min_score[0]["username"], "dev1")

        # Challenge type filter
        results_type = self.service.get_candidates(challenge_type="SECURITY")
        self.assertEqual(len(results_type), 1)
        self.assertEqual(results_type[0]["username"], "dev2")

    @patch("users.recruiter_service.AchievementService.get_user_achievements", return_value=[])
    @patch("users.recruiter_service.Evaluation.objects.filter")
    @patch("users.recruiter_service.User.objects.get")
    def test_3_get_candidate_detail_returns_safe_evidence(self, mock_user_get, mock_eval_filter, mock_ach):
        mock_user_get.return_value = self.dev1
        ev1 = self._mock_eval(self.dev1, self.c1, score=100, eval_id=1)

        def eval_filter_side_effect(*args, **kwargs):
            mock_res = MagicMock()
            mock_res.select_related.return_value.order_by.return_value.__getitem__.return_value = [ev1]
            mock_res.select_related.return_value.order_by.return_value = [ev1]
            return mock_res

        mock_eval_filter.side_effect = eval_filter_side_effect

        detail = self.service.get_candidate_detail("dev1")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["username"], "dev1")
        self.assertEqual(detail["metrics"]["total_points"], 100)
        self.assertIn("skills", detail)
        self.assertIn("challenge_evidence", detail)
        self.assertEqual(len(detail["challenge_evidence"]), 1)
        evidence = detail["challenge_evidence"][0]
        self.assertEqual(evidence["challenge_title"], "Fix Calc")
        self.assertEqual(evidence["score"], 100)
        self.assertNotIn("code", evidence)
        self.assertNotIn("stdout", evidence)


class RecruiterDashboardAPITests(SimpleTestCase):
    def setUp(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from users.views import RecruiterCandidateDetailView, RecruiterCandidateListView

        self.factory = APIRequestFactory()
        self.list_view = RecruiterCandidateListView.as_view()
        self.detail_view = RecruiterCandidateDetailView.as_view()

        self.student = User(id=1, username="student1", role=User.Role.STUDENT)
        self.recruiter = User(id=2, username="recruiter1", role=User.Role.RECRUITER)

    def test_1_unauthenticated_request_returns_401(self):
        request = self.factory.get("/api/recruiter/candidates/")
        response = self.list_view(request)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_2_student_request_returns_403(self):
        from rest_framework.test import force_authenticate
        request = self.factory.get("/api/recruiter/candidates/")
        force_authenticate(request, user=self.student)
        response = self.list_view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("users.recruiter_service.RecruiterDashboardService.get_candidates")
    def test_3_recruiter_request_returns_200(self, mock_get_candidates):
        from rest_framework.test import force_authenticate
        mock_get_candidates.return_value = [
            {
                "user_id": 10,
                "username": "candidate1",
                "overall_skill_score": 90,
                "total_points": 300,
                "challenges_completed": 3,
                "challenges_attempted": 3,
                "average_score": 100.0,
                "completion_percentage": 100.0,
                "achievements_count": 1,
            }
        ]

        request = self.factory.get("/api/recruiter/candidates/")
        force_authenticate(request, user=self.recruiter)
        response = self.list_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "candidate1")

    @patch("users.recruiter_service.RecruiterDashboardService.get_candidate_detail")
    def test_4_recruiter_detail_returns_404_for_unknown_user(self, mock_get_detail):
        from rest_framework.test import force_authenticate
        mock_get_detail.return_value = None

        request = self.factory.get("/api/recruiter/candidates/ghost/")
        force_authenticate(request, user=self.recruiter)
        response = self.detail_view(request, username="ghost")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Candidate not found.")


class RefreshTokenRotationAndBlacklistTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.refresh_view = TokenRefreshView.as_view()

    @patch("rest_framework_simplejwt.serializers.TokenRefreshSerializer.validate")
    def test_1_refresh_token_rotation_returns_new_access_and_refresh_tokens(self, mock_validate):
        mock_validate.return_value = {
            "access": "new.access.token",
            "refresh": "new.rotated.refresh.token",
        }

        request = self.factory.post("/api/auth/refresh/", {"refresh": "initial.refresh.token"}, format="json")
        response = self.refresh_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["access"], "new.access.token")
        self.assertEqual(response.data["refresh"], "new.rotated.refresh.token")

    @patch("rest_framework_simplejwt.serializers.TokenRefreshSerializer.validate")
    def test_2_old_refresh_token_rejection(self, mock_validate):
        from rest_framework_simplejwt.exceptions import InvalidToken
        mock_validate.side_effect = InvalidToken("Token is blacklisted")

        request = self.factory.post("/api/auth/refresh/", {"refresh": "old.blacklisted.token"}, format="json")
        response = self.refresh_view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutAPITests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.logout_view = LogoutView.as_view()

    @patch("users.views.RefreshToken")
    def test_1_logout_successfully_blacklists_refresh_token(self, mock_refresh_cls):
        mock_token_instance = MagicMock()
        mock_refresh_cls.return_value = mock_token_instance

        request = self.factory.post("/api/auth/logout/", {"refresh": "dummy.refresh.jwt"}, format="json")
        response = self.logout_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("message"), "Logged out successfully.")
        mock_refresh_cls.assert_called_once_with("dummy.refresh.jwt")
        mock_token_instance.blacklist.assert_called_once()

    def test_2_logout_missing_refresh_token_rejected_safely(self):
        request = self.factory.post("/api/auth/logout/", {}, format="json")
        response = self.logout_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("detail"), "Refresh token is required.")

    @patch("users.views.RefreshToken")
    def test_3_logout_invalid_refresh_token_rejected_safely(self, mock_refresh_cls):
        from rest_framework_simplejwt.exceptions import TokenError
        mock_refresh_cls.side_effect = TokenError("Token is invalid or expired")

        request = self.factory.post("/api/auth/logout/", {"refresh": "invalid.jwt.token"}, format="json")
        response = self.logout_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("detail"), "Invalid or expired refresh token.")

    @patch("users.views.RefreshToken")
    def test_4_logout_already_blacklisted_token_handled_safely(self, mock_refresh_cls):
        from rest_framework_simplejwt.exceptions import TokenError
        mock_token_instance = MagicMock()
        mock_token_instance.blacklist.side_effect = TokenError("Token is blacklisted")
        mock_refresh_cls.return_value = mock_token_instance

        request = self.factory.post("/api/auth/logout/", {"refresh": "already.blacklisted.jwt"}, format="json")
        response = self.logout_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("detail"), "Invalid or expired refresh token.")

    @patch("users.views.RefreshToken")
    def test_5_logout_unauthenticated_request_works_with_valid_refresh_token(self, mock_refresh_cls):
        mock_token_instance = MagicMock()
        mock_refresh_cls.return_value = mock_token_instance

        request = self.factory.post("/api/auth/logout/", {"refresh": "valid.refresh.jwt"}, format="json")
        response = self.logout_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("message"), "Logged out successfully.")
