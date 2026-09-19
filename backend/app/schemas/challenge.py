from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChallengeListResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    difficulty: str
    challenge_type: str
    programming_language: str
    points: int

    model_config = ConfigDict(from_attributes=True)


class ChallengeFileResponse(BaseModel):
    path: str
    is_test: bool
    is_readonly: bool
    content: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("content", mode="after")
    @classmethod
    def mask_test_content(cls, v, info):
        # Security rule: If is_test is True, never expose content
        if info.data.get("is_test"):
            return None
        return v


class ChallengeRepositoryResponse(BaseModel):
    files: List[ChallengeFileResponse]


class ChallengeDetailResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    difficulty: str
    challenge_type: str
    programming_language: str
    starter_code: str
    time_limit: int
    memory_limit: int
    points: int
    repository: Optional[ChallengeRepositoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ChallengeProgressItem(BaseModel):
    challenge_id: int
    title: str
    difficulty: str
    challenge_type: str
    programming_language: str
    status: str  # "NOT_ATTEMPTED", "PASSED", "FAILED"
    best_score: Optional[int] = None
    attempts_count: int = 0
    latest_attempt_at: Optional[str] = None
    points: int


class ProgressSummary(BaseModel):
    total_challenges: int = 0
    attempted_challenges: int = 0
    completed_challenges: int = 0
    completion_percentage: float = 0.0


class ChallengeProgressResponse(BaseModel):
    summary: ProgressSummary
    challenges: List[ChallengeProgressItem]


class SubmissionHistoryEvaluationSummary(BaseModel):
    score: int
    tests_total: int
    tests_passed: int
    tests_failed: int
    execution_time: float
    memory_used: float
    evaluated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChallengeSubmissionHistoryResponse(BaseModel):
    id: int
    challenge: int
    challenge_title: str
    challenge_slug: str
    language: str
    status: str
    score: int
    created_at: str
    evaluation: Optional[SubmissionHistoryEvaluationSummary] = None

    model_config = ConfigDict(from_attributes=True)
