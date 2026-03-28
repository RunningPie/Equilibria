"""
Collaboration API - Tech Specs v4.2 Section 7.E

Peer review endpoints for collaborative feedback system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from starlette.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
)

from app.schemas.collaboration import (
    PeerSessionInboxItem, PeerSessionDetail, QuestionInfo,
    ReviewSubmitRequest, ReviewSubmitResult,
    PeerSessionRequest, RateRequest, RateResult
)
from app.schemas.jsend import JSendResponse, jsend_success, jsend_fail, jsend_error
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.core.logging_config import get_loggers, log_assessment_event
from app.core.feedback_scoring import calculate_system_score
from app.core.social_elo import update_theta_social
from app.db.models import User, PeerSession, Question

router = APIRouter(
    prefix="/collaboration",
    tags=["Collaboration"]
)

system_logger, assessment_logger = get_loggers()


@router.get(
    "/inbox",
    response_model=JSendResponse[List[PeerSessionInboxItem]],
    status_code=status.HTTP_200_OK,
    summary="Get reviewer's inbox",
    description="List all pending peer review tasks for the current user as reviewer"
)
async def get_inbox(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get list of peer sessions where current user is the reviewer
    and status is PENDING_REVIEW (waiting for reviewer's feedback).
    """
    try:
        result = await db.execute(
            select(PeerSession)
            .where(PeerSession.reviewer_id == current_user.user_id)
            .where(PeerSession.status == "PENDING_REVIEW")
            .order_by(PeerSession.created_at.desc())
        )
        peer_sessions = result.scalars().all()

        inbox_items = []
        for session in peer_sessions:
            # Get question preview
            question_result = await db.execute(
                select(Question).where(Question.question_id == session.question_id)
            )
            question = question_result.scalar_one_or_none()
            question_preview = question.content[:50] + "..." if question else "Unknown question"

            item = PeerSessionInboxItem(
                session_id=session.session_id,
                question_preview=question_preview,
                status=session.status,
                created_at=session.created_at
            )
            inbox_items.append(item)

        return jsend_success(
            code=HTTP_200_OK,
            message="Inbox retrieved successfully",
            data=inbox_items
        )

    except Exception as e:
        system_logger.error(
            f"Error retrieving inbox: {str(e)}",
            extra={"event_type": "INBOX_RETRIEVE_ERROR", "user_id": str(current_user.user_id)}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving inbox"
        )


@router.get(
    "/inbox/{session_id}",
    response_model=JSendResponse[PeerSessionDetail],
    status_code=status.HTTP_200_OK,
    summary="Get review task details",
    description="Get details of a specific peer review task. Requester is anonymous."
)
async def get_review_task(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get details of a peer session where current user is the reviewer.
    Returns question info and requester's query (requester identity is hidden).
    """
    try:
        result = await db.execute(
            select(PeerSession)
            .where(PeerSession.session_id == session_id)
            .where(PeerSession.reviewer_id == current_user.user_id)
        )
        peer_session = result.scalar_one_or_none()

        if not peer_session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Peer session not found or you are not the reviewer"
            )

        # Get question details
        question_result = await db.execute(
            select(Question).where(Question.question_id == peer_session.question_id)
        )
        question = question_result.scalar_one_or_none()

        if not question:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Question not found"
            )

        detail = PeerSessionDetail(
            session_id=peer_session.session_id,
            question=QuestionInfo(
                content=question.content,
                topic_tags=question.topic_tags if hasattr(question, 'topic_tags') and question.topic_tags else []
            ),
            requester_query=peer_session.requester_query if hasattr(peer_session, 'requester_query') else "",
            status=peer_session.status,
            expires_at=None  # Can add expiration logic later
        )

        return jsend_success(
            code=HTTP_200_OK,
            message="Review task details retrieved successfully",
            data=detail
        )

    except Exception as e:
        system_logger.error(
            f"Error retrieving review task: {str(e)}",
            extra={"event_type": "REVIEW_TASK_RETRIEVE_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving review task"
        )


@router.post(
    "/inbox/{session_id}/submit",
    response_model=JSendResponse[ReviewSubmitResult],
    status_code=status.HTTP_200_OK,
    summary="Submit review feedback",
    description="Submit constructive feedback for a peer review session. Calculates system_score using NLP."
)
async def submit_review(
    session_id: str,
    submit_data: ReviewSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Submit review feedback as the reviewer.
    - Validates reviewer owns the session
    - Calculates system_score using NLP keyword matching
    - Updates review_content and system_score
    - Changes status to WAITING_CONFIRMATION
    """
    try:
        result = await db.execute(
            select(PeerSession)
            .where(PeerSession.session_id == session_id)
            .where(PeerSession.reviewer_id == current_user.user_id)
        )
        peer_session = result.scalar_one_or_none()

        if not peer_session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Peer session not found or you are not the reviewer"
            )

        if peer_session.status != "PENDING_REVIEW":
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message=f"Cannot submit review. Current status: {peer_session.status}"
            )

        # Calculate system_score using NLP
        system_score = calculate_system_score(submit_data.review_content)

        # Update peer session
        peer_session.review_content = submit_data.review_content
        peer_session.system_score = system_score
        peer_session.status = "WAITING_CONFIRMATION"

        await db.commit()

        # Log assessment event
        assessment_logger.info(
            f"Peer review submitted: session={session_id}, reviewer={current_user.user_id}, "
            f"system_score={system_score:.2f}",
            extra={
                "event_type": "PEER_REVIEW_SUBMITTED",
                "peer_session_id": session_id,
                "reviewer_id": str(current_user.user_id),
                "system_score": system_score
            }
        )

        result_data = ReviewSubmitResult(
            session_id=peer_session.session_id,
            system_score=system_score,
            status=peer_session.status
        )

        return jsend_success(
            code=HTTP_200_OK,
            message="Review submitted successfully",
            data=result_data
        )

    except Exception as e:
        system_logger.error(
            f"Error submitting review: {str(e)}",
            extra={"event_type": "PEER_REVIEW_SUBMIT_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error submitting review"
        )


@router.get(
    "/requests",
    response_model=JSendResponse[List[PeerSessionRequest]],
    status_code=status.HTTP_200_OK,
    summary="Get requester's peer review requests",
    description="List all peer sessions where current user is the requester"
)
async def get_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get list of peer sessions where current user is the requester.
    Shows all statuses including PENDING_REVIEW, WAITING_CONFIRMATION, COMPLETED.
    """
    try:
        result = await db.execute(
            select(PeerSession)
            .where(PeerSession.requester_id == current_user.user_id)
            .order_by(PeerSession.created_at.desc())
        )
        peer_sessions = result.scalars().all()

        request_items = []
        for session in peer_sessions:
            # Get question preview
            question_result = await db.execute(
                select(Question).where(Question.question_id == session.question_id)
            )
            question = question_result.scalar_one_or_none()
            question_preview = question.content[:50] + "..." if question else "Unknown question"

            item = PeerSessionRequest(
                session_id=session.session_id,
                question_preview=question_preview,
                status=session.status,
                created_at=session.created_at,
                review_content=session.review_content if session.status != "PENDING_REVIEW" else None
            )
            request_items.append(item)

        return jsend_success(
            code=HTTP_200_OK,
            message="Requests retrieved successfully",
            data=request_items
        )

    except Exception as e:
        system_logger.error(
            f"Error retrieving requests: {str(e)}",
            extra={"event_type": "REQUESTS_RETRIEVE_ERROR", "user_id": str(current_user.user_id)}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving requests"
        )


@router.post(
    "/requests/{session_id}/rate",
    response_model=JSendResponse[RateResult],
    status_code=status.HTTP_200_OK,
    summary="Rate peer feedback",
    description="Rate the helpfulness of received peer feedback. Triggers Social Elo update."
)
async def rate_feedback(
    session_id: str,
    rate_data: RateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Rate peer feedback as the requester (thumbs up/down).
    - Validates requester owns the session
    - Updates is_helpful
    - Calculates final_score = 0.5*system_score + 0.5*(1 if helpful else 0)
    - Triggers Social Elo update for reviewer
    - Changes status to COMPLETED
    """
    try:
        result = await db.execute(
            select(PeerSession)
            .where(PeerSession.session_id == session_id)
            .where(PeerSession.requester_id == current_user.user_id)
        )
        peer_session = result.scalar_one_or_none()

        if not peer_session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Peer session not found or you are not the requester"
            )

        if peer_session.status != "WAITING_CONFIRMATION":
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message=f"Cannot rate feedback. Current status: {peer_session.status}"
            )

        # Update is_helpful
        peer_session.is_helpful = rate_data.is_helpful

        # Calculate final_score
        final_score = peer_session.calculate_final_score()
        peer_session.final_score = final_score

        # Get reviewer for Social Elo update
        reviewer_result = await db.execute(
            select(User).where(User.user_id == peer_session.reviewer_id)
        )
        reviewer = reviewer_result.scalar_one_or_none()

        if not reviewer:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Reviewer not found"
            )

        # Update Social Elo
        theta_before, theta_after = update_theta_social(reviewer, peer_session)

        # Update requester status back to ACTIVE
        current_user.status = "ACTIVE"

        await db.commit()

        # Log assessment event
        assessment_logger.info(
            f"Peer feedback rated: session={session_id}, requester={current_user.user_id}, "
            f"is_helpful={rate_data.is_helpful}, final_score={final_score:.2f}, "
            f"reviewer_theta={theta_before:.1f}->{theta_after:.1f}",
            extra={
                "event_type": "PEER_RATED",
                "peer_session_id": session_id,
                "requester_id": str(current_user.user_id),
                "reviewer_id": str(reviewer.user_id),
                "is_helpful": rate_data.is_helpful,
                "final_score": final_score,
                "theta_social_before": theta_before,
                "theta_social_after": theta_after
            }
        )

        result_data = RateResult(
            final_score=final_score,
            reviewer_theta_social_before=theta_before,
            reviewer_theta_social_after=theta_after
        )

        return jsend_success(
            code=HTTP_200_OK,
            message="Feedback rated successfully",
            data=result_data
        )

    except Exception as e:
        system_logger.error(
            f"Error rating feedback: {str(e)}",
            extra={"event_type": "PEER_RATE_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error rating feedback"
        )
