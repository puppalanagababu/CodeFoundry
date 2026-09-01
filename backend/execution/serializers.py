from rest_framework import serializers


class CodeExecutionRequestSerializer(serializers.Serializer):
    code = serializers.CharField(required=False, allow_blank=True, default="")
    files = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        allow_empty=True,
    )
    entrypoint = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(default="Python", required=False)
    stdin = serializers.CharField(default="", required=False, allow_blank=True)
    timeout = serializers.IntegerField(
        default=5, required=False, min_value=1, max_value=15
    )

    def validate(self, attrs):
        code = attrs.get("code", "")
        files = attrs.get("files", {})

        if not code and not files:
            raise serializers.ValidationError(
                {"code": "Either 'code' or non-empty 'files' repository map must be provided."}
            )
        return attrs

