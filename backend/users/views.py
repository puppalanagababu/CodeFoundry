import logging
from django.conf import settings
from django.db.models import Avg
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from challenges.models import Challenge
from submissions.models import Submission
from .serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegisterSerializer,
    UserSerializer,
)
from .throttles import LoginRateThrottle, PasswordResetRateThrottle

User = get_user_model()
logger = logging.getLogger("users.auth")


def get_client_ip(request):
    if not request:
        return "unknown"
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def sanitize_log_value(value):
    if not value:
        return ""
    return str(value).replace("\r", "").replace("\n", "").replace("\t", "").strip()[:150]


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        username = ""
        if hasattr(request, "data") and isinstance(request.data, dict):
            username = request.data.get("username", "")
        clean_user = sanitize_log_value(username)
        ip = get_client_ip(request)

        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                logger.info("Login successful for user: %s (IP: %s)", clean_user, ip)
            return response
        except (AuthenticationFailed, InvalidToken):
            logger.warning("Login authentication failed for user: %s (IP: %s)", clean_user, ip)
            raise
        except Exception:
            logger.warning("Login authentication failed for user: %s (IP: %s)", clean_user, ip)
            raise


class LogoutView(APIView):
    """
    Blacklists the provided refresh token, invalidating the session.
    Allowed for any requester with a valid refresh token (even if access token has expired).
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        refresh_token = request.data.get("refresh") if isinstance(request.data, dict) else None
        if not refresh_token:
            logger.warning("Logout failed: missing refresh token (IP: %s)", ip)
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Logout completed successfully (IP: %s)", ip)
            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )
        except (TokenError, InvalidToken):
            logger.warning("Logout failed: invalid or expired refresh token (IP: %s)", ip)
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Unexpected error during logout (IP: %s)", ip)
            return Response(
                {"detail": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR if not getattr(settings, 'DEBUG', False) else status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetRequestView(APIView):
    """
    Initiates password reset by sending an email with a secure single-use token.
    Account enumeration protected: always returns generic 200 response.
    """
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        User = get_user_model()
        ip = get_client_ip(request)
        serializer = PasswordResetRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"].strip()
            users = User.objects.filter(email__iexact=email, is_active=True)
            for user in users:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = f"/reset-password?uid={uid}&token={token}"
                send_mail(
                    subject="CodeFoundry — Password Reset Request",
                    message=(
                        f"Hello {user.username},\n\n"
                        f"A password reset was requested for your CodeFoundry account.\n"
                        f"Use the following link to reset your password:\n"
                        f"{reset_url}\n\n"
                        f"This link will expire in 30 minutes and can only be used once.\n"
                        f"If you did not request this, you can safely ignore this email."
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@codefoundry.dev"),
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            logger.info("Password reset requested (IP: %s)", ip)

        return Response(
            {"detail": "If an account exists for this email, password reset instructions have been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    Confirms password reset using secure token and sets the new password.
    Single-use guarantee via default_token_generator.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning("Password reset failed: invalid or expired token (IP: %s)", ip)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        # Invalidate existing sessions by blacklisting all outstanding refresh tokens for the user
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            for token in outstanding_tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            logger.warning("Could not blacklist outstanding tokens for user ID: %s", user.id)

        logger.info("Password reset completed successfully for user ID: %s (IP: %s)", user.id, ip)
        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_subs = Submission.objects.filter(user=request.user)

        # Overview calculations
        total_submissions = user_subs.count()
        challenges_attempted = (
            user_subs.values("challenge_id").distinct().count()
        )
        challenges_passed = (
            user_subs.filter(status=Submission.Status.PASSED)
            .values("challenge_id")
            .distinct()
            .count()
        )
        avg_score_agg = user_subs.aggregate(Avg("score"))["score__avg"]
        average_score = (
            round(avg_score_agg) if avg_score_agg is not None else 0
        )

        # Recent Submissions (latest 5)
        recent_qs = (
            user_subs.select_related("challenge")
            .order_by("-submitted_at", "-id")[:5]
        )
        recent_submissions = []
        for sub in recent_qs:
            recent_submissions.append(
                {
                    "id": sub.id,
                    "challenge": (
                        sub.challenge_id
                        if hasattr(sub, "challenge_id")
                        else getattr(sub.challenge, "id", None)
                    ),
                    "challenge_title": (
                        sub.challenge.title if sub.challenge else ""
                    ),
                    "status": sub.status,
                    "score": sub.score,
                    "language": sub.language,
                    "submitted_at": (
                        sub.submitted_at.isoformat()
                        if sub.submitted_at
                        else None
                    ),
                }
            )

        # Difficulty Progress
        difficulty_progress = []
        for diff in Challenge.Difficulty.values:
            diff_subs = user_subs.filter(challenge__difficulty=diff)
            diff_attempted = diff_subs.values("challenge_id").distinct().count()
            diff_passed = (
                diff_subs.filter(status=Submission.Status.PASSED)
                .values("challenge_id")
                .distinct()
                .count()
            )
            diff_avg = diff_subs.aggregate(Avg("score"))["score__avg"]
            diff_avg_score = round(diff_avg) if diff_avg is not None else 0

            difficulty_progress.append(
                {
                    "difficulty": diff,
                    "attempted": diff_attempted,
                    "passed": diff_passed,
                    "average_score": diff_avg_score,
                }
            )

        data = {
            "overview": {
                "challenges_attempted": challenges_attempted,
                "challenges_passed": challenges_passed,
                "total_submissions": total_submissions,
                "average_score": average_score,
            },
            "recent_submissions": recent_submissions,
            "difficulty_progress": difficulty_progress,
        }
        return Response(data, status=status.HTTP_200_OK)


class SkillProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from evaluations.skill_profile import SkillProfileService

        service = SkillProfileService()
        profile_data = service.get_user_profile(request.user)
        return Response(profile_data, status=status.HTTP_200_OK)


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from evaluations.leaderboard import LeaderboardService

        service = LeaderboardService()
        results = service.get_leaderboard(current_user=request.user)
        return Response({"results": results}, status=status.HTTP_200_OK)


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username, *args, **kwargs):
        from .profile_service import PublicProfileService

        service = PublicProfileService()
        profile = service.get_public_profile(username=username)
        if profile is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(profile, status=status.HTTP_200_OK)


class RecruiterCandidateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from .permissions import IsRecruiterUser
        from .recruiter_service import RecruiterDashboardService

        # Check recruiter permission
        if not IsRecruiterUser().has_permission(request, self):
            return Response(
                {"detail": "You do not have permission to access the recruiter dashboard."},
                status=status.HTTP_403_FORBIDDEN,
            )

        search = request.query_params.get("search", "")
        min_skill_score_raw = request.query_params.get("min_skill_score")
        challenge_type = request.query_params.get("challenge_type")

        min_skill_score = None
        if min_skill_score_raw is not None:
            try:
                min_skill_score = int(min_skill_score_raw)
            except (ValueError, TypeError):
                min_skill_score = None

        service = RecruiterDashboardService()
        candidates = service.get_candidates(
            search=search,
            min_skill_score=min_skill_score,
            challenge_type=challenge_type,
        )
        return Response({"results": candidates}, status=status.HTTP_200_OK)


class RecruiterCandidateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username, *args, **kwargs):
        from .permissions import IsRecruiterUser
        from .recruiter_service import RecruiterDashboardService

        # Check recruiter permission
        if not IsRecruiterUser().has_permission(request, self):
            return Response(
                {"detail": "You do not have permission to access the recruiter dashboard."},
                status=status.HTTP_403_FORBIDDEN,
            )

        service = RecruiterDashboardService()
        candidate = service.get_candidate_detail(username=username)
        if candidate is None:
            return Response(
                {"detail": "Candidate not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(candidate, status=status.HTTP_200_OK)
