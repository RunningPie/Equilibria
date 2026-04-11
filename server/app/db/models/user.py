"""
User Model - Merepresentasikan tabel users di skema public.
Sesuai Technical Specifications v2 Section 3.1 Table users.
"""
# Updated imports for SQLAlchemy 2.0+ typing
from sqlalchemy import String, Float, Integer, Boolean, DateTime, CheckConstraint
from typing import Optional as TypingOptional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class User(Base):
    """
    Model untuk tabel users.
    Menyimpan informasi profil siswa, Elo rating (individual & social),
    dan status pembelajaran.
    """
    # Standard SQLAlchemy convention is __tablename__
    __tablename__ = "users"

    # Primary Key - UUID untuk keamanan dan skalabilitas
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Student ID - Unique identifier dari institusi
    nim: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True  # Index untuk performa login/search
    )

    # Display Name
    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Hashed Password - Argon2id (sesuai Specs Section 3.1)
    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # Elo Rating Individual - Skala [0, 2000] mulai dari 1300
    theta_individu: Mapped[float] = mapped_column(
        Float,
        default=1300.0,
        nullable=False
    )

    # Social Elo Rating - Skala [0, 2000] mulai dari 1300
    theta_social: Mapped[float] = mapped_column(
        Float,
        default=1300.0,
        nullable=False
    )

    # K-Factor untuk pembaruan Elo (Vesin piecewise: {30,20,15,10})
    k_factor: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False
    )

    # Total final attempts (untuk K-factor decay)
    total_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Status pengguna untuk trigger kolaborasi
    status: Mapped[str] = mapped_column(
        String(20),
        default='ACTIVE',
        nullable=False
    )

    # Group assignment untuk ablation study (A=with intervention, B=without)
    group_assignment: Mapped[str] = mapped_column(
        String(1),
        default='B',
        nullable=False
    )

    # Flag apakah user pernah mengalami stagnation terdeteksi
    stagnation_ever_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Mandatory Pre-Test Flag (Cold-Start Mitigation)
    has_completed_pretest: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Admin flag for administrative privileges
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Soft delete flag for account lifecycle
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Soft delete timestamp
    deleted_at: Mapped[TypingOptional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    # Account Creation Timestamp
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships (untuk lazy loading)
    # Note: Use string for back_populates to avoid circular import issues
    assessment_logs: Mapped[list["AssessmentLog"]] = relationship(
        "AssessmentLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    peer_sessions_requester: Mapped[list["PeerSession"]] = relationship(
        "PeerSession",
        foreign_keys="PeerSession.requester_id",
        back_populates="requester"
    )

    peer_sessions_reviewer: Mapped[list["PeerSession"]] = relationship(
        "PeerSession",
        foreign_keys="PeerSession.reviewer_id",
        back_populates="reviewer"
    )
    
    assessment_sessions: Mapped[list["AssessmentSession"]] = relationship(
        "AssessmentSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    module_progress: Mapped[list["UserModuleProgress"]] = relationship(
        "UserModuleProgress",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Batasan Tabel - Pastikan theta dalam rentang valid per Tech Specs v4.2
    __table_args__ = (
        CheckConstraint(
            'theta_individu >= 0 AND theta_individu <= 2000',
            name='check_theta_individu_range'
        ),
        CheckConstraint(
            'theta_social >= 0 AND theta_social <= 2000',
            name='check_theta_social_range'
        ),
        CheckConstraint(
            'k_factor > 0',
            name='check_k_factor_positive'
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'NEEDS_PEER_REVIEW')",
            name='check_status_valid'
        ),
        CheckConstraint(
            "group_assignment IN ('A', 'B')",
            name='check_group_assignment_valid'
        ),
    )

    def __repr__(self) -> str:
        return f"<User(nim='{self.nim}', theta_ind={self.theta_individu}, theta_soc={self.theta_social})>"

    @property
    def theta_display(self) -> float:
        """
        Menghitung theta_display dengan weighted average per Tech Specs v4.2.
        theta_display = (0.8 × θ_individu) + (0.2 × θ_social)
        """
        return (0.8 * self.theta_individu) + (0.2 * self.theta_social)