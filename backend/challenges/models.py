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


class TestCase(models.Model):
    challenge = models.ForeignKey(
        "challenges.Challenge",
        on_delete=models.CASCADE,
        related_name="test_cases",
    )
    name = models.CharField(max_length=100)
    input_data = models.TextField(blank=True, default="")
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.challenge.title} - {self.name} ({self.points} pts)"


class ChallengeFile(models.Model):
    challenge = models.ForeignKey(
        "challenges.Challenge",
        on_delete=models.CASCADE,
        related_name="files",
    )
    path = models.CharField(
        max_length=255,
        help_text="Relative repository file path (e.g., 'src/main.py', 'README.md').",
    )
    content = models.TextField(
        blank=True,
        default="",
    )
    is_test = models.BooleanField(
        default=False,
        help_text="Identifies whether this file is a test file.",
    )
    is_readonly = models.BooleanField(
        default=False,
        help_text="Identifies whether this file is read-only for students.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["path"]
        unique_together = [("challenge", "path")]

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.path or not self.path.strip():
            raise ValidationError({"path": "Path cannot be empty."})

        # Normalize path
        normalized = self.path.strip().replace("\\", "/")
        if normalized.startswith("/"):
            raise ValidationError(
                {"path": "Path must be relative, cannot start with '/'."}
            )

        segments = normalized.split("/")
        for seg in segments:
            if seg in ["..", "."] or not seg:
                raise ValidationError(
                    {"path": f"Invalid path segment '{seg}' or path traversal detected."}
                )
        self.path = normalized

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.challenge.title} - {self.path}"
