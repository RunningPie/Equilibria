from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

# === Schema Response ===

class PreTestSessionResponse(BaseModel):
    session_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    current_question_index: int = Field(..., example=0)
    total_questions: int = Field(..., example=5)
    started_at: datetime = Field(..., example="2024-01-01T12:00:00Z")
    completed_at: Optional[datetime] = Field(None, example="2024-01-01T12:00:00Z")
    is_completed: bool = Field(default=False)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "current_question_index": 0,
                "total_questions": 5,
                "started_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:00:00Z",
                "is_completed": False
            }
        }
    )

class PreTestQuestion(BaseModel):
    question_id: str = Field(..., min_length=5, max_length=10, example="CH01-Q001")
    content: str = Field(..., min_length=5, example="What is the capital of France?")
    question_number: int = Field(..., example=1)
    total_questions: int = Field(..., example=5)
    topic_tags: list[str] = Field(..., example=["JOIN", "GROUP BY"])
    
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "CH01-Q001",
                "content": "What is the capital of France?",
                "question_number": 1,
                "total_questions": 5,
                "topic_tags": ["JOIN", "GROUP BY"],
            }
        }
    )
    
class PreTestResult(BaseModel):
    session_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    theta_initial: Optional[float] = Field(None, ge=500, le=1500)
    has_completed_pretest: bool = Field(..., example=False)
    total_correct: int = Field(..., example=0)
    total_questions: int = Field(default=5)
    redirect: Optional[str] = Field(None, example="dashboard")
    is_correct: bool = Field(..., example=True, description="Whether the submitted answer was correct")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "theta_initial": 0.0,
                "has_completed_pretest": False,
                "total_correct": 0,
                "total_questions": 5,
                "redirect": "dashboard",
                "is_correct": True
            }
        }
    )

# === Schema Request ===

class PreTestAnswerSubmit(BaseModel):
    question_id: str = Field(..., min_length=5, max_length=10, example="CH01-Q001")
    question_number: int = Field(..., example=1)
    user_query: str = Field(..., min_length=10, max_length=1000, example="SELECT * FROM users WHERE age > 18")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "CH01-Q001",
                "user_query": "SELECT * FROM users WHERE age > 18"
            }
        }
    )