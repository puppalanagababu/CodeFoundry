from django.contrib import admin
from .models import Challenge, ChallengeFile, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


class ChallengeFileInline(admin.TabularInline):
    model = ChallengeFile
    extra = 1
    fields = ("path", "is_test", "is_readonly", "content")


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

    inlines = [TestCaseInline, ChallengeFileInline]


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "challenge",
        "points",
        "is_hidden",
        "is_active",
        "created_at",
    )

    list_filter = (
        "challenge",
        "is_hidden",
        "is_active",
    )

    search_fields = (
        "name",
        "challenge__title",
    )


@admin.register(ChallengeFile)
class ChallengeFileAdmin(admin.ModelAdmin):
    list_display = (
        "path",
        "challenge",
        "is_test",
        "is_readonly",
        "created_at",
    )

    list_filter = (
        "challenge",
        "is_test",
        "is_readonly",
    )

    search_fields = (
        "path",
        "challenge__title",
    )