from django.conf import settings
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

    skill_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Deterministic skill score breakdown across dimensions.",
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


class Achievement(models.Model):
    class RequirementType(models.TextChoices):
        BUG_FIX_COUNT = "BUG_FIX_COUNT", "Bug Fix Count"
        SECURITY_COUNT = "SECURITY_COUNT", "Security Count"
        PERFORMANCE_COUNT = "PERFORMANCE_COUNT", "Performance Count"
        TESTING_COUNT = "TESTING_COUNT", "Testing Count"
        PERFECT_SCORE_COUNT = "PERFECT_SCORE_COUNT", "Perfect Score Count"
        TOTAL_COMPLETED_COUNT = "TOTAL_COMPLETED_COUNT", "Total Completed Count"

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="🏆")
    requirement_type = models.CharField(
        max_length=50,
        choices=RequirementType.choices,
    )
    requirement_value = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="user_achievements",
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "achievement")]
        ordering = ["-earned_at", "achievement__name"]

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"