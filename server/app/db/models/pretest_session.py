"""
PreTest Session Model.
Sesuai Technical Specifications v2 Section 3.1 Table pretest_sessions.
"""
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class PreTestSession(Base):
    """
    Model untuk tabel pretest_sessions.
    Menyimpan sesi pretest untuk cold-start mitigation.
    """
    __tablename__ = "pretest_sessions"
    
    # Primary Key - UUID for session identifier
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    current_question_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    
    answers: Mapped[dict] = mapped_column(
        JSONB, # isinya: {question_id: is_correct}
        nullable=False,
        default=dict
    )
    
    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5
    )
    
    current_theta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )
    
    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    completed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
