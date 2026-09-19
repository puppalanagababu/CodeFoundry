from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.challenge import Challenge
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse, paginate_queryset
from app.schemas.submission import (
    BestSubmissionItem,
    BestSubmissionsResponse,
    EvaluationDetailResponse,
    EvaluationSummaryResponse,
    SubmissionCreateRequest,
    SubmissionCreateResponse,
    SubmissionDetailResponse,
    SubmissionHistoryItem,
    TestCaseResult,
)
from app.tasks.evaluation_tasks import evaluate_submission

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])


@router.get(
    "/best/",
    response_model=BestSubmissionsResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/best",
    response_model=BestSubmissionsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_best_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns aggregated best submission metrics per challenge for the current user.
    """
    user_submissions = (
        db.query(Submission)
        .options(joinedload(Submission.challenge))
        .filter(Submission.user_id == current_user.id)
        .order_by(Submission.challenge_id.asc(), Submission.submitted_at.desc(), Submission.id.desc())
        .all()
    )

    # Group by challenge_id preserving order
    challenge_groups = {}
    for sub in user_submissions:
        ch_id = sub.challenge_id
        if ch_id not in challenge_groups:
            challenge_groups[ch_id] = []
        challenge_groups[ch_id].append(sub)

    results: List[BestSubmissionItem] = []
    for ch_id, ch_subs in challenge_groups.items():
        latest_sub = ch_subs[0]
        best_score = max((s.score for s in ch_subs), default=0)
        attempts = len(ch_subs)

        results.append(
            BestSubmissionItem(
                challenge=ch_id,
                challenge_title=latest_sub.challenge.title if latest_sub.challenge else "",
                best_score=best_score,
                attempts=attempts,
                latest_status=latest_sub.status if latest_sub else None,
                latest_submission_id=latest_sub.id if latest_sub else None,
            )
        )

    return BestSubmissionsResponse(results=results)


@router.get(
    "/",
    response_model=PaginatedResponse[SubmissionHistoryItem],
    status_code=status.HTTP_200_OK,
)
@router.get(
    "",
    response_model=PaginatedResponse[SubmissionHistoryItem],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def list_submissions(
    request: Request,
    challenge: Optional[str] = Query(None, description="Filter by challenge ID"),
    status_param: Optional[str] = Query(None, alias="status", description="Filter by submission status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists current user's submissions with filtering and pagination.
    """
    query = (
        db.query(Submission)
        .options(
            joinedload(Submission.challenge),
            joinedload(Submission.evaluation),
        )
        .filter(Submission.user_id == current_user.id)
    )

    # Challenge filter
    if challenge:
        try:
            challenge_id = int(challenge)
            query = query.filter(Submission.challenge_id == challenge_id)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Invalid challenge id '{challenge}'."},
            )

    # Status filter
    if status_param:
        status_upper = status_param.strip().upper()
        valid_statuses = [s.value for s in SubmissionStatus]
        if status_upper not in valid_statuses:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Invalid status '{status_param}'. Valid choices are: {valid_statuses}."},
            )
        query = query.filter(Submission.status == status_upper)

    query = query.order_by(Submission.submitted_at.desc(), Submission.id.desc())

    total_count = query.count()
    offset = (page - 1) * page_size
    submissions = query.offset(offset).limit(page_size).all()

    items: List[SubmissionHistoryItem] = []
    for sub in submissions:
        eval_summary = None
        if sub.evaluation:
            eval_summary = EvaluationSummaryResponse(
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

        items.append(
            SubmissionHistoryItem(
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

    return paginate_queryset(items, total_count, page, page_size, request)


@router.post(
    "/",
    response_model=SubmissionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "",
    response_model=SubmissionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_submission(
    payload: SubmissionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits code/repository solution for evaluation and dispatches Celery background worker task.
    """
    # Verify challenge existence
    challenge = (
        db.query(Challenge)
        .filter(Challenge.id == payload.challenge)
        .first()
    )
    if not challenge:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"challenge": f"Invalid pk \"{payload.challenge}\" - object does not exist."},
        )

    # Create submission record
    submission = Submission(
        user_id=current_user.id,
        challenge_id=payload.challenge,
        code=payload.code or "",
        files=payload.files or {},
        language=payload.language or "Python",
        status=SubmissionStatus.PENDING.value,
        score=0,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Dispatch asynchronous background task via Celery
    evaluate_submission.delay(submission.id)

    return SubmissionCreateResponse(
        submission_id=submission.id,
        challenge=submission.challenge_id,
        status=submission.status,
        score=submission.score,
        message="Submission queued for evaluation.",
    )


@router.get(
    "/{submission_id}/",
    response_model=SubmissionDetailResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/{submission_id}",
    response_model=SubmissionDetailResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_submission_detail(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves full submission and evaluation details for current user. Masks hidden test data.
    """
    submission = (
        db.query(Submission)
        .options(
            joinedload(Submission.challenge),
            joinedload(Submission.evaluation),
        )
        .filter(
            Submission.id == submission_id,
            Submission.user_id == current_user.id,
        )
        .first()
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Submission matches the given query.",
        )

    eval_detail = None
    if submission.evaluation:
        raw_test_results = submission.evaluation.test_results or []
        sanitized_test_results = [
            TestCaseResult.from_raw(r) for r in raw_test_results
        ]

        eval_detail = EvaluationDetailResponse(
            status=submission.evaluation.status,
            score=submission.evaluation.score,
            tests_total=submission.evaluation.tests_total,
            tests_passed=submission.evaluation.tests_passed,
            tests_failed=submission.evaluation.tests_failed,
            stdout=submission.evaluation.stdout or "",
            stderr=submission.evaluation.stderr or "",
            execution_time=submission.evaluation.execution_time or 0.0,
            memory_used=submission.evaluation.memory_used or 0.0,
            test_results=sanitized_test_results,
            skill_breakdown=submission.evaluation.skill_breakdown or {},
        )

    return SubmissionDetailResponse(
        submission_id=submission.id,
        challenge=submission.challenge_id,
        status=submission.status,
        score=submission.score,
        evaluation=eval_detail,
    )
