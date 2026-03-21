"""
Assessment Session Model.
Sesuai Technical Specifications v2 Section 3.1 Table assessment_sessions.
"""
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from app.db.base import Base
import uuid
import enum


class AssessmentSessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class AssessmentSession(Base):
    """
    Model untuk tabel assessment_sessions.
    Menyimpan sesi assessment untuk setiap user per module.
    """
    
    __tablename__ = "assessment_sessions"
    
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid.uuid4
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user = relationship(
        "User",
        back_populates="assessment_sessions"
    )
    
    module_id: Mapped[str] = mapped_column(
        String(5),
        ForeignKey("modules.module_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    ) 
    
    module = relationship(
        "Module",
        back_populates="assessment_sessions"
    )
    
    current_question_id: Mapped[str] = mapped_column(
        String(10),
        nullable=True
    )
    
    current_question_attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    question_ids_served: Mapped[list] = mapped_column(
        ARRAY(String(10)),
        server_default=text("'{}'"),
        nullable=False,
        index=True
    )
    
    status: Mapped[AssessmentSessionStatus] = mapped_column(
        Enum(
            AssessmentSessionStatus,
            name="assessment_session_status",
            create_constraint=True,
        ),
        nullable=False,
        server_default=AssessmentSessionStatus.ACTIVE.value,
    )
    
    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    ended_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
