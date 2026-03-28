"""
Social Elo Update Module - Tech Specs v4.2 Section 6.5

Implements Social Elo rating update for reviewers based on feedback ratings.
theta_social measures reviewer quality and is updated after requester rates feedback.
"""

from datetime import datetime
from typing import Tuple

from app.db.models import User, PeerSession


# Social Elo Constants (Section 6.5)
K_SOCIAL = 30  # Same as K_individu novice phase
EXPECTED_SCORE_SOCIAL = 0.5  # Neutral baseline - "average" reviewer expected score
RATING_MIN = 0.0
RATING_MAX = 2000.0


def update_theta_social(
    reviewer: User,
    peer_session: PeerSession
) -> Tuple[float, float]:
    """
    Update reviewer's theta_social based on final_score from rated feedback.

    Algorithm (Section 6.5):
    - W_social = peer_session.final_score (0.0 - 1.0)
    - We_social = 0.5 (neutral baseline)
    - K_social = 30 (novice phase)
    - delta = K_social * (W_social - We_social)  # range: [-15, +15]
    - new_theta_social = CLAMP(reviewer.theta_social + delta, 0, 2000)

    Args:
        reviewer: The reviewer User whose theta_social will be updated
        peer_session: The completed peer session with final_score set

    Returns:
        Tuple of (theta_social_before, theta_social_after)
    """
    # Calculate final_score if not already set
    final_score = peer_session.calculate_final_score()

    # Elo update parameters
    W_social = final_score  # Actual score from rating
    We_social = EXPECTED_SCORE_SOCIAL  # Expected baseline
    K_social = K_SOCIAL

    # Calculate rating delta
    delta = K_social * (W_social - We_social)
    # delta range: [-15, +15] per interaction

    # Store previous value for logging
    theta_social_before = reviewer.theta_social

    # Calculate new rating with clamping
    new_theta_social = reviewer.theta_social + delta
    new_theta_social = max(RATING_MIN, min(RATING_MAX, new_theta_social))

    # Update reviewer
    reviewer.theta_social = new_theta_social

    # Update peer session for analysis logging
    peer_session.theta_social_before = theta_social_before
    peer_session.theta_social_after = new_theta_social
    peer_session.status = "COMPLETED"
    peer_session.completed_at = datetime.utcnow()

    return theta_social_before, new_theta_social
