"""
Question Model - Merepresentasikan tabel questions di skema public.
Sesuai Technical Specifications v2 Section 3.1 Table questions.
"""
from sqlalchemy import Column, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base


class Question(Base):
    """
    Model untuk tabel questions.
    Menyimpan bank soal SQL dengan difficulty yang dinamis (Elo-based).
    """
    __tablename__ = "questions"

    # Primary Key - Question Code (e.g., 'CH01-Q005')
    question_id = Column(
        String(10),
        primary_key=True,
        nullable=False
    )

    # Foreign Key to Modules
    module_id = Column(
        String(5),
        ForeignKey("modules.module_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Question Narrative (HTML/Markdown)
    content = Column(
        Text,
        nullable=False
    )

    # Canonical Solution (for sandbox comparison)
    target_query = Column(
        Text,
        nullable=False
    )

    # Initial Difficulty - Manually calibrated post-pretest
    initial_difficulty = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # Dynamic Difficulty - Updated via Elo Engine
    current_difficulty = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # Topic Tags for categorization (e.g., ['JOIN', 'GROUP BY'])
    topic_tags = Column(
        ARRAY(String),
        nullable=True,
        default=[]
    )

    # Availability Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # Relationships
    module = relationship(
        "Module",
        back_populates="questions"
    )

    assessment_logs = relationship(
        "AssessmentLog",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    peer_sessions = relationship(
        "PeerSession",
        back_populates="question"
    )

    def __repr__(self):
        return f"<Question(question_id='{self.question_id}', D={self.current_difficulty})>"