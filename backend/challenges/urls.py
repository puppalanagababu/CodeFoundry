from django.urls import path
from submissions.views import ChallengeSubmissionHistoryView
from .views import ChallengeDetailView, ChallengeListView

urlpatterns = [
    path("", ChallengeListView.as_view(), name="challenge-list"),
    path("<int:pk>/", ChallengeDetailView.as_view(), name="challenge-detail"),
    path(
        "<int:pk>/submissions/",
        ChallengeSubmissionHistoryView.as_view(),
        name="challenge-submissions",
    ),
]

