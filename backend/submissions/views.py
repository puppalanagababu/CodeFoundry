from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from challenges.models import Challenge
from evaluations.tasks import evaluate_submission
from .models import Submission
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    SubmissionHistorySerializer,
)


class SubmissionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class SubmissionListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = SubmissionPagination

    def get(self, request, *args, **kwargs):
        queryset = Submission.objects.filter(user=request.user).select_related(
            "challenge"
        )

        # Challenge filter
        challenge_param = request.query_params.get("challenge")
        if challenge_param:
            try:
                challenge_id = int(challenge_param)
                queryset = queryset.filter(challenge_id=challenge_id)
            except ValueError:
                return Response(
                    {"error": f"Invalid challenge id '{challenge_param}'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Status filter
        status_param = request.query_params.get("status")
        if status_param:
            status_upper = status_param.strip().upper()
            if status_upper not in Submission.Status.values:
                return Response(
                    {
                        "error": f"Invalid status '{status_param}'. Valid choices are: {list(Submission.Status.values)}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_upper)

        queryset = queryset.order_by("-submitted_at", "-id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = SubmissionHistorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SubmissionHistorySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(user=request.user)

        # Dispatch asynchronous evaluation to Celery worker
        evaluate_submission.delay(submission.id)

        response_data = {
            "submission_id": submission.id,
            "challenge": (
                submission.challenge_id
                if hasattr(submission, "challenge_id")
                else getattr(submission.challenge, "id", None)
            ),
            "status": submission.status,
            "score": submission.score,
            "message": "Submission queued for evaluation.",
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(
            Submission.objects.filter(user=request.user),
            pk=pk,
        )
        serializer = SubmissionDetailSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BestSubmissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_submissions = Submission.objects.filter(
            user=request.user
        ).select_related("challenge")

        # Distinct challenge IDs attempted by user
        challenge_ids = (
            user_submissions.values_list("challenge_id", flat=True)
            .distinct()
            .order_by("challenge_id")
        )

        results = []
        for ch_id in challenge_ids:
            ch_subs = user_submissions.filter(challenge_id=ch_id).order_by(
                "-submitted_at", "-id"
            )
            latest_sub = ch_subs.first()
            best_score = ch_subs.aggregate(Max("score"))["score__max"] or 0
            attempts = ch_subs.count()

            results.append(
                {
                    "challenge": ch_id,
                    "challenge_title": (
                        latest_sub.challenge.title
                        if latest_sub and latest_sub.challenge
                        else ""
                    ),
                    "best_score": best_score,
                    "attempts": attempts,
                    "latest_status": (
                        latest_sub.status if latest_sub else None
                    ),
                    "latest_submission_id": (
                        latest_sub.id if latest_sub else None
                    ),
                }
            )

        return Response({"results": results}, status=status.HTTP_200_OK)


class ChallengeSubmissionHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = SubmissionPagination

    def get(self, request, pk, *args, **kwargs):
        challenge = get_object_or_404(Challenge, pk=pk)
        queryset = (
            Submission.objects.filter(
                user=request.user, challenge=challenge
            )
            .select_related("challenge")
            .order_by("-submitted_at", "-id")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = SubmissionHistorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SubmissionHistorySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


SubmissionCreateView = SubmissionListCreateView

