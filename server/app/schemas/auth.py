"""
Authentication Schemas
Technical Specifications v2 - Section 7.1
"""
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class LoginRequest(BaseModel):
    """Login request schema."""
    nim: str = Field(..., min_length=1, max_length=20, description="Student ID")
    password: str = Field(..., min_length=6, description="Password")


class UserResponse(BaseModel):
    """
    User profile response schema.
    Technical Specifications v2 - Section 3.1, 7.2
    """
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)
    
    # Fields - use UUID type to match SQLAlchemy model
    user_id: UUID = Field(..., description="Unique user identifier")
    nim: str = Field(..., min_length=1, max_length=20)
    full_name: str = Field(..., min_length=1, max_length=100)
    current_theta: float = Field(..., ge=-3.0, le=3.0)
    theta_social: float = Field(..., ge=-3.0, le=3.0)
    k_factor: int = Field(..., gt=0)
    has_completed_pretest: bool
    created_at: datetime
    
    # Serializer untuk UUID → string (untuk JSON response)
    @field_serializer('user_id')
    def serialize_user_id(self, user_id: UUID, _info) -> str:
        """Convert UUID object to string for JSON serialization."""
        return str(user_id)


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenResponse(BaseModel):
    """Token-only response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    """User profile update schema."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=6)