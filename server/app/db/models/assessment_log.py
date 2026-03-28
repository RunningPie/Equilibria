"""
Assessment Log Model.
Sesuai Technical Specifications v2 Section 3.1 Table assessment_logs.
"""
from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base


class AssessmentLog(Base):
    """
    Model untuk tabel assessment_logs.
    Menyimpan riwayat setiap attempt siswa untuk analisis stagnasi & learning gain.
    Logging komprehensif sesuai Specs Section 6.6.
    """
    __tablename__ = "assessment_logs"

    # Primary Key - Auto-increment Serial
    log_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    # Session Grouping Identifier
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # Foreign Key to Users
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign Key to Questions
    question_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("questions.question_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Submitted SQL Query
    user_query: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Nomor Attempt (1, 2, atau 3 untuk multi-attempt per soal)
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Flag Attempt Final (TRUE saat user klik Next atau mencapai attempt 3)
    is_final_attempt: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    # Theta Sebelum Pembaruan (hanya diisi jika is_final_attempt = TRUE)
    theta_before: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    # Theta Setelah Pembaruan (hanya diisi jika is_final_attempt = TRUE)
    theta_after: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    # Difficulty Sebelum Pembaruan (hanya diisi jika is_final_attempt = TRUE)
    difficulty_before: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    # Difficulty Setelah Pembaruan (hanya diisi jika is_final_attempt = TRUE)
    difficulty_after: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    # Waktu Eksekusi dalam Milidetik (total waktu dari attempt pertama hingga final submit)
    execution_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    # Stagnation Detection Flag - TRUE jika stagnation terdeteksi pada attempt ini
    # Hanya relevan jika is_final_attempt = TRUE
    stagnation_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Sandbox Execution Result
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    # Attempt Timestamp
    timestamp: Mapped[DateTime] = mapped_column(
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
