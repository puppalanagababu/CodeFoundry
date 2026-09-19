from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get(
    "/",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns user dashboard metrics including overview statistics, recent submissions, and difficulty progress.
    """
    return dashboard_service.get_dashboard(db, current_user.id)
