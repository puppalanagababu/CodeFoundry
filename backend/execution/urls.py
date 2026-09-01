from django.urls import path
from .views import CodeExecutionView

urlpatterns = [
    path("run/", CodeExecutionView.as_view(), name="code-execution-run"),
]
