from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, IntegrityError

from app.db.session import get_db # TODO: db session belum dibuat
from app.db.models import User
from app.schemas.jsend import JSendResponse, JSendStatus
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserUpdate,
    UserResponse,
    LoginResponse,
    LogoutResponse
)

# TODO: core security belum dibuat
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.logging_config import get_loggers
from server.app.db.models import user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

logger = get_loggers()[0] # Ambil system logger untuk logging di auth

@router.post(
    "/register",
    response_model=JSendResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Endpoint for user registration. Creates a new user account with provided NIM, full name, and password."
)
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> JSendResponse[UserResponse]:
    '''
    Register pengguna baru sesuai tech spec 7.3
    
    NIM: 8-10 digit, unique
    Full Name: max 100 characters
    Password: min 8 characters
    '''
    try:
        # cek nim
        result = await db.execute(select(User).where(User.nim == user_data.nim))
        existing_user = result.scalars().first()
        
        if existing_user:
            logger.warning(
                "Registration Failed - NIM already exists",
                extra={"event_type": "AUTH_REGISTRATION_FAILED", "nim": user_data.nim}
            )
            return JSendResponse[LoginResponse](
                status=JSendStatus.FAIL,
                code=status.HTTP_400_BAD_REQUEST,
                message="NIM already registered",
                data=None
            )
        
        # Kalau belum ada, buat user baru
        new_user = User(
            nim=user_data.nim,
            full_name=user_data.full_name,
            password_hash=get_password_hash(user_data.password)
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # buat JWT
        access_token = create_access_token(data={"user_id": str(new_user.user_id)})
        logger.info(
            "User registered successfully",
            extra={"event_type": "AUTH_REGISTER_SUCCESS", "user_id": new_user.user_id}
        )
        return JSendResponse[LoginResponse](
            status=JSendStatus.SUCCESS,
            code=status.HTTP_201_CREATED,
            message="User registered successfully",
            data=LoginResponse(
                user=UserResponse.model_validate(new_user),
                access_token=access_token,
                token_type="bearer"
            )
        )
    except IntegrityError as e:
        logger.error(
            f"Database integrity error during registration: {str(e)}",
            extra={"event_type": "AUTH_REGISTER_ERROR"}
        )
        return JSendResponse[LoginResponse](
            status=JSendStatus.ERROR,
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error during registration",
            data=None
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during registration: {str(e)}",
            extra={"event_type": "AUTH_REGISTER_ERROR"}
        )
        return JSendResponse[LoginResponse](
            status=JSendStatus.ERROR,
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error during registration",
            data=None
        )

@router.post(
    "/login",
    response_model=JSendResponse[LoginResponse],
    summary="User login",
    description="Endpoint for user login. Validates NIM and password, returns access token if successful."
)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> JSendResponse[LoginResponse]:
    '''
    Login pengguna sesuai tech spec 7.3
    
    NIM: 8-10 digit, must exist
    Password: min 8 characters, must match hash in DB
    
    Responsenya JWT (30 menit) + informasi user
    '''
    try:
        # Cari NIM
        result = await db.execute(select(User).where(User.nim == login_data.nim))
        user = result.scalars().first()
        
        # Login gagal - user tidak ditemukan atau password salah
        if not user or not verify_password(login_data.password, user.password_hash):
            logger.warning(
                "Login Failed - Invalid credentials",
                extra={"event_type": "AUTH_LOGIN_FAILED", "nim": login_data.nim}
            )
            return JSendResponse[LoginResponse](
                status=JSendStatus.FAIL,
                code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid NIM or password",
                data=None
            )
        
        # Login berhasil, buat JWT
        access_token = create_access_token(data={"user_id": str(user.user_id)})
        logger.info(
            "User logged in successfully",
            extra={"event_type": "AUTH_LOGIN_SUCCESS", "user_id": user.user_id}
        )
        return JSendResponse[LoginResponse](
            status=JSendStatus.SUCCESS,
            code=status.HTTP_200_OK,
            message="Login successful",
            data=LoginResponse(
                user=UserResponse.model_validate(user),
                access_token=access_token,
                token_type="bearer"
            )
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during login: {str(e)}",
            extra={"event_type": "AUTH_LOGIN_ERROR"}
        )
        return JSendResponse[LoginResponse](
            status=JSendStatus.ERROR,
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error during login",
            data=None
        )

@router.post(
    "/logout",
    response_model=JSendResponse[LogoutResponse],
    summary="User logout",
    description="Endpoint for user logout. Invalidates the user's access token (if token blacklisting is implemented)."
)
async def logout_user(
    current_user: User = Depends(get_current_user),
) -> JSendResponse[LogoutResponse]:
    '''
    Logout pengguna sesuai tech spec 7.3
    
    Karena JWT stateless, logout bisa dilakukan dengan token blacklisting (opsional) atau cukup di client-side dengan menghapus token.
    
    Responsenya hanya pesan sukses logout.
    '''
    logger.info(
        f"Logged out user: {current_user.user_id}",
        extra={"event_type": "AUTH_LOGOUT", "user_id": current_user.user_id}
    )
    return JSendResponse[LogoutResponse](
        status=JSendStatus.SUCCESS,
        code=status.HTTP_200_OK,
        message="Successfully logged out",
        data=LogoutResponse(message="Successfully logged out")
    )

@router.get(
    "/me",
    response_model=JSendResponse[UserResponse],
    summary="Get current user profile",
    description="Endpoint to get the profile of the currently authenticated user."
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> JSendResponse[UserResponse]:
    '''
    Get profil pengguna saat ini sesuai tech spec 7.3
    
    Responsenya informasi user yang sedang login.
    '''
    logger.info(
        f"Fetched profile for user: {current_user.user_id}",
        extra={"event_type": "AUTH_GET_PROFILE", "user_id": current_user.user_id}
    )
    return JSendResponse[UserResponse](
        status=JSendStatus.SUCCESS,
        code=status.HTTP_200_OK,
        message="User profile fetched successfully",
        data=UserResponse.model_validate(current_user)
    )

@router.put(
    "/me",
    response_model=JSendResponse[UserResponse],
    summary="Update current user profile",
    description="Endpoint to update the profile of the currently authenticated user. Allows updating full name and password."
)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSendResponse[UserResponse]:
    '''
    Update profil pengguna saat ini sesuai tech spec 7.3
    
    Bisa update full name dan password (harus verifikasi password lama)
    
    Responsenya informasi user yang sudah diupdate.
    '''
    try:
        if user_update.full_name:
            current_user.full_name = user_update.full_name
        
        if user_update.old_password and user_update.new_password:
            if not verify_password(user_update.old_password, current_user.password_hash):
                logger.warning(
                    "Profile Update Failed - Incorrect old password",
                    extra={"event_type": "AUTH_UPDATE_PROFILE_FAILED", "user_id": current_user.user_id}
                )
                return JSendResponse[UserResponse](
                    status=JSendStatus.FAIL,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="Incorrect old password",
                    data=None
                )
            current_user.password_hash = get_password_hash(user_update.new_password)
        
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(
            f"Updated profile for user: {current_user.user_id}",
            extra={"event_type": "AUTH_UPDATE_PROFILE_SUCCESS", "user_id": current_user.user_id}
        )
        return JSendResponse[UserResponse](
            status=JSendStatus.SUCCESS,
            code=status.HTTP_200_OK,
            message="User profile updated successfully",
            data=UserResponse.model_validate(current_user)
        )
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Unexpected error during profile update: {str(e)}",
            extra={"event_type": "AUTH_UPDATE_PROFILE_ERROR", "user_id": current_user.user_id}
        )
        return JSendResponse[UserResponse](
            status=JSendStatus.ERROR,
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error during profile update",
            data=None
        )