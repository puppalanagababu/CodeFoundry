from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CodeExecutionRequestSerializer
from .services import ExecutionService


class CodeExecutionView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, execution_service=None, **kwargs):
        super().__init__(**kwargs)
        self.execution_service = execution_service or ExecutionService()

    def post(self, request, *args, **kwargs):
        serializer = CodeExecutionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data.get("code", "")
        files = serializer.validated_data.get("files")
        entrypoint = serializer.validated_data.get("entrypoint", "")
        language = serializer.validated_data.get("language", "Python")
        stdin_data = serializer.validated_data.get("stdin", "")
        timeout = serializer.validated_data.get("timeout", 5)

        # Normalize stdin_data to ensure trailing newline if non-empty
        if stdin_data and not stdin_data.endswith("\n"):
            stdin_data = stdin_data + "\n"
        elif not stdin_data:
            stdin_data = None

        try:
            result = self.execution_service.execute(
                code=code,
                language=language,
                stdin_data=stdin_data,
                timeout=timeout,
                files=files,
                entrypoint=entrypoint,
            )

            is_success = result.exit_code == 0
            response_data = {
                "status": "SUCCESS" if is_success else "FAILED",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
                "exit_code": result.exit_code,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "status": "ERROR",
                    "stdout": "",
                    "stderr": f"Execution error: {str(e)}",
                    "execution_time": 0.0,
                    "exit_code": 1,
                },
                status=status.HTTP_200_OK,
            )
