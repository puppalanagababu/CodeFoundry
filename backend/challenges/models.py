from django.db import models


class Challenge(models.Model):

    class Difficulty(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"
        EXPERT = "EXPERT", "Expert"

    class ChallengeType(models.TextChoices):
        BUG_FIX = "BUG_FIX", "Bug Fix"
        FEATURE = "FEATURE", "Feature"
        API = "API", "API Integration"
        DATABASE = "DATABASE", "Database"
        PERFORMANCE = "PERFORMANCE", "Performance"
        SECURITY = "SECURITY", "Security"
        TESTING = "TESTING", "Testing"
        CODE_REVIEW = "CODE_REVIEW", "Code Review"
        DEBUGGING = "DEBUGGING", "Debugging"

    title = models.CharField(max_length=200)

    slug = models.SlugField(
        unique=True
    )

    description = models.TextField()

    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
    )

    challenge_type = models.CharField(
        max_length=20,
        choices=ChallengeType.choices,
        default=ChallengeType.BUG_FIX,
    )

    programming_language = models.CharField(
        max_length=50,
        default="Python",
    )

    starter_code = models.TextField(
        blank=True,
    )

    time_limit = models.PositiveIntegerField(
        default=10,
        help_text="Maximum execution time in seconds.",
    )

    memory_limit = models.PositiveIntegerField(
        default=256,
        help_text="Maximum memory in MB.",
    )

    points = models.PositiveIntegerField(
        default=100,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.title