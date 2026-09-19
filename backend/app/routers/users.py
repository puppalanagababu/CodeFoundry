from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.evaluation import Achievement
from app.models.user import User
from app.schemas.profile import (
    AchievementItem,
    PublicProfileResponse,
    SkillProfileResponse,
    UserAchievementsResponse,
)
from app.services.achievement_service import AchievementService
from app.services.profile_service import PublicProfileService
from app.services.skill_profile_service import SkillProfileService

router = APIRouter(prefix="/api", tags=["Users & Profiles"])
skill_profile_service = SkillProfileService()
public_profile_service = PublicProfileService()
achievement_service = AchievementService()


@router.get(
    "/users/skill-profile/",
    response_model=SkillProfileResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/users/skill-profile",
    response_model=SkillProfileResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_user_skill_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the deterministic aggregated skill profile for the current authenticated user.
    """
    return skill_profile_service.get_user_profile(db, current_user.id)


@router.get(
    "/users/profile/{username}/",
    response_model=PublicProfileResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/users/profile/{username}",
    response_model=PublicProfileResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_public_profile(
    username: str,
    db: Session = Depends(get_db),
):
    """
    Returns the safe, read-only developer public profile for the specified username.
    """
    profile = public_profile_service.get_public_profile(db, username=username)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return profile


@router.get(
    "/users/achievements/",
    response_model=UserAchievementsResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/users/achievements",
    response_model=UserAchievementsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_current_user_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the list of earned achievements for the authenticated user.
    """
    achievements = achievement_service.get_user_achievements(db, current_user.id)
    return UserAchievementsResponse(results=achievements)


@router.get(
    "/achievements/",
    response_model=List[AchievementItem],
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/achievements",
    response_model=List[AchievementItem],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def list_all_achievements(
    db: Session = Depends(get_db),
):
    """
    Lists all active achievement definitions available in the system.
    """
    achs = db.query(Achievement).filter(Achievement.is_active == True).order_by(Achievement.id.asc()).all()
    return [
        AchievementItem(
            code=ach.code,
            name=ach.name,
            description=ach.description,
            icon=ach.icon,
            requirement_type=ach.requirement_type,
            requirement_value=ach.requirement_value,
        )
        for ach in achs
    ]
