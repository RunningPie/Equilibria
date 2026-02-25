"""
Authentication Schemas
Technical Specifications v2 - Section 7.1
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request schema."""
    nim: str = Field(..., min_length=1, max_length=20, description="Student ID")
    password: str = Field(..., min_length=6, description="Password")


class UserResponse(BaseModel):
    """User profile response schema."""
    user_id: str
    nim: str
    full_name: str
    current_theta: float
    theta_social: float
    k_factor: int
    has_completed_pretest: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


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