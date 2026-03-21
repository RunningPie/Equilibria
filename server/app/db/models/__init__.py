"""
Models Package Initialization.

PENTING: Semua model harus di-import di sini agar Alembic dapat mendeteksi
mereka saat menjalankan `alembic revision --autogenerate`.

Jika model tidak di-import di sini, Alembic tidak akan membuat migration
untuk tabel tersebut.
"""

# Import semua model untuk Alembic autogenerate
from app.db.models.user import User
from app.db.models.module import Module
from app.db.models.question import Question
from app.db.models.assessment_log import AssessmentLog
from app.db.models.peer_session import PeerSession
from app.db.models.pretest_session import PreTestSession
from app.db.models.assessment_session import AssessmentSession
from app.db.models.user_module_progress import UserModuleProgress

# Eksport semua model untuk import eksternal
__all__ = [
    "User",
    "Module",
    "Question",
    "AssessmentLog",
    "PeerSession",
    "PreTestSession",
    "AssessmentSession",
    "UserModuleProgress",
]