import logging
from typing import Optional
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.execution import CodeExecutionRequest, CodeExecutionResponse
from execution.services import ExecutionService

logger = logging.getLogger("app.execution")
router = APIRouter(prefix="/api/execution", tags=["Execution"])

execution_service = ExecutionService()


@router.post("/run/", response_model=CodeExecutionResponse, status_code=status.HTTP_200_OK)
@router.post("/run", response_model=CodeExecutionResponse, status_code=status.HTTP_200_OK)
def execute_code(
    payload: CodeExecutionRequest,
    current_user: User = Depends(get_current_user),
):
    code = payload.code or ""
    files = payload.files
    entrypoint = payload.entrypoint or ""
    language = payload.language or "Python"
    stdin_data = payload.stdin or ""
    timeout = payload.timeout

    # Normalize stdin_data to ensure trailing newline if non-empty
    if stdin_data and not stdin_data.endswith("\n"):
        normalized_stdin: Optional[str] = stdin_data + "\n"
    elif not stdin_data:
        normalized_stdin = None
    else:
        normalized_stdin = stdin_data

    try:
        result = execution_service.execute(
            code=code,
            language=language,
            stdin_data=normalized_stdin,
            timeout=timeout,
            files=files,
            entrypoint=entrypoint,
        )

        is_success = result.exit_code == 0
        return CodeExecutionResponse(
            status="SUCCESS" if is_success else "FAILED",
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time=result.execution_time,
            exit_code=result.exit_code,
        )
    except Exception as e:
        logger.warning("Code execution exception: %s", e)
        return CodeExecutionResponse(
            status="ERROR",
            stdout="",
            stderr=f"Execution error: {str(e)}",
            execution_time=0.0,
            exit_code=1,
        )
