"""
User Model - Merepresentasikan tabel users di skema public.
Sesuai Technical Specifications v2 Section 3.1 Table users.
"""
# Updated imports for SQLAlchemy 2.0+ typing
from sqlalchemy import String, Float, Integer, Boolean, DateTime, CheckConstraint
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

    # Elo Rating Individual - Normalized [-3.0, +3.0]
    # Mapped[float] tells the type checker this is a float on instances
    current_theta: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    # Social Contribution Score
    theta_social: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    # K-Factor untuk Elo update (decay piecewise)
    k_factor: Mapped[int] = mapped_column(
        Integer,
        default=32,
        nullable=False
    )

    # Mandatory Pre-Test Flag (Cold-Start Mitigation)
    has_completed_pretest: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
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

    # Table Constraints - Ensure theta dalam range valid
    __table_args__ = (
        CheckConstraint(
            'current_theta >= -3.0 AND current_theta <= 3.0',
            name='check_current_theta_range'
        ),
        CheckConstraint(
            'k_factor > 0',
            name='check_k_factor_positive'
        ),
    )

    def __repr__(self) -> str:
        return f"<User(nim='{self.nim}', theta={self.current_theta})>"

    @property
    def theta_final(self) -> float:
        """
        Menghitung final theta dengan bobot 50-50 (individual + social).
        Sesuai Specs Section 6.6.
        
        With Mapped[float], the type checker now knows these are floats
        on instances, so no type error occurs here.
        """
        return (0.5 * self.current_theta) + (0.5 * self.theta_social)