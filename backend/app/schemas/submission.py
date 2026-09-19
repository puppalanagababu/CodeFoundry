from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubmissionCreateRequest(BaseModel):
    challenge: int = Field(..., description="Challenge ID")
    code: Optional[str] = Field(default="", description="Submitted single-file code")
    files: Optional[Dict[str, str]] = Field(default_factory=dict, description="Multi-file dictionary")
    language: Optional[str] = Field(default="Python", description="Programming language")

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_code_or_files(self) -> "SubmissionCreateRequest":
        code = self.code or ""
        files = self.files or {}

        if not code and not files:
            raise ValueError("Either 'code' or 'files' must be provided.")

        # Sanitize files dictionary: strip any client-submitted test files
        if files and isinstance(files, dict):
            sanitized_files = {}
            for path, content in files.items():
                if path.startswith("tests/") or path.endswith("_test.py") or "test_" in path:
                    # Ignore/strip client-submitted test files (server files are authoritative)
                    continue
                sanitized_files[path] = content
            self.files = sanitized_files

            # For backward compatibility, populate code if blank
            if not code:
                py_content = next(
                    (content for path, content in sanitized_files.items() if path.endswith(".py")),
                    ""
                )
                self.code = py_content

        return self


class TestCaseResult(BaseModel):
    test_case_id: Optional[int] = None
    name: Optional[str] = None
    passed: bool = False
    points: int = 0
    max_points: int = 0
    execution_time: float = 0.0
    is_hidden: bool = False
    input_data: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    stderr: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "TestCaseResult":
        is_hidden = raw.get("is_hidden", False)
        item = cls(
            test_case_id=raw.get("test_case_id"),
            name=raw.get("name"),
            passed=raw.get("passed", False),
            points=raw.get("points", 0),
            max_points=raw.get("max_points", 0),
            execution_time=raw.get("execution_time", 0.0),
            is_hidden=is_hidden,
        )
        if not is_hidden:
            item.input_data = raw.get("input_data", "")
            item.expected_output = raw.get("expected_output", "")
            item.actual_output = raw.get("stdout", "")
            item.stderr = raw.get("stderr", "")
        return item


class EvaluationDetailResponse(BaseModel):
    status: str
    score: int
    tests_total: int
    tests_passed: int
    tests_failed: int
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    memory_used: float = 0.0
    test_results: List[TestCaseResult] = Field(default_factory=list)
    skill_breakdown: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class EvaluationSummaryResponse(BaseModel):
    score: int
    tests_total: int
    tests_passed: int
    tests_failed: int
    execution_time: float
    memory_used: float
    evaluated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionCreateResponse(BaseModel):
    submission_id: int
    challenge: int
    status: str
    score: int
    message: str = "Submission queued for evaluation."


class SubmissionDetailResponse(BaseModel):
    submission_id: int
    challenge: int
    status: str
    score: int
    evaluation: Optional[EvaluationDetailResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionHistoryItem(BaseModel):
    id: int
    challenge: int
    challenge_title: str
    challenge_slug: str
    language: str
    status: str
    score: int
    created_at: str
    evaluation: Optional[EvaluationSummaryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BestSubmissionItem(BaseModel):
    challenge: int
    challenge_title: str
    best_score: int
    attempts: int
    latest_status: Optional[str] = None
    latest_submission_id: Optional[int] = None


class BestSubmissionsResponse(BaseModel):
    results: List[BestSubmissionItem]
