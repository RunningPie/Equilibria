"""
Peer Session Model.
Sesuai Technical Specifications v2 Section 3.1 Table peer_sessions.
"""
from sqlalchemy import String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class PeerSession(Base):
    """
    Model untuk tabel peer_sessions.
    Menyimpan sesi peer review untuk mitigasi overpersonalization.
    Sesuai Specs Section 3.1 & 6.4 (Constraint-Based Re-ranking).
    """
    __tablename__ = "peer_sessions"

    # Primary Key - UUID for session identifier
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign Key - User experiencing stagnation
    requester_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign Key - Assigned heterogeneous peer
    reviewer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign Key - Question context for review
    question_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("questions.question_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Constructive Feedback Text (NOT NULL per Specs)
    review_content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # NLP Keyword Matching Score [0.0, 1.0]
    system_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Requester's Binary Confirmation (Helpful/Not Helpful)
    is_helpful: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,  # NULLABLE per Specs (until confirmed)
        default=None
    )

    # Computed Final Score: (0.5 * system_score) + (0.5 * is_helpful)
    final_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Session State: PENDING_REVIEW, WAITING_CONFIRMATION, COMPLETED
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING_REVIEW"
    )

    # Session Initiation Timestamp
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    requester = relationship(
        "User",
        foreign_keys=[requester_id],
        back_populates="peer_sessions_requester"
    )

    reviewer = relationship(
        "User",
        foreign_keys=[reviewer_id],
        back_populates="peer_sessions_reviewer"
    )

    question = relationship(
        "Question",
        back_populates="peer_sessions"
    )

    def __repr__(self):
        return f"<PeerSession(session_id={self.session_id}, status='{self.status}')>"

    def calculate_final_score(self) -> float:
        """
        Calculate final score dengan bobot 50-50.
        Sesuai Specs Section 6.6.
        """
        if self.is_helpful is None:
            return self.system_score  # Belum ada konfirmasi
        
        helpful_score = 1.0 if self.is_helpful else 0.0
        return (0.5 * self.system_score) + (0.5 * helpful_score)
