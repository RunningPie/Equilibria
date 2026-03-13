"""
Assessment Log & Peer Session Models.
Sesuai Technical Specifications v2 Section 3.1 Tables assessment_logs & peer_sessions.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey, Enum, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
import enum

class AssessmentSessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class AssessmentLog(Base):
    """
    Model untuk tabel assessment_logs.
    Menyimpan riwayat setiap attempt siswa untuk analisis stagnasi & learning gain.
    Logging komprehensif sesuai Specs Section 6.6.
    """
    __tablename__ = "assessment_logs"

    # Primary Key - Auto-increment Serial
    log_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    # Session Grouping Identifier
    session_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # Foreign Key to Users
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign Key to Questions
    question_id = Column(
        String(10),
        ForeignKey("questions.question_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Submitted SQL Query
    user_query = Column(
        Text,
        nullable=False
    )

    # Sandbox Execution Result
    is_correct = Column(
        Boolean,
        nullable=False
    )

    # Theta Before Update (for delta calculation)
    theta_before = Column(
        Float,
        nullable=False
    )

    # Theta After Update (for delta calculation)
    theta_after = Column(
        Float,
        nullable=False
    )

    # Execution Time in Milliseconds (excluding idle)
    execution_time_ms = Column(
        Integer,
        nullable=False,
        default=0
    )

    # Attempt Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="assessment_logs"
    )

    question = relationship(
        "Question",
        back_populates="assessment_logs"
    )

    def __repr__(self):
        return f"<AssessmentLog(log_id={self.log_id}, user_id={self.user_id}, correct={self.is_correct})>"

    @property
    def theta_delta(self) -> float:
        """Calculate theta change for stagnation detection."""
        return self.theta_after - self.theta_before

class PreTestSession(Base):
    __tablename__ = "pretest_sessions"
    
    # Primary Key - UUID for session identifier
    session_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    current_question_index = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    answers = Column(
        JSONB, # isinya: {question_id: is_correct}
        nullable=False,
        default=dict
    )
    
    total_questions = Column(
        Integer,
        nullable=False,
        default=5
    )
    
    current_theta = Column(
        Float,
        nullable=False,
        default=0.0
    )
    
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    

class PeerSession(Base):
    """
    Model untuk tabel peer_sessions.
    Menyimpan sesi peer review untuk mitigasi overpersonalization.
    Sesuai Specs Section 3.1 & 6.4 (Constraint-Based Re-ranking).
    """
    __tablename__ = "peer_sessions"

    # Primary Key - UUID for session identifier
    session_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign Key - User experiencing stagnation
    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign Key - Assigned heterogeneous peer
    reviewer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign Key - Question context for review
    question_id = Column(
        String(10),
        ForeignKey("questions.question_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Constructive Feedback Text (NOT NULL per Specs)
    review_content = Column(
        Text,
        nullable=False
    )

    # NLP Keyword Matching Score [0.0, 1.0]
    system_score = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # Requester's Binary Confirmation (Helpful/Not Helpful)
    is_helpful = Column(
        Boolean,
        nullable=True,  # NULLABLE per Specs (until confirmed)
        default=None
    )

    # Computed Final Score: (0.5 * system_score) + (0.5 * is_helpful)
    final_score = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # Session State: PENDING_REVIEW, WAITING_CONFIRMATION, COMPLETED
    status = Column(
        String(50),
        nullable=False,
        default="PENDING_REVIEW"
    )

    # Session Initiation Timestamp
    created_at = Column(
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
    
class AssessmentSession(Base):
    
    __tablename__ = "assessment_sessions"
    
    session_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid.uuid4
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user = relationship(
        "User",
        back_populates="assessment_sessions"
    )
    
    module_id = Column(
        String(5),
        ForeignKey("modules.module_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    ) 
    
    module = relationship(
        "Module",
        back_populates="assessment_sessions"
    )
    
    question_ids_served = Column(
        ARRAY(String(10)),
        server_default=text("'{}'"),
        nullable=False,
        index=True
    )
    
    status = Column(
        Enum(
            AssessmentSessionStatus,
            name="assessment_session_status",
            create_constraint=True,
        ),
        nullable=False,
        server_default=AssessmentSessionStatus.ACTIVE.value,
    )
    
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    ended_at = Column(
        DateTime(timezone=True),
        nullable=True
    )