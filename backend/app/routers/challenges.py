from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.challenge import Challenge, ChallengeType, Difficulty
from app.models.submission import Submission
from app.models.user import User
from app.schemas.challenge import (ChallengeDetailResponse,ChallengeFileResponse,ChallengeListResponse,ChallengeProgressResponse,ChallengeRepositoryResponse,ChallengeSubmissionHistoryResponse,SubmissionHistoryEvaluationSummary,)
from app.schemas.common import PaginatedResponse, paginate_queryset
from app.services.progress_service import ChallengeProgressService

router = APIRouter(prefix="/api/challenges", tags=["Challenges"])
progress_service = ChallengeProgressService()


@router.get(
    "/progress/",
    response_model=ChallengeProgressResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/progress",
    response_model=ChallengeProgressResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_challenge_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns user progress and attempt metrics aggregated across all active challenges.
    """
    return progress_service.get_user_progress(current_user, db)


@router.get(
    "/",
    response_model=PaginatedResponse[ChallengeListResponse],
    status_code=status.HTTP_200_OK,
)
@router.get(
    "",
    response_model=PaginatedResponse[ChallengeListResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def list_challenges(
    request: Request,
    search: Optional[str] = Query(None, description="Search keyword in title, description, or slug"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    challenge_type: Optional[str] = Query(None, description="Filter by challenge type"),
    programming_language: Optional[str] = Query(None, description="Filter by programming language"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists active challenges with searching, filtering, and pagination.
    """
    query = db.query(Challenge).filter(Challenge.is_active == True)

    # Search filter
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Challenge.title.ilike(term),
                Challenge.description.ilike(term),
                Challenge.slug.ilike(term),
            )
        )

    # Difficulty filter
    if difficulty and difficulty.strip():
        diff_upper = difficulty.strip().upper()
        valid_difficulties = [d.value for d in Difficulty]
        if diff_upper not in valid_difficulties:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Invalid difficulty '{difficulty}'. Valid choices are: {valid_difficulties}."},
            )
        query = query.filter(Challenge.difficulty == diff_upper)

    # Challenge type filter
    if challenge_type and challenge_type.strip():
        ct_upper = challenge_type.strip().upper()
        valid_types = [ct.value for ct in ChallengeType]
        if ct_upper not in valid_types:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Invalid challenge_type '{challenge_type}'. Valid choices are: {valid_types}."},
            )
        query = query.filter(Challenge.challenge_type == ct_upper)

    # Programming language filter
    if programming_language and programming_language.strip():
        query = query.filter(
            func.lower(Challenge.programming_language) == programming_language.strip().lower()
        )

    # Deterministic ordering
    query = query.order_by(Challenge.created_at.desc(), Challenge.id.desc())

    total_count = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    result_items = [ChallengeListResponse.model_validate(item) for item in items]
    return paginate_queryset(result_items, total_count, page, page_size, request)


@router.get(
    "/{challenge_id}/",
    response_model=ChallengeDetailResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/{challenge_id}",
    response_model=ChallengeDetailResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_challenge_detail(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves challenge details. Hidden test file contents are masked.
    """
    challenge = (
        db.query(Challenge)
        .options(joinedload(Challenge.files))
        .filter(Challenge.id == challenge_id, Challenge.is_active == True)
        .first()
    )
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Challenge matches the given query.",
        )

    # Construct repository structure
    repository = None
    if challenge.files:
        file_list = [
            ChallengeFileResponse(
                path=cf.path,
                is_test=cf.is_test,
                is_readonly=cf.is_readonly,
                content=None if cf.is_test else cf.content,
            )
            for cf in challenge.files
        ]
        repository = ChallengeRepositoryResponse(files=file_list)

    return ChallengeDetailResponse(
        id=challenge.id,
        title=challenge.title,
        slug=challenge.slug,
        description=challenge.description,
        difficulty=challenge.difficulty,
        challenge_type=challenge.challenge_type,
        programming_language=challenge.programming_language,
        starter_code=challenge.starter_code,
        time_limit=challenge.time_limit,
        memory_limit=challenge.memory_limit,
        points=challenge.points,
        repository=repository,
    )


@router.get(
    "/{challenge_id}/submissions/",
    response_model=PaginatedResponse[ChallengeSubmissionHistoryResponse],
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/{challenge_id}/submissions",
    response_model=PaginatedResponse[ChallengeSubmissionHistoryResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_challenge_submissions(
    challenge_id: int,
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves user-scoped submission history for a specific challenge.
    """
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Challenge matches the given query.",
        )

    query = (
        db.query(Submission)
        .options(
            joinedload(Submission.evaluation),
            joinedload(Submission.challenge),
        )
        .filter(
            Submission.user_id == current_user.id,
            Submission.challenge_id == challenge_id,
        )
        .order_by(Submission.submitted_at.desc(), Submission.id.desc())
    )

    total_count = query.count()
    offset = (page - 1) * page_size
    submissions = query.offset(offset).limit(page_size).all()

    results: List[ChallengeSubmissionHistoryResponse] = []
    for sub in submissions:
        eval_summary = None
        if sub.evaluation:
            eval_summary = SubmissionHistoryEvaluationSummary(
                score=sub.evaluation.score,
                tests_total=sub.evaluation.tests_total,
                tests_passed=sub.evaluation.tests_passed,
                tests_failed=sub.evaluation.tests_failed,
                execution_time=sub.evaluation.execution_time,
                memory_used=sub.evaluation.memory_used,
                evaluated_at=(
                    sub.evaluation.evaluated_at.isoformat()
                    if sub.evaluation.evaluated_at
                    else None
                ),
            )

        results.append(
            ChallengeSubmissionHistoryResponse(
                id=sub.id,
                challenge=sub.challenge_id,
                challenge_title=sub.challenge.title if sub.challenge else "",
                challenge_slug=sub.challenge.slug if sub.challenge else "",
                language=sub.language,
                status=sub.status,
                score=sub.score,
                created_at=sub.submitted_at.isoformat() if sub.submitted_at else "",
                evaluation=eval_summary,
            )
        )

    return paginate_queryset(results, total_count, page, page_size, request)
