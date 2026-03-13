"""
Module Model - Merepresentasikan tabel modules di skema public.
Sesuai Technical Specifications v2 Section 3.1 Table modules.
"""
from sqlalchemy import Column, String, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.models import user_module_progress


class Module(Base):
    """
    Model untuk tabel modules.
    Menyimpan materi pembelajaran hierarkis (CH01, CH02, CH03).
    Sesuai Specs Section 4 (Material Structure).
    """
    __tablename__ = "modules"

    # Primary Key - Module Code (e.g., 'CH01')
    module_id = Column(
        String(5),
        primary_key=True,
        nullable=False
    )

    # Display Name
    title = Column(
        String(255),
        nullable=False
    )

    # Module Overview/Description
    description = Column(
        Text,
        nullable=True
    )

    # Difficulty Range - Lower Bound (D_min)
    difficulty_min = Column(
        Float,
        nullable=False,
        default=-3.0
    )

    # Difficulty Range - Upper Bound (D_max)
    difficulty_max = Column(
        Float,
        nullable=False,
        default=3.0
    )

    # HTML Content for Learning Material
    content_html = Column(
        Text,
        nullable=True
    )
    
    # Relationships
    questions = relationship(
        "Question",
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