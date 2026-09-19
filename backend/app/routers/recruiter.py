from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.schemas.recruiter import (
    CandidateCompareRequest,
    CandidateCompareResponse,
    CandidateDetailResponse,
    CandidateListResponse,
)
from app.services.recruiter_service import RecruiterDashboardService

router = APIRouter(prefix="/api/recruiter", tags=["Recruiter"])
recruiter_service = RecruiterDashboardService()


@router.get(
    "/candidates/",
    response_model=CandidateListResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/candidates",
    response_model=CandidateListResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def list_candidates(
    search: Optional[str] = Query("", description="Search by username"),
    min_skill_score: Optional[int] = Query(None, description="Filter by minimum overall skill score"),
    challenge_type: Optional[str] = Query(None, description="Filter by challenge type attempted"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER, UserRole.ADMIN)),
):
    """
    Retrieves filtered and ranked candidate engineering readiness summaries for authorized recruiters.
    """
    candidates = recruiter_service.get_candidates(
        db=db,
        search=search or "",
        min_skill_score=min_skill_score,
        challenge_type=challenge_type,
    )
    return CandidateListResponse(results=candidates)


@router.post(
    "/candidates/compare/",
    response_model=CandidateCompareResponse,
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/candidates/compare",
    response_model=CandidateCompareResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def compare_candidates_post(
    payload: CandidateCompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER, UserRole.ADMIN)),
):
    """
    Side-by-side comparison of 2 to 5 candidates.
    """
    usernames = payload.usernames or []
    if len(usernames) < 2 or len(usernames) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comparison requires between 2 and 5 candidates.",
        )

    candidates = recruiter_service.compare_candidates(db, usernames=usernames)
    return CandidateCompareResponse(candidates=candidates)


@router.get(
    "/candidates/compare/",
    response_model=CandidateCompareResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/candidates/compare",
    response_model=CandidateCompareResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def compare_candidates_get(
    usernames: Optional[str] = Query(None, description="Comma-separated candidate usernames"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER, UserRole.ADMIN)),
):
    """
    GET endpoint for side-by-side candidate comparison (comma-separated usernames).
    """
    if not usernames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comparison requires between 2 and 5 candidates.",
        )

    user_list = [u.strip() for u in usernames.split(",") if u.strip()]
    if len(user_list) < 2 or len(user_list) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comparison requires between 2 and 5 candidates.",
        )

    candidates = recruiter_service.compare_candidates(db, usernames=user_list)
    return CandidateCompareResponse(candidates=candidates)


@router.get(
    "/candidates/{username}/",
    response_model=CandidateDetailResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/candidates/{username}",
    response_model=CandidateDetailResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_candidate_detail(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER, UserRole.ADMIN)),
):
    """
    Retrieves detailed, recruiter-safe engineering assessment and challenge evidence for a candidate.
    """
    candidate = recruiter_service.get_candidate_detail(db, username=username)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )
    return candidate
