from django.db.models import Avg
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from challenges.models import Challenge
from submissions.models import Submission
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegisterSerializer,
    UserSerializer,
)


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

