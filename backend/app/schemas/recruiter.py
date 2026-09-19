from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.profile import PublicProfileAchievementItem, PublicProfileActivityItem, SkillDimensionItem


class CandidateSummaryItem(BaseModel):
    user_id: int
    username: str
    overall_skill_score: Optional[int] = None
    total_points: int
    challenges_completed: int
    challenges_attempted: int
    average_score: Optional[float] = None
    completion_percentage: float
    achievements_count: int

    model_config = ConfigDict(from_attributes=True)


class CandidateListResponse(BaseModel):
    results: List[CandidateSummaryItem]


class CandidateMetrics(BaseModel):
    total_points: int
    challenges_completed: int
    challenges_attempted: int
    average_score: Optional[float] = None
    completion_percentage: float


class CandidateDetailResponse(BaseModel):
    username: str
    overall_skill_score: Optional[int] = None
    skills: Dict[str, SkillDimensionItem]
    metrics: CandidateMetrics
    achievements: List[PublicProfileAchievementItem] = Field(default_factory=list)
    challenge_evidence: List[PublicProfileActivityItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CandidateCompareRequest(BaseModel):
    usernames: List[str] = Field(..., description="List of 2 to 5 candidate usernames to compare")


class CandidateCompareResponse(BaseModel):
    candidates: List[CandidateDetailResponse]
