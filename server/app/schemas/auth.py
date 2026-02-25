from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

# === Schema Request ===

class UserRegister(BaseModel):
    nim: str = Field(..., min_length=8, max_length=10, example="1234567890")
    full_name: str = Field(..., max_length=100, example="John Doe")
    password: str = Field(..., min_length=8, example="strongpassword123")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nim": "1234567890",
                "full_name": "John Doe",
                "password": "strongpassword123"
            }
        }
    )

class UserLogin(BaseModel):
    nim: str = Field(..., min_length=8, max_length=10, example="1234567890")
    password: str = Field(..., min_length=8, example="strongpassword123")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nim": "1234567890",
                "password": "strongpassword123"
            }
        }
    )

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100, example="John Doe Updated")
    old_password: Optional[str] = Field(None, min_length=8, example="newstrongpassword123")
    new_password: Optional[str] = Field(None, min_length=8, example="newstrongpassword123")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe Updated",
                "old_password": "oldpassword123",
                "new_password": "newstrongpassword123"
            }
        }
    )

# === Schema Response ===
class UserResponse(BaseModel):
    '''
    Dipake buat response yang mengembalikan informasi user, misalnya setelah login atau update profile
    '''
    user_id: UUID
    nim: str
    full_name: str
    current_theta: float
    theta_social: float
    k_factor: int
    has_completed_pretest: bool
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True, # supaya bisa baca dari SQLAlchemy model
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "nim": "1234567890",
                "full_name": "John Doe",
                "current_theta": 0.0,
                "theta_social": 0.0,
                "k_factor": 32,
                "has_completed_pretest": False,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    )

class LoginResponse(BaseModel):
    '''
    Dipake buat response setelah login atau register berhasil, mengembalikan access token dan informasi user
    '''
    access_token: str
    token_type: str = "bearer"
    user: UserResponse # ini ambil dari model atas
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "bearer",
                "user": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "nim": "1234567890",
                    "full_name": "John Doe Updated",
                    "current_theta": 0.0,
                    "theta_social": 0.0,
                    "k_factor": 32,
                    "has_completed_pretest": False,
                    "created_at": "2024-01-01T12:00:00Z"
                }
            }
        }
    )

class LogoutResponse(BaseModel):
    message: str = Field(..., example="Successfully logged out")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Successfully logged out"
            }
        }
    )