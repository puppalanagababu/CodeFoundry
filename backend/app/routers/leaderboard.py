from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.leaderboard import LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])
leaderboard_service = LeaderboardService()


@router.get(
    "/",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the ranked developer leaderboard based on evaluated challenge metrics.
    """
    results = leaderboard_service.get_leaderboard(db, current_user_id=current_user.id)
    return LeaderboardResponse(results=results)
