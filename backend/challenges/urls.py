from django.urls import path
from submissions.views import ChallengeSubmissionHistoryView
from .views import ChallengeDetailView, ChallengeListView, ChallengeProgressView


urlpatterns = [
    path("", ChallengeListView.as_view(), name="challenge-list"),
    path("progress/", ChallengeProgressView.as_view(), name="challenge-progress"),
    path("<int:pk>/", ChallengeDetailView.as_view(), name="challenge-detail"),
    path(
        "<int:pk>/submissions/",
        ChallengeSubmissionHistoryView.as_view(),
        name="challenge-submissions",
    ),
]


