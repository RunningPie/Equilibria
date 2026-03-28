"""
Peer Matching Module - Tech Specs v4.2 Section 6.4

Implements constraint-based re-ranking for heterogeneous peer matching
to break filter bubbles during stagnation.
"""
import numpy
import random
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func as sql_func

from app.db.models import User, PeerSession
from app.core.logging_config import get_loggers

system_logger, assessment_logger = get_loggers()

# Cohen's d threshold for meaningful heterogeneity (medium effect size)
COHEN_D_THRESHOLD = 0.5

# Fallback population std if all users have same theta (edge case)
FALLBACK_POPULATION_STD = 100.0


async def calculate_population_std(db: AsyncSession) -> float:
    """
    Calculate population standard deviation of theta_individu
    across all ACTIVE users.
    
    Args:
        db: Async database session
        
    Returns:
        Population standard deviation of theta_individu
    """
    result = await db.execute(
        select(User.theta_individu).where(User.status == "ACTIVE")
    )
    thetas = [row[0] for row in result.all()]
    
    if len(thetas) < 2:
        return FALLBACK_POPULATION_STD
    
    population_std = numpy.std(thetas, ddof=0)  # Population std (ddof=0)
    
    if population_std == 0:
        return FALLBACK_POPULATION_STD
    
    return float(population_std)


async def find_heterogeneous_peer(
    requester: User,
    db: AsyncSession
) -> Optional[User]:
    """
    Find a heterogeneous peer for collaborative review.
    
    Algorithm (Section 6.4):
    1. Calculate population std of theta_individu across ACTIVE users
    2. Compute min_difference = 0.5 * population_std (Cohen's d = 0.5)
    3. Filter users where |theta_peer - theta_requester| >= min_difference
    4. Exclude users with status 'NEEDS_PEER_REVIEW'
    5. Order by theta difference descending, take top 5, random select
    
    Args:
        requester: User experiencing stagnation
        db: Async database session
        
    Returns:
        Selected peer User or None if no suitable peer found
    """
    # Step 1: Calculate population standard deviation
    population_std = await calculate_population_std(db)
    
    # Step 2: Compute minimum difference (Cohen's d = 0.5)
    min_difference = COHEN_D_THRESHOLD * population_std
    
    system_logger.info(
        f"Peer matching: population_std={population_std:.2f}, min_diff={min_difference:.2f}, "
        f"requester_theta={requester.theta_individu:.2f}",
        extra={
            "event_type": "PEER_MATCH_INIT",
            "requester_id": str(requester.user_id),
            "population_std": population_std,
            "min_difference": min_difference
        }
    )
    
    # Step 3 & 4: Find candidates with sufficient theta difference
    # Exclude: requester themselves, users needing peer review
    result = await db.execute(
        select(User).where(
            User.user_id != requester.user_id,
            User.status != "NEEDS_PEER_REVIEW",
            sql_func.abs(User.theta_individu - requester.theta_individu) >= min_difference
        ).order_by(
            User.theta_individu.desc(),
            sql_func.abs(User.theta_individu - requester.theta_individu).desc()
        ).limit(5)
    )
    
    candidates = result.scalars().all()
    
    if not candidates:
        system_logger.warning(
            f"No heterogeneous peer found for user {requester.user_id}",
            extra={
                "event_type": "PEER_MATCH_FAIL",
                "requester_id": str(requester.user_id),
                "requester_theta": requester.theta_individu,
                "min_difference": min_difference
            }
        )
        return None
    
    # Step 5: Random selection from top 5 candidates
    import random
    selected_peer = random.choice(list(candidates))
    
    theta_diff = abs(selected_peer.theta_individu - requester.theta_individu)
    cohen_d = theta_diff / population_std
    
    system_logger.info(
        f"Peer match success: requester={requester.user_id}, "
        f"reviewer={selected_peer.user_id}, theta_diff={theta_diff:.2f}, cohen_d={cohen_d:.2f}",
        extra={
            "event_type": "PEER_MATCH_SUCCESS",
            "requester_id": str(requester.user_id),
            "reviewer_id": str(selected_peer.user_id),
            "theta_diff": theta_diff,
            "cohen_d": cohen_d
        }
    )
    
    return selected_peer


async def create_peer_session(
    requester: User,
    reviewer: User,
    question_id: str,
    requester_query: str,
    db: AsyncSession
) -> PeerSession:
    """
    Create a peer session record linking requester and reviewer.
    
    Args:
        requester: User experiencing stagnation
        reviewer: Assigned heterogeneous peer
        question_id: Question ID context for review
        requester_query: The requester's SQL query for review
        db: Async database session
        
    Returns:
        Created PeerSession record
    """
    peer_session = PeerSession(
        requester_id=requester.user_id,
        reviewer_id=reviewer.user_id,
        question_id=question_id,
        requester_query=requester_query,
        review_content="",  # To be filled by reviewer
        system_score=0.0,    # To be calculated when review submitted
        is_helpful=None,   # To be set by requester
        final_score=0.0,   # To be calculated after rating
        status="PENDING_REVIEW"
    )
    
    db.add(peer_session)
    
    # Update user statuses
    requester.status = "NEEDS_PEER_REVIEW"
    # Note: Reviewer status remains ACTIVE (they can still use the system)
    
    await db.flush()  # Get the session_id
    
    system_logger.info(
        f"Peer session created: session_id={peer_session.session_id}, "
        f"requester={requester.user_id}, reviewer={reviewer.user_id}",
        extra={
            "event_type": "PEER_SESSION_CREATED",
            "peer_session_id": str(peer_session.session_id),
            "requester_id": str(requester.user_id),
            "reviewer_id": str(reviewer.user_id),
            "question_id": question_id
        }
    )
    
    return peer_session
