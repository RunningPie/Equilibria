'''
Modul utk deps injection
utamanya di sini utk get current user
di endpoint-endpoint
'''

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.db.models.user import User
from sqlalchemy.future import select

# === Pake OAUTH2 Bearer token scheme ===
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="JWT",
    auto_error=False  # biar bisa custom error handling
)

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> Optional[User]:
    '''
    Dependency untuk mendapatkan current user dari JWT token
    
    Usage:
    async def some_route(current_user: User = Depends(get_current_user)):
        ...
    '''
    # exception utk reuse
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # cek token
    if not token:
        raise credentials_exception
    
    # decode & validasi
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        # ambil user dari DB
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if user is None:
            raise credentials_exception
        
        return user
    except JWTError:
        raise credentials_exception
    except Exception as e:
        # log error lain yang mungkin terjadi
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def get_current_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db=Depends(get_db)
) -> Optional[User]:
    '''
    Variant dari get_current_user yang mengembalikan None jika token tidak valid atau tidak ada
    
    Usage:
    async def some_route(current_user: Optional[User] = Depends(get_current_optional_user)):
        if current_user:
            # user authenticated
        else:
            # user anonymous
    '''
    try:
        if token is None:
            return None
        
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        return user
    except JWTError:
        return None
    except Exception as e:
        # log error lain yang mungkin terjadi
        return None