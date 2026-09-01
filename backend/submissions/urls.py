from django.urls import path
from .views import (
    BestSubmissionsView,
    SubmissionDetailView,
    SubmissionListCreateView,
)

urlpatterns = [
    path("", SubmissionListCreateView.as_view(), name="submission-list-create"),
    path("best/", BestSubmissionsView.as_view(), name="submission-best"),
    path("<int:pk>/", SubmissionDetailView.as_view(), name="submission-detail"),
]


