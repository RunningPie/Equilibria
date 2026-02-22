"""
Dependency Injection Module
Technical Specifications v2 - Section 7.1, 7.2

Provides reusable dependencies for FastAPI routes:
- Database session
- JWT token validation
- Current user retrieval
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import datetime, timedelta

from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.core.logging_config import get_loggers
from app.db.models.user import User
from sqlalchemy import select

system_logger, _ = get_loggers()

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """
    Dependency for database session.
    Ensures proper session cleanup after each request.
    Technical Specifications v2 - Section 3.1
    """
    db = AsyncSessionLocal()
    try:
        yield db
        await db.commit()
    except Exception as e:
        await db.rollback()
        system_logger.error(
            f"Database session error: {str(e)}",
            extra={"event_type": "DB_SESSION_ERROR"}
        )
        raise
    finally:
        await db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    Technical Specifications v2 - Section 7.1
    
    Raises:
        HTTPException 401: Invalid or expired token
        HTTPException 404: User not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        system_logger.warning(
            "Authentication attempt without credentials",
            extra={"event_type": "AUTH_NO_CREDENTIALS"}
        )
        raise credentials_exception
    
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_type: str = payload.get("type")
        if token_type != "access":
            raise credentials_exception
            
    except JWTError as e:
        system_logger.warning(
            f"JWT validation failed: {str(e)}",
            extra={"event_type": "AUTH_JWT_INVALID"}
        )
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        system_logger.warning(
            f"User not found for token: {user_id}",
            extra={"event_type": "AUTH_USER_NOT_FOUND"}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.
    Technical Specifications v2 - Section 7.1
    
    Args:
        data: Payload data (should include user_id as 'sub')
        expires_delta: Token expiration time (default from settings)
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "type": "access"  # Token type for validation
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token (longer expiration).
    Technical Specifications v2 - Section 7.1
    """
    return create_access_token(
        data,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )