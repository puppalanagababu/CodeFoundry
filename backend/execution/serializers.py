from rest_framework import serializers


class CodeExecutionRequestSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, allow_blank=False)
    language = serializers.CharField(default="Python", required=False)
    stdin = serializers.CharField(default="", required=False, allow_blank=True)
    timeout = serializers.IntegerField(
        default=5, required=False, min_value=1, max_value=15
    )
