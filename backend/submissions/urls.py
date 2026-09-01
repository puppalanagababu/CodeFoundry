from django.urls import path
from .views import SubmissionCreateView

urlpatterns = [
    path("", SubmissionCreateView.as_view(), name="submission-create"),
]
