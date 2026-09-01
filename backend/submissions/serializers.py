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
        ]


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
