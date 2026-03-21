"""
Module Model - Merepresentasikan tabel modules di skema public.
Sesuai Technical Specifications v2 Section 3.1 Table modules.
"""
from sqlalchemy import Column, String, Float, Boolean, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Module(Base):
    """
    Model untuk tabel modules.
    Menyimpan materi pembelajaran hierarkis (CH01, CH02, CH03).
    Sesuai Specs Section 4 (Material Structure).
    """
    __tablename__ = "modules"

    # Primary Key - Module Code (e.g., 'CH01')
    module_id: Mapped[str] = mapped_column(
        String(5),
        primary_key=True,
        nullable=False
    )

    # Display Name
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Module Overview/Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    # Difficulty Range - Lower Bound (D_min)
    difficulty_min: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=-3.0
    )

    # Difficulty Range - Upper Bound (D_max)
    difficulty_max: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=3.0
    )

    # Threshold Unlock - minimum theta_individu yang diperlukan untuk mengakses modul ini
    unlock_theta_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Indeks Urutan untuk urutan tampilan
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    # Konten HTML untuk Materi Pembelajaran
    content_html: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relasi
    questions = relationship(
        "Question",
        back_populates="module",
        cascade="all, delete-orphan"
    )
    
    assessment_sessions = relationship(
        "AssessmentSession",
        back_populates="module",
        cascade="all, delete-orphan"
    )
    
    user_progress = relationship(
        "UserModuleProgress",
        back_populates="module",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Module(module_id='{self.module_id}', title='{self.title}')>"

    def is_unlocked_for_user(self, user_id: UUID) -> bool:
        # CH01 selalu unlocked:
        if self.module_id == "CH01":
            return True
        
        return False

    @property
    def difficulty_range(self) -> tuple:
        """Returns difficulty range as tuple (min, max)."""
        return (self.difficulty_min, self.difficulty_max)