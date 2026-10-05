from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class SkillDimensionItem(BaseModel):
    score: Optional[int] = None
    sample_size: int = 0
    total_weight: Optional[float] = 0.0
    status: str  # "measured", "insufficient_data", "not_measured"


class SkillProfileResponse(BaseModel):
    overall_score: Optional[int] = None
    skills: Dict[str, SkillDimensionItem]
    total_evaluations_analyzed: int = 0
    measured_dimensions_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class PublicProfileActivityItem(BaseModel):
    challenge_id: int
    challenge_title: str
    challenge_type: str
    difficulty: str
    score: int
    status: str
    evaluated_at: Optional[str] = None


class PublicProfileAchievementItem(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    earned_at: Optional[str] = None


class PublicProfileResponse(BaseModel):
    username: str
    overall_skill_score: Optional[int] = None
    skill_breakdown: Dict[str, SkillDimensionItem]
    challenges_completed: int = 0
    challenges_attempted: int = 0
    completion_percentage: float = 0.0
    average_score: Optional[float] = None
    total_points: int = 0
    achievements: List[PublicProfileAchievementItem] = []
    recent_activity: List[PublicProfileActivityItem] = []

    model_config = ConfigDict(from_attributes=True)


class AchievementItem(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    requirement_type: Optional[str] = None
    requirement_value: Optional[int] = None
    earned_at: Optional[str] = None
    is_earned: bool = False


class UserAchievementsResponse(BaseModel):
    results: List[PublicProfileAchievementItem]
