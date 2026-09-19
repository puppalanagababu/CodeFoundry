from typing import Dict, Optional
from pydantic import BaseModel, Field, model_validator


class CodeExecutionRequest(BaseModel):
    code: Optional[str] = ""
    files: Optional[Dict[str, str]] = None
    entrypoint: Optional[str] = ""
    language: str = "Python"
    stdin: Optional[str] = ""
    timeout: int = Field(default=5, ge=1, le=15)

    @model_validator(mode="after")
    def validate_code_or_files(self):
        has_code = bool(self.code and self.code.strip())
        has_files = bool(self.files and isinstance(self.files, dict) and len(self.files) > 0)
        if not has_code and not has_files:
            raise ValueError("Either 'code' or non-empty 'files' repository map must be provided.")
        return self


class CodeExecutionResponse(BaseModel):
    status: str
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    exit_code: int = 0
