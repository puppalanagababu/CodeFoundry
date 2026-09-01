from rest_framework import serializers
from challenges.models import Challenge
from evaluations.models import Evaluation
from .models import Submission


class SubmissionCreateSerializer(serializers.ModelSerializer):
    challenge = serializers.PrimaryKeyRelatedField(
        queryset=Challenge.objects.all()
    )
    code = serializers.CharField(required=True, allow_blank=False)
    language = serializers.CharField(default="Python", required=False)

    class Meta:
        model = Submission
        fields = ["challenge", "code", "language"]


class EvaluationSerializer(serializers.ModelSerializer):
    test_results = serializers.SerializerMethodField()

    class Meta:
        model = Evaluation
        fields = [
            "status",
            "score",
            "tests_total",
            "tests_passed",
            "tests_failed",
            "stdout",
            "stderr",
            "execution_time",
            "memory_used",
            "test_results",
        ]

    def get_test_results(self, obj):
        results = getattr(obj, "test_results", [])
        if not isinstance(results, list):
            return []
        sanitized = []
        for r in results:
            item = {
                "test_case_id": r.get("test_case_id"),
                "name": r.get("name"),
                "passed": r.get("passed", False),
                "points": r.get("points", 0),
                "max_points": r.get("max_points", 0),
                "execution_time": r.get("execution_time", 0.0),
                "is_hidden": r.get("is_hidden", False),
            }
            if not r.get("is_hidden", False):
                item["input_data"] = r.get("input_data", "")
                item["expected_output"] = r.get("expected_output", "")
                item["actual_output"] = r.get("stdout", "")
                item["stderr"] = r.get("stderr", "")
            sanitized.append(item)
        return sanitized



class SubmissionResponseSerializer(serializers.ModelSerializer):
    submission_id = serializers.IntegerField(source="id", read_only=True)
    challenge = serializers.PrimaryKeyRelatedField(
        read_only=True, source="challenge_id"
    )
    evaluation = EvaluationSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "submission_id",
            "challenge",
            "status",
            "score",
            "evaluation",
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    submission_id = serializers.IntegerField(source="id", read_only=True)
    challenge = serializers.PrimaryKeyRelatedField(
        read_only=True, source="challenge_id"
    )
    evaluation = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "submission_id",
            "challenge",
            "status",
            "score",
            "evaluation",
        ]

    def get_evaluation(self, obj):
        try:
            if hasattr(obj, "evaluation") and obj.evaluation is not None:
                return EvaluationSerializer(obj.evaluation).data
        except Exception:
            pass
        return None


class EvaluationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = [
            "score",
            "tests_total",
            "tests_passed",
            "tests_failed",
            "execution_time",
            "memory_used",
            "evaluated_at",
        ]


class SubmissionHistorySerializer(serializers.ModelSerializer):
    challenge = serializers.IntegerField(source="challenge_id", read_only=True)
    challenge_title = serializers.CharField(
        source="challenge.title", read_only=True
    )
    challenge_slug = serializers.CharField(
        source="challenge.slug", read_only=True
    )
    created_at = serializers.DateTimeField(
        source="submitted_at", read_only=True
    )
    evaluation = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id",
            "challenge",
            "challenge_title",
            "challenge_slug",
            "language",
            "status",
            "score",
            "created_at",
            "evaluation",
        ]

    def get_evaluation(self, obj):
        try:
            if hasattr(obj, "evaluation") and obj.evaluation is not None:
                return EvaluationSummarySerializer(obj.evaluation).data
        except Exception:
            pass
        return None


