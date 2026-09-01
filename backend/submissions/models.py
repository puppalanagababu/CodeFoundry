from django.conf import settings
from django.db import models


class Submission(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Failed"
        ERROR = "ERROR", "Error"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    challenge = models.ForeignKey(
        "challenges.Challenge",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    code = models.TextField()

    language = models.CharField(
        max_length=50,
        default="Python",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    score = models.PositiveIntegerField(
        default=0,
    )

    execution_time = models.FloatField(
        default=0,
        help_text="Execution time in seconds.",
    )

    memory_used = models.FloatField(
        default=0,
        help_text="Memory used in MB.",
    )

    test_results = models.JSONField(
        default=dict,
        blank=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"