"""
Admin Schema - Schemas for admin functionality
Includes user management and log access schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# === User Management Schemas ===

class AdminUserCreate(BaseModel):
    """Schema for creating a new user (admin only)"""
    nim: str = Field(..., min_length=8, max_length=10, example="1234567890")
    full_name: str = Field(..., max_length=100, example="John Doe")
    password: str = Field(..., min_length=8, example="strongpassword123")
    group_assignment: Optional[str] = Field("B", max_length=1, pattern="^[AB]$", example="B")
    is_admin: Optional[bool] = Field(False, example=False)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nim": "1234567890",
                "full_name": "John Doe",
                "password": "strongpassword123",
                "group_assignment": "B",
                "is_admin": False
            }
        }
    )


class AdminUserUpdate(BaseModel):
    """Schema for updating an existing user (admin only)"""
    full_name: Optional[str] = Field(None, max_length=100, example="John Doe Updated")
    password: Optional[str] = Field(None, min_length=8, example="newstrongpassword123")
    group_assignment: Optional[str] = Field(None, max_length=1, pattern="^[AB]$", example="A")
    status: Optional[str] = Field(None, max_length=20, example="ACTIVE")
    is_admin: Optional[bool] = Field(None, example=True)
    theta_individu: Optional[float] = Field(None, ge=0, le=2000, example=1400.0)
    theta_social: Optional[float] = Field(None, ge=0, le=2000, example=1350.0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe Updated",
                "password": "newstrongpassword123",
                "group_assignment": "A",
                "status": "ACTIVE",
                "is_admin": True,
                "theta_individu": 1400.0,
                "theta_social": 1350.0
            }
        }
    )


class AdminUserResponse(BaseModel):
    """Schema for admin user response with all fields"""
    user_id: UUID
    nim: str
    full_name: str
    theta_individu: float
    theta_social: float
    k_factor: int
    total_attempts: int
    status: str
    has_completed_pretest: bool
    group_assignment: str
    stagnation_ever_detected: bool
    is_admin: bool
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "nim": "1234567890",
                "full_name": "John Doe",
                "theta_individu": 1300.0,
                "theta_social": 1300.0,
                "k_factor": 30,
                "total_attempts": 0,
                "status": "ACTIVE",
                "has_completed_pretest": False,
                "group_assignment": "B",
                "stagnation_ever_detected": False,
                "is_admin": False,
                "is_deleted": False,
                "deleted_at": None,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    )


class UserListResponse(BaseModel):
    """Schema for list of users response"""
    users: List[AdminUserResponse]
    total: int
    page: int = Field(..., ge=1, example=1)
    page_size: int = Field(..., ge=1, le=100, example=20)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [],
                "total": 0,
                "page": 1,
                "page_size": 20
            }
        }
    )


# === Log Access Schemas ===

class LogQueryParams(BaseModel):
    """Query parameters for log filtering"""
    date: Optional[str] = Field(None, pattern=r"^\d{8}$", example="20260411", 
                                  description="Date in YYYYMMDD format")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "20260411"
            }
        }
    )


class LogEntry(BaseModel):
    """Schema for a single log entry"""
    timestamp: Optional[str] = Field(None, example="2026-04-11T10:57:00Z")
    level: Optional[str] = Field(None, example="INFO")
    message: str = Field(..., example="Log message content")
    extra: Optional[Dict[str, Any]] = Field(None, example={"event_type": "TEST"})
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-04-11T10:57:00Z",
                "level": "INFO",
                "message": "User logged in successfully",
                "extra": {"event_type": "AUTH_LOGIN_SUCCESS", "user_id": "123e4567-e89b-12d3-a456-426614174000"}
            }
        }
    )


class LogsResponse(BaseModel):
    """Schema for logs response"""
    date: Optional[str] = Field(None, example="20260411")
    files: List[str] = Field(default=[], example=["syslog_20260411_105700.json"])
    logs: List[LogEntry] = Field(default=[], description="List of log entries")
    total_entries: int = Field(default=0, ge=0, example=150)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "20260411",
                "files": ["syslog_20260411_105700.json"],
                "logs": [],
                "total_entries": 150
            }
        }
    )


class DeleteUserResponse(BaseModel):
    """Schema for soft delete user response"""
    message: str = Field(..., example="User soft deleted successfully")
    deleted_user_id: UUID
    is_deleted: bool = Field(..., example=True)
    deleted_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "User soft deleted successfully",
                "deleted_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_deleted": True,
                "deleted_at": "2026-04-11T12:00:00Z"
            }
        }
    )
