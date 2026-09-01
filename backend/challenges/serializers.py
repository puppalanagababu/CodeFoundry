from rest_framework import serializers
from .models import Challenge, ChallengeFile


class ChallengeFileSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = ChallengeFile
        fields = [
            "path",
            "is_test",
            "is_readonly",
            "content",
        ]

    def get_content(self, obj):
        # Security rule: If is_test=True, NEVER return content.
        if obj.is_test:
            return None
        return obj.content


class ChallengeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "difficulty",
            "challenge_type",
            "programming_language",
            "points",
        ]


class ChallengeDetailSerializer(serializers.ModelSerializer):
    repository = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "difficulty",
            "challenge_type",
            "programming_language",
            "starter_code",
            "time_limit",
            "memory_limit",
            "points",
            "repository",
        ]

    def get_repository(self, obj):
        try:
            if hasattr(obj, "files"):
                file_list = list(obj.files.all())
                if file_list:
                    return {
                        "files": ChallengeFileSerializer(file_list, many=True).data
                    }
        except Exception:
            pass
        return None

