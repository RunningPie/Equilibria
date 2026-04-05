"""
Social Elo Update Module - Tech Specs v4.2 Section 6.5

Implementasi Social Elo rating update untuk reviewers berdasarkan feedback ratings.
theta_social mengukur kualitas reviewer dan diupdate setelah requester rate feedback.
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
    Update theta_social reviewer berdasarkan final_score dari feedback yang dirate.

    Algoritma (Section 6.5):
    - W_social = peer_session.final_score (0.0 - 1.0)
    - We_social = 0.5 (neutral baseline)
    - K_social = 30 (novice phase)
    - delta = K_social * (W_social - We_social)  # range: [-15, +15]
    - new_theta_social = CLAMP(reviewer.theta_social + delta, 0, 2000)

    Args:
        reviewer: Reviewer User yang theta_social-nya akan diupdate
        peer_session: Peer session yang sudah selesai dengan final_score yang sudah di-set

    Returns:
        Tuple of (theta_social_before, theta_social_after)
    """
    # Hitung final_score kalau belum di-set
    final_score = peer_session.calculate_final_score()

    # Parameter Elo update
    W_social = final_score  # Actual score dari rating
    We_social = EXPECTED_SCORE_SOCIAL  # Expected baseline
    K_social = K_SOCIAL

    # Hitung rating delta
    delta = K_social * (W_social - We_social)
    # delta range: [-15, +15] per interaksi

    # Simpan nilai sebelumnya untuk logging
    theta_social_before = reviewer.theta_social

    # Hitung rating baru dengan clamping
    new_theta_social = reviewer.theta_social + delta
    new_theta_social = max(RATING_MIN, min(RATING_MAX, new_theta_social))

    # Update reviewer
    reviewer.theta_social = new_theta_social

    # Update peer session untuk analysis logging
    peer_session.theta_social_before = theta_social_before
    peer_session.theta_social_after = new_theta_social
    peer_session.status = "COMPLETED"
    peer_session.completed_at = datetime.utcnow()

    return theta_social_before, new_theta_social
