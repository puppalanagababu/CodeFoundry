from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class LeaderboardItem(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int
    challenges_completed: int
    average_score: float
    overall_skill_score: Optional[int] = None
    is_current_user: bool = False

    model_config = ConfigDict(from_attributes=True)


class LeaderboardResponse(BaseModel):
    results: List[LeaderboardItem]
