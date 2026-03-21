'''
Ini core modul untuk:
1. buat hash
2. verifikasi hash
3. buat JWT token
'''

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional
from app.core.config import settings

# === Password Hashing (tech spec 10.3) ===

# setup konfig argon2id
# sesuai rekomendasi RFC 9106
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__type="id",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''
    Verifikasi password dengan hash
    '''
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    '''
    Hash password dengan argon2id
    '''
    return pwd_context.hash(password)

# === JWT Token Management (tech spec 10.4) ===
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    '''
    Buat JWT access token dengan payload data dan expiration
    '''
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)))
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    '''
    Decode dan verifikasi JWT token, kembalikan payload jika valid
    '''
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None