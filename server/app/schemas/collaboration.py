"""
Schema untuk API Collaboration - Tech Specs v4.2 Bagian 7.E

Endpoint kolaboratif untuk sistem peer review.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class QuestionInfo(BaseModel):
    """Informasi soal untuk konteks peer review"""
    content: str = Field(..., description="Question text")
    topic_tags: List[str] = Field(default=[], description="Topic tags for the question")


class PeerSessionInboxItem(BaseModel):
    """Item di inbox reviewer - review yang menunggu"""
    session_id: UUID = Field(..., description="Peer session ID")
    question_preview: str = Field(..., description="Question content preview")
    status: str = Field(..., description="Session status (PENDING_REVIEW)")
    created_at: datetime = Field(..., description="Session creation time")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "question_preview": "Tampilkan rata-rata IPK...",
                "status": "PENDING_REVIEW",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class PeerSessionDetail(BaseModel):
    """Detail view untuk reviewer - requester bersifat anonim"""
    session_id: UUID = Field(..., description="Peer session ID")
    question: QuestionInfo = Field(..., description="Question details")
    requester_query: str = Field(..., description="Requester's SQL query")
    status: str = Field(..., description="Session status")
    expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "question": {
                    "content": "Tampilkan rata-rata IPK dari mahasiswa IF",
                    "topic_tags": ["AVG", "GROUP BY"]
                },
                "requester_query": "SELECT AVG(ipk) FROM mahasiswa",
                "status": "PENDING_REVIEW",
                "expires_at": "2024-01-16T10:30:00Z"
            }
        }
    )


class ReviewSubmitRequest(BaseModel):
    """Request untuk submit feedback review"""
    review_content: str = Field(..., description="Reviewer's constructive feedback", min_length=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "review_content": "Query Anda salah karena kurang GROUP BY. Seharusnya: SELECT jurusan, AVG(ipk) FROM mahasiswa GROUP BY jurusan"
            }
        }
    )


class ReviewSubmitResult(BaseModel):
    """Hasil setelah submit review"""
    session_id: UUID = Field(..., description="Peer session ID")
    system_score: float = Field(..., description="NLP-calculated quality score [0.0, 1.0]")
    status: str = Field(..., description="Updated status (WAITING_CONFIRMATION)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "system_score": 0.75,
                "status": "WAITING_CONFIRMATION"
            }
        }
    )


class PeerSessionRequest(BaseModel):
    """Item di daftar request requester"""
    session_id: UUID = Field(..., description="Peer session ID")
    question_preview: str = Field(..., description="Question content preview")
    status: str = Field(..., description="Session status")
    created_at: datetime = Field(..., description="Session creation time")
    review_content: Optional[str] = Field(None, description="Review content if available")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "question_preview": "Tampilkan rata-rata IPK...",
                "status": "WAITING_CONFIRMATION",
                "created_at": "2024-01-15T10:30:00Z",
                "review_content": "Query Anda salah karena..."
            }
        }
    )


class RateRequest(BaseModel):
    """Request untuk memberi rating feedback peer"""
    is_helpful: bool = Field(..., description="Whether the feedback was helpful (thumbs up/down)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_helpful": True
            }
        }
    )


class RateResult(BaseModel):
    """Hasil setelah memberi rating feedback - termasuk update Social Elo"""
    final_score: float = Field(..., description="Combined score: 0.5*system_score + 0.5*is_helpful")
    reviewer_theta_social_before: float = Field(..., description="Reviewer's social rating before update")
    reviewer_theta_social_after: float = Field(..., description="Reviewer's social rating after update")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "final_score": 0.75,
                "reviewer_theta_social_before": 1300.0,
                "reviewer_theta_social_after": 1307.5
            }
        }
    )
