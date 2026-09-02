from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Challenge
from .serializers import ChallengeDetailSerializer, ChallengeListSerializer


class ChallengePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class ChallengeListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ChallengePagination

    def get(self, request, *args, **kwargs):
        queryset = Challenge.objects.filter(is_active=True)

        # Search filter
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(slug__icontains=search)
            )

        # Difficulty filter
        difficulty = request.query_params.get("difficulty")
        if difficulty:
            difficulty_upper = difficulty.strip().upper()
            if difficulty_upper not in Challenge.Difficulty.values:
                return Response(
                    {
                        "error": f"Invalid difficulty '{difficulty}'. Valid choices are: {list(Challenge.Difficulty.values)}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(difficulty=difficulty_upper)

        # Challenge type filter
        challenge_type = request.query_params.get("challenge_type")
        if challenge_type:
            challenge_type_upper = challenge_type.strip().upper()
            if challenge_type_upper not in Challenge.ChallengeType.values:
                return Response(
                    {
                        "error": f"Invalid challenge_type '{challenge_type}'. Valid choices are: {list(Challenge.ChallengeType.values)}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(challenge_type=challenge_type_upper)

        # Programming language filter
        language = request.query_params.get("programming_language")
        if language:
            queryset = queryset.filter(
                programming_language__iexact=language.strip()
            )

        # Deterministic ordering
        queryset = queryset.order_by("-created_at", "-id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = ChallengeListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ChallengeListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChallengeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        challenge = get_object_or_404(
            Challenge.objects.filter(is_active=True),
            pk=pk,
        )
        serializer = ChallengeDetailSerializer(challenge)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChallengeProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from .progress import ChallengeProgressService

        service = ChallengeProgressService()
        progress_data = service.get_user_progress(request.user)
        return Response(progress_data, status=status.HTTP_200_OK)


