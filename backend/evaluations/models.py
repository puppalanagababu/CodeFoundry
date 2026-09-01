from django.db import models


class Evaluation(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="evaluation",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    score = models.PositiveIntegerField(
        default=0,
    )

    tests_total = models.PositiveIntegerField(
        default=0,
    )

    tests_passed = models.PositiveIntegerField(
        default=0,
    )

    tests_failed = models.PositiveIntegerField(
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

    stdout = models.TextField(
        blank=True,
    )

    stderr = models.TextField(
        blank=True,
    )

    test_results = models.JSONField(
        default=list,
        blank=True,
    )

    evaluated_at = models.DateTimeField(
        null=True,
        blank=True,
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Evaluation #{self.id} - {self.submission}"