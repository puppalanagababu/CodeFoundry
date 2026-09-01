from django.contrib import admin
from .models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "challenge_type",
        "difficulty",
        "programming_language",
        "points",
        "is_active",
        "created_at",
    )

    list_filter = (
        "difficulty",
        "challenge_type",
        "programming_language",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
    )

    prepopulated_fields = {
        "slug": ("title",)
    }