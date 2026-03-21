'''
Junction table untuk lock status modul per user
'''
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class UserModuleProgress(Base):

    __tablename__ = "user_module_progress"
    
    # Composite PK
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )
    
    module_id: Mapped[str] = mapped_column(
        String(5),
        ForeignKey("modules.module_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )
    
    # Status apakah modul bisa diakses
    is_unlocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Status penyelesaian modul
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Akses pertama
    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Waktu penyelesaian
    completed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relasi
    user = relationship("User", back_populates="module_progress")
    module = relationship("Module", back_populates="user_progress")
    
    def __repr__(self):
        return f"<UserModuleProgress(user_id={self.user_id}, module_id={self.module_id})>"
    
    