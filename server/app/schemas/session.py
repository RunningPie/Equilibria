"""
Schemas untuk Assessment Session API - Tech Specs v4.2
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SessionStartRequest(BaseModel):
    """Request untuk memulai assessment session baru"""
    module_id: str = Field(..., description="ID modul (CH01, CH02, dll)", examples=["CH01"])
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "module_id": "CH01"
            }
        }
    )


class SessionStartResult(BaseModel):
    """Response dari POST /session/start"""
    session_id: UUID = Field(..., description="ID session yang baru dibuat")
    module_id: str = Field(..., description="ID modul")
    user_theta: float = Field(..., description="Rating theta user saat memulai session")
    status: str = Field(..., description="Status session (ACTIVE)")
    started_at: datetime = Field(..., description="Waktu mulai session")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "module_id": "CH01",
                "user_theta": 1300.0,
                "status": "ACTIVE",
                "started_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class QuestionResponse(BaseModel):
    """Response dari GET /session/{id}/question"""
    session_id: UUID = Field(..., description="ID session")
    question_id: str = Field(..., description="ID soal")
    module_id: str = Field(..., description="ID modul")
    content: str = Field(..., description="Teks pertanyaan")
    current_difficulty: float = Field(..., description="Difficulty soal saat ini")
    attempt_count: int = Field(..., description="Jumlah attempt untuk soal ini")
    max_attempts: int = Field(..., description="Maksimal attempt (3)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "question_id": "CH01-001",
                "module_id": "CH01",
                "content": "Tampilkan semua mahasiswa dari jurusan IF",
                "current_difficulty": 1250.0,
                "attempt_count": 1,
                "max_attempts": 3
            }
        }
    )


class SessionStatus(BaseModel):
    """Response dari GET /session/{id}"""
    session_id: UUID = Field(..., description="ID session")
    module_id: str = Field(..., description="ID modul")
    status: str = Field(..., description="Status session (ACTIVE, COMPLETED)")
    user_theta_start: float = Field(..., description="Theta user saat mulai")
    user_theta_current: float = Field(..., description="Theta user saat ini")
    questions_served: int = Field(..., description="Jumlah soal yang sudah di-serve")
    questions_completed: int = Field(..., description="Jumlah soal yang sudah selesai")
    started_at: datetime = Field(..., description="Waktu mulai session")
    ended_at: Optional[datetime] = Field(None, description="Waktu selesai session")
    current_question_id: Optional[str] = Field(None, description="ID soal aktif saat ini")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "module_id": "CH01",
                "status": "ACTIVE",
                "user_theta_start": 1300.0,
                "user_theta_current": 1325.0,
                "questions_served": 5,
                "questions_completed": 3,
                "started_at": "2024-01-15T10:30:00Z",
                "ended_at": None,
                "current_question_id": "CH01-005"
            }
        }
    )


class SubmitRequest(BaseModel):
    """Request untuk POST /session/{id}/submit"""
    question_id: str = Field(..., description="ID soal yang dijawab")
    user_query: str = Field(..., description="Query SQL yang disubmit user")
    execution_time_ms: int = Field(..., description="Waktu eksekusi dalam milidetik")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "CH01-001",
                "user_query": "SELECT * FROM mahasiswa WHERE jurusan = 'IF'",
                "execution_time_ms": 1500
            }
        }
    )


class SubmitResult(BaseModel):
    """Response dari POST /session/{id}/submit"""
    is_correct: bool = Field(..., description="Apakah jawaban benar")
    is_final_attempt: bool = Field(..., description="Apakah ini attempt terakhir")
    attempt_number: int = Field(..., description="Nomor attempt (1, 2, atau 3)")
    feedback: str = Field(..., description="Feedback untuk user")
    theta_before: Optional[float] = Field(None, description="Theta sebelum update (hanya jika final)")
    theta_after: Optional[float] = Field(None, description="Theta setelah update (hanya jika final)")
    next_question_available: bool = Field(..., description="Apakah masih ada soal berikutnya")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_correct": True,
                "is_final_attempt": True,
                "attempt_number": 1,
                "feedback": "Jawaban benar! Query Anda berhasil menampilkan data yang diminta.",
                "theta_before": 1300.0,
                "theta_after": 1325.0,
                "next_question_available": True
            }
        }
    )


class NextResult(BaseModel):
    """Response dari POST /session/{id}/next"""
    session_id: UUID = Field(..., description="ID session")
    question_id: str = Field(..., description="ID soal berikutnya")
    module_id: str = Field(..., description="ID modul")
    content: str = Field(..., description="Teks pertanyaan berikutnya")
    current_difficulty: float = Field(..., description="Difficulty soal saat ini")
    attempt_count: int = Field(..., description="Jumlah attempt untuk soal ini (dimulai dari 1)")
    max_attempts: int = Field(..., description="Maksimal attempt (3)")
    theta_before: Optional[float] = Field(None, description="Theta sebelum update dari soal yang baru saja diselesaikan")
    theta_after: Optional[float] = Field(None, description="Theta setelah update dari soal yang baru saja diselesaikan")
    previous_question_id: Optional[str] = Field(None, description="ID soal yang baru saja diselesaikan")
    theta_change: Optional[float] = Field(None, description="Perubahan theta (theta_after - theta_before)")
    stagnation_detected: bool = Field(False, description="Apakah stagnation terdeteksi (variance < 165)")
    peer_session_created: bool = Field(False, description="Apakah peer session berhasil dibuat (hanya jika stagnation terdeteksi)")
    questions_served: int = Field(..., description="Jumlah soal yang sudah di-serve dalam session ini")
    total_questions_available: int = Field(..., description="Total jumlah soal tersedia di modul ini")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "question_id": "CH01-002",
                "module_id": "CH01",
                "content": "Tampilkan mahasiswa dengan IPK tertinggi",
                "current_difficulty": 1350.0,
                "attempt_count": 1,
                "max_attempts": 3,
                "theta_before": 1300.0,
                "theta_after": 1325.0,
                "previous_question_id": "CH01-001",
                "theta_change": 25.0,
                "stagnation_detected": False,
                "questions_served": 2,
                "total_questions_available": 20
            }
        }
    )
