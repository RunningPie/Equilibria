"""
Authentication API Router
Technical Specifications v2 - Section 7.1, 7.2

Endpoints:
- POST /login - User login with NIM and password
- POST /logout - User logout (invalidate token)
- GET /me - Get current user profile
- PUT /me - Update user profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from datetime import timedelta

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
    LoginResponse,
    UserResponse,
    UserUpdate,
    TokenResponse
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
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with NIM and password. Returns JWT token."
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint with NIM and password.
    Technical Specifications v2 - Section 7.1
    
    **Request:**
    - nim: Student ID (VARCHAR 20)
    - password: Plain text password
    
    **Response:**
    - access_token: JWT token for authentication
    - refresh_token: JWT token for token refresh
    - user: User profile data
    """
    system_logger.info(
        f"Login attempt for NIM: {request.nim}",
        extra={"event_type": "AUTH_LOGIN_ATTEMPT"}
    )
    
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid NIM or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        system_logger.warning(
            f"Login failed - Invalid password for NIM: {request.nim}",
            extra={"event_type": "AUTH_LOGIN_FAILED_INVALID_PASSWORD"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid NIM or password"
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
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Invalidate current session token."
)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint.
    Technical Specifications v2 - Section 7.1
    
    Note: JWT tokens are stateless, so logout is client-side
    (delete token from storage). This endpoint logs the event.
    """
    system_logger.info(
        f"Logout for user: {current_user.nim}",
        extra={
            "event_type": "AUTH_LOGOUT",
            "user_id": str(current_user.user_id)
        }
    )
    
    return {"message": "Logout successful"}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get authenticated user profile."
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    Technical Specifications v2 - Section 7.2
    
    Requires valid JWT token in Authorization header.
    """
    system_logger.debug(
        f"Profile accessed by user: {current_user.nim}",
        extra={
            "event_type": "AUTH_PROFILE_ACCESS",
            "user_id": str(current_user.user_id)
        }
    )
    
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
    description="Update authenticated user profile information."
)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile.
    Technical Specifications v2 - Section 7.2
    
    **Updatable fields:**
    - full_name
    - password (will be hashed)
    """
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
    
    return UserResponse.model_validate(current_user)


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Register a new student account."
)
async def register(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user account.
    Technical Specifications v2 - Section 7.1
    
    **Note:** For TA purposes, registration might be disabled
    and users pre-created by admin.
    """
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NIM already registered"
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
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )