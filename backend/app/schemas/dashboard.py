from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DashboardOverview(BaseModel):
    challenges_attempted: int
    challenges_passed: int
    total_submissions: int
    average_score: int


class RecentSubmissionItem(BaseModel):
    id: int
    challenge: int
    challenge_title: str
    status: str
    score: int
    language: str
    submitted_at: Optional[str] = None


class DifficultyProgressItem(BaseModel):
    difficulty: str
    attempted: int
    passed: int
    average_score: int


class DashboardResponse(BaseModel):
    overview: DashboardOverview
    recent_submissions: List[RecentSubmissionItem]
    difficulty_progress: List[DifficultyProgressItem]

    model_config = ConfigDict(from_attributes=True)
