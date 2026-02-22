"""
Authentication API Router
Technical Specifications v2 - Section 7.1, 7.2

All endpoints follow JSend response convention.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from datetime import timedelta
from typing import Optional

from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import (
    get_current_user,
    create_access_token,
    create_refresh_token
)
from app.core.config import settings
from app.core.logging_config import get_loggers
from app.schemas.auth import (
    LoginRequest,
    LoginResponse as AuthLoginResponse,
    UserResponse,
    UserUpdate,
    TokenResponse
)
from app.schemas.jsend import (
    JSendResponse,
    success_response,
    fail_response,
    error_response
)

system_logger, _ = get_loggers()

# Password hashing context (Argon2id sesuai Specs Section 3.1)
pwd_context = CryptContext(schemes=["argon2"], argon2__type="id")

router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return pwd_context.hash(password)


@router.post(
    "/login",
    response_model=JSendResponse[AuthLoginResponse],
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with NIM and password. Returns JWT token."
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> JSendResponse[AuthLoginResponse]:
    """
    Login endpoint with NIM and password.
    Technical Specifications v2 - Section 7.1
    
    **Request:**
    - nim: Student ID (VARCHAR 20)
    - password: Plain text password
    
    **Response (JSend):**
    - status: "success" | "fail" | "error"
    - code: HTTP status code
    - data: {access_token, refresh_token, token_type, user}
    - message: Error message if any
    """
    system_logger.info(
        f"Login attempt for NIM: {request.nim}",
        extra={"event_type": "AUTH_LOGIN_ATTEMPT"}
    )
    
    try:
        # Get user from database
        result = await db.execute(
            select(User).where(User.nim == request.nim)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            system_logger.warning(
                f"Login failed - User not found: {request.nim}",
                extra={"event_type": "AUTH_LOGIN_FAILED_USER_NOT_FOUND"}
            )
            return fail_response(
                message="Invalid NIM or password",
                code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            system_logger.warning(
                f"Login failed - Invalid password for NIM: {request.nim}",
                extra={"event_type": "AUTH_LOGIN_FAILED_INVALID_PASSWORD"}
            )
            return fail_response(
                message="Invalid NIM or password",
                code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.user_id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.user_id)}
        )
        
        system_logger.info(
            f"Login successful for user: {user.nim}",
            extra={
                "event_type": "AUTH_LOGIN_SUCCESS",
                "user_id": str(user.user_id)
            }
        )
        
        response_data = AuthLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
        
        return success_response(
            data=response_data,
            message="Login successful"
        )
        
    except Exception as e:
        system_logger.error(
            f"Login error: {str(e)}",
            extra={"event_type": "AUTH_LOGIN_ERROR"}
        )
        return error_response(
            message="Internal server error during login",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/logout",
    response_model=JSendResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Invalidate current session token."
)
async def logout(
    current_user: User = Depends(get_current_user)
) -> JSendResponse:
    """
    Logout endpoint.
    Technical Specifications v2 - Section 7.1
    
    Note: JWT tokens are stateless, so logout is client-side
    (delete token from storage). This endpoint logs the event.
    """
    try:
        system_logger.info(
            f"Logout for user: {current_user.nim}",
            extra={
                "event_type": "AUTH_LOGOUT",
                "user_id": str(current_user.user_id)
            }
        )
        
        return success_response(
            data=None,
            message="Logout successful"
        )
        
    except Exception as e:
        system_logger.error(
            f"Logout error: {str(e)}",
            extra={"event_type": "AUTH_LOGOUT_ERROR"}
        )
        return error_response(
            message="Internal server error during logout",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/me",
    response_model=JSendResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get authenticated user profile."
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> JSendResponse[UserResponse]:
    """
    Get current user profile.
    Technical Specifications v2 - Section 7.2
    
    Requires valid JWT token in Authorization header.
    """
    try:
        system_logger.info(
            f"Profile accessed by user: {current_user.nim}",
            extra={
                "event_type": "AUTH_PROFILE_ACCESS",
                "user_id": str(current_user.user_id)
            }
        )
        
        return success_response(
            data=UserResponse.model_validate(current_user),
            message="Profile retrieved successfully"
        )
        
    except Exception as e:
        system_logger.error(
            f"Get profile error: {str(e)}",
            extra={"event_type": "AUTH_PROFILE_ERROR"}
        )
        return error_response(
            message="Internal server error retrieving profile",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put(
    "/me",
    response_model=JSendResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
    description="Update authenticated user profile information."
)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSendResponse[UserResponse]:
    """
    Update user profile.
    Technical Specifications v2 - Section 7.2
    
    **Updatable fields:**
    - full_name
    - password (will be hashed)
    """
    try:
        system_logger.info(
            f"Profile update for user: {current_user.nim}",
            extra={
                "event_type": "AUTH_PROFILE_UPDATE",
                "user_id": str(current_user.user_id)
            }
        )
        
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        await db.commit()
        await db.refresh(current_user)
        
        return success_response(
            data=UserResponse.model_validate(current_user),
            message="Profile updated successfully"
        )
        
    except Exception as e:
        await db.rollback()
        system_logger.error(
            f"Update profile error: {str(e)}",
            extra={"event_type": "AUTH_PROFILE_UPDATE_ERROR"}
        )
        return error_response(
            message="Internal server error updating profile",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/register",
    response_model=JSendResponse[AuthLoginResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Register a new student account."
)
async def register(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> JSendResponse[AuthLoginResponse]:
    """
    Register new user account.
    Technical Specifications v2 - Section 7.1
    
    **Note:** For TA purposes, registration might be disabled
    and users pre-created by admin.
    """
    try:
        system_logger.info(
            f"Registration attempt for NIM: {request.nim}",
            extra={"event_type": "AUTH_REGISTER_ATTEMPT"}
        )
        
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.nim == request.nim)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            system_logger.warning(
                f"Registration failed - NIM already exists: {request.nim}",
                extra={"event_type": "AUTH_REGISTER_FAILED_EXISTS"}
            )
            return fail_response(
                message="NIM already registered",
                code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new user
        new_user = User(
            nim=request.nim,
            full_name=request.nim,  # Default name, can be updated later
            password_hash=hash_password(request.password),
            current_theta=0.0,
            theta_social=0.0,
            k_factor=32,
            has_completed_pretest=False
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        system_logger.info(
            f"Registration successful for user: {new_user.nim}",
            extra={
                "event_type": "AUTH_REGISTER_SUCCESS",
                "user_id": str(new_user.user_id)
            }
        )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(new_user.user_id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(new_user.user_id)}
        )
        
        response_data = AuthLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user)
        )
        
        return success_response(
            data=response_data,
            code=status.HTTP_201_CREATED,
            message="Registration successful"
        )
        
    except Exception as e:
        await db.rollback()
        system_logger.error(
            f"Registration error: {str(e)}",
            extra={"event_type": "AUTH_REGISTER_ERROR"}
        )
        return error_response(
            message="Internal server error during registration",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )