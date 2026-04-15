"""
Endpoint API Admin - Fungsionalitas administratif
Berisi operasi CRUD user dan akses log
"""
import os
import json
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import User
from app.schemas.jsend import JSendResponse, jsend_success, jsend_fail, jsend_error
from app.schemas.admin import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    UserListResponse,
    LogQueryParams,
    LogsResponse,
    LogEntry,
    DeleteUserResponse
)
from app.core.dependencies import get_current_user
from app.core.security import get_password_hash
from app.core.logging_config import get_loggers
from app.core.config import settings

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

logger = get_loggers()[0]

# Direktori log (relatif terhadap root proyek)
SYSLOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "syslogs")
ASSLOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "asslogs")


# === Dependency Autorisasi Admin ===

async def get_current_admin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency untuk memastikan hanya admin yang bisa mengakses endpoint admin
    """
    if not current_user.is_admin:
        logger.warning(
            f"Admin access denied for user: {current_user.user_id}",
            extra={"event_type": "ADMIN_ACCESS_DENIED", "user_id": current_user.user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# === Endpoint CRUD User ===

@router.get(
    "/users",
    response_model=JSendResponse[UserListResponse],
    summary="List all users",
    description="Get paginated list of all users with optional sorting. Admin only."
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page (max 1000)"),
    sortby: str = Query(None, description="Sort by column: 'nim' or 'name' (full_name)"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List semua user dengan pagination dan sorting opsional (hanya admin)
    """
    try:
        # Validasi parameter sortby
        order_by = None
        if sortby:
            sortby_lower = sortby.lower()
            if sortby_lower not in ('nim', 'name'):
                return jsend_fail(
                    code=status.HTTP_400_BAD_REQUEST,
                    message="Invalid sortby value. Must be 'nim' or 'name'"
                )
            order_by = User.nim if sortby_lower == 'nim' else User.full_name
        
        # Ambil total count menggunakan func.count untuk efisiensi
        count_result = await db.execute(select(func.count()).select_from(User))
        total = count_result.scalar()
        
        # Bangun query
        query = select(User)
        if order_by is not None:
            query = query.order_by(order_by.asc())
        
        # Ambil user dengan pagination
        offset = (page - 1) * page_size
        result = await db.execute(
            query
            .offset(offset)
            .limit(page_size)
        )
        users = result.scalars().all()
        
        logger.info(
            f"Admin {admin.user_id} listed users: page={page}, page_size={page_size}, sortby={sortby}",
            extra={"event_type": "ADMIN_LIST_USERS", "admin_id": admin.user_id, "page": page, "page_size": page_size, "sortby": sortby}
        )
        
        return jsend_success(
            code=status.HTTP_200_OK,
            message="Users retrieved successfully",
            data=UserListResponse(
                users=[AdminUserResponse.model_validate(user) for user in users],
                total=total,
                page=page,
                page_size=page_size
            )
        )
    except Exception as e:
        logger.error(
            f"Error listing users: {str(e)}",
            extra={"event_type": "ADMIN_LIST_USERS_ERROR", "admin_id": admin.user_id}
        )
        return jsend_error(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error retrieving users"
        )


@router.get(
    "/users/{user_id}",
    response_model=JSendResponse[AdminUserResponse],
    summary="Get user by ID",
    description="Get detailed information about a specific user. Admin only."
)
async def get_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Ambil user tertentu berdasarkan ID (hanya admin)
    """
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if not user:
            return jsend_fail(
                code=status.HTTP_404_NOT_FOUND,
                message="User not found"
            )
        
        logger.info(
            f"Admin {admin.user_id} fetched user {user_id}",
            extra={"event_type": "ADMIN_GET_USER", "admin_id": admin.user_id, "target_user_id": user_id}
        )
        
        return jsend_success(
            code=status.HTTP_200_OK,
            message="User retrieved successfully",
            data=AdminUserResponse.model_validate(user)
        )
    except Exception as e:
        logger.error(
            f"Error getting user {user_id}: {str(e)}",
            extra={"event_type": "ADMIN_GET_USER_ERROR", "admin_id": admin.user_id, "target_user_id": user_id}
        )
        return jsend_error(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error retrieving user"
        )


@router.post(
    "/users",
    response_model=JSendResponse[AdminUserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user account. Admin only."
)
async def create_user(
    user_data: AdminUserCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Buat user baru (hanya admin)
    """
    try:
        # Cek apakah NIM sudah ada
        result = await db.execute(select(User).where(User.nim == user_data.nim))
        if result.scalars().first():
            return jsend_fail(
                code=status.HTTP_400_BAD_REQUEST,
                message="NIM already registered"
            )
        
        # Buat user baru
        new_user = User(
            nim=user_data.nim,
            full_name=user_data.full_name,
            password_hash=get_password_hash(user_data.password),
            group_assignment=user_data.group_assignment or 'B',
            is_admin=user_data.is_admin or False
        )
        
        db.add(new_user)
        await db.flush()  # Flush untuk mendapatkan nilai auto-generated (user_id, created_at, defaults)
        await db.refresh(new_user)  # Refresh untuk mengisi field auto-generated
        
        logger.info(
            f"Admin {admin.user_id} created user {new_user.user_id}",
            extra={"event_type": "ADMIN_CREATE_USER", "admin_id": admin.user_id, "new_user_id": str(new_user.user_id)}
        )
        
        return jsend_success(
            code=status.HTTP_201_CREATED,
            message="User created successfully",
            data=AdminUserResponse.model_validate(new_user)
        )
    except Exception as e:
        # Catatan: db.rollback() ditangani oleh get_db() context manager saat exception
        logger.error(
            f"Error creating user: {str(e)}",
            extra={"event_type": "ADMIN_CREATE_USER_ERROR", "admin_id": admin.user_id}
        )
        raise  # Re-raise to let get_db() handle rollback


@router.put(
    "/users/{user_id}",
    response_model=JSendResponse[AdminUserResponse],
    summary="Update user",
    description="Update an existing user. Admin only."
)
async def update_user(
    user_id: UUID,
    user_update: AdminUserUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update user (hanya admin)
    """
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if not user:
            return jsend_fail(
                code=status.HTTP_404_NOT_FOUND,
                message="User not found"
            )
        
        # Update field jika diberikan
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.password is not None:
            user.password_hash = get_password_hash(user_update.password)
        if user_update.group_assignment is not None:
            user.group_assignment = user_update.group_assignment
        if user_update.status is not None:
            user.status = user_update.status
        if user_update.is_admin is not None:
            user.is_admin = user_update.is_admin
        if user_update.theta_individu is not None:
            user.theta_individu = user_update.theta_individu
        if user_update.theta_social is not None:
            user.theta_social = user_update.theta_social
        
        # Catatan: db.commit() ditangani oleh get_db() context manager saat exit berhasil
        
        logger.info(
            f"Admin {admin.user_id} updated user {user_id}",
            extra={"event_type": "ADMIN_UPDATE_USER", "admin_id": admin.user_id, "target_user_id": user_id}
        )
        
        return jsend_success(
            code=status.HTTP_200_OK,
            message="User updated successfully",
            data=AdminUserResponse.model_validate(user)
        )
    except Exception as e:
        # Catatan: db.rollback() ditangani oleh get_db() context manager saat exception
        logger.error(
            f"Error updating user {user_id}: {str(e)}",
            extra={"event_type": "ADMIN_UPDATE_USER_ERROR", "admin_id": admin.user_id, "target_user_id": user_id}
        )
        raise  # Re-raise to let get_db() handle rollback


@router.delete(
    "/users/{user_id}",
    response_model=JSendResponse[DeleteUserResponse],
    summary="Soft delete user",
    description="Soft delete a user account (marks as deleted, preserves data). Admin only."
)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Soft delete user (hanya admin) - mempertahankan semua data terkait untuk analytics.
    Catatan: db.commit() ditangani otomatis oleh get_db() context manager.
    """
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if not user:
            return jsend_fail(
                code=status.HTTP_404_NOT_FOUND,
                message="User not found"
            )
        
        # Cegah admin menghapus dirinya sendiri
        if user.user_id == admin.user_id:
            return jsend_fail(
                code=status.HTTP_400_BAD_REQUEST,
                message="Cannot delete your own account"
            )
        
        # Cek apakah sudah dihapus
        if user.is_deleted:
            return jsend_fail(
                code=status.HTTP_400_BAD_REQUEST,
                message="User is already deleted"
            )
        
        # Soft delete: tandai sebagai dihapus dan anonimkan PII
        deleted_at = datetime.now()
        user.is_deleted = True
        user.deleted_at = deleted_at
        # Anonimkan NIM: 'del_' (4 karakter) + 16 karakter pertama UUID = maksimal 20 karakter
        user.nim = f"del_{str(user.user_id)[:16]}"
        user.full_name = "Deleted User"
        user.password_hash = "deleted"  # Invalidasi password
        
        # Catatan: db.commit() ditangani oleh get_db() context manager saat exit berhasil
        
        logger.info(
            f"Admin {admin.user_id} soft deleted user {user_id}",
            extra={"event_type": "ADMIN_SOFT_DELETE_USER", "admin_id": admin.user_id, "deleted_user_id": user_id}
        )
        
        return jsend_success(
            code=status.HTTP_200_OK,
            message="User soft deleted successfully",
            data=DeleteUserResponse(
                message="User soft deleted successfully",
                deleted_user_id=user_id,
                is_deleted=True,
                deleted_at=deleted_at
            )
        )
    except Exception as e:
        # Catatan: db.rollback() ditangani oleh get_db() context manager saat exception
        logger.error(
            f"Error soft deleting user {user_id}: {str(e)}",
            extra={"event_type": "ADMIN_DELETE_USER_ERROR", "admin_id": admin.user_id, "target_user_id": user_id}
        )
        raise  # Re-raise to let get_db() handle rollback


# === Endpoint Akses Log ===

def _get_log_files(log_dir: str, date_str: Optional[str] = None) -> List[str]:
    """
    Fungsi helper untuk mendapatkan file log, opsional difilter berdasarkan tanggal
    """
    if not os.path.exists(log_dir):
        return []
    
    all_files = os.listdir(log_dir)
    log_files = [f for f in all_files if f.endswith('.json') and not f.startswith('.')]
    
    if date_str:
        # Filter berdasarkan tanggal - file bernama seperti: syslog_YYYYMMDD_HHMMSS.json
        log_files = [f for f in log_files if f"_{date_str}_" in f]
    
    return sorted(log_files)


def _read_log_file(log_dir: str, filename: str) -> List[LogEntry]:
    """
    Fungsi helper untuk membaca dan parse file log
    """
    entries = []
    filepath = os.path.join(log_dir, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    log_data = json.loads(line)
                    entries.append(LogEntry(
                        timestamp=log_data.get('timestamp'),
                        level=log_data.get('level'),
                        message=log_data.get('message', ''),
                        extra=log_data.get('extra')
                    ))
                except json.JSONDecodeError:
                    # Lewati baris yang malformed
                    continue
    except Exception:
        pass
    
    return entries


def _read_log_file_limited(log_dir: str, filename: str, limit: int) -> List[LogEntry]:
    """
    Fungsi helper untuk membaca N baris terakhir dari file log secara efisien
    """
    entries = []
    filepath = os.path.join(log_dir, filename)
    
    try:
        # Baca semua baris, parse dari akhir (yang paling baru terlebih dahulu)
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Proses dari akhir (entry terbaru) hingga limit
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                log_data = json.loads(line)
                entries.append(LogEntry(
                    timestamp=log_data.get('timestamp'),
                    level=log_data.get('level'),
                    message=log_data.get('message', ''),
                    extra=log_data.get('extra')
                ))
                if len(entries) >= limit:
                    break
            except json.JSONDecodeError:
                continue
        
        # Balik ke urutan kronologis
        entries.reverse()
    except Exception:
        pass
    
    return entries


@router.get(
    "/logs/syslogs",
    response_model=JSendResponse[LogsResponse],
    summary="Get system logs",
    description="Get system logs with optional date filtering and limit. Admin only."
)
async def get_syslogs(
    date: Optional[str] = Query(None, pattern=r"^\d{8}$", description="Date in YYYYMMDD format"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit to N latest entries from the latest log file"),
    admin: User = Depends(get_current_admin)
) -> JSONResponse:
    """
    Ambil system logs (hanya admin)
    
    - **date**: Filter tanggal opsional dalam format YYYYMMDD (misal, 20260411)
    - **limit**: Jika diberikan, hanya mengembalikan N entry terbaru dari file log terakhir
    """
    try:
        log_files = _get_log_files(SYSLOG_DIR, date)
        
        all_entries = []
        if limit and log_files:
            # Get the latest log file only and return last N entries
            latest_file = log_files[-1]  # Files are sorted, last is latest
            all_entries = _read_log_file_limited(SYSLOG_DIR, latest_file, limit)
            # Only include the file we read from
            log_files = [latest_file]
        else:
            # Read all log entries from all matching files
            for log_file in log_files:
                entries = _read_log_file(SYSLOG_DIR, log_file)
                all_entries.extend(entries)
        
        logger.info(
            f"Admin {admin.user_id} accessed syslogs: date={date}, limit={limit}, files={len(log_files)}, entries={len(all_entries)}",
            extra={"event_type": "ADMIN_GET_SYSLOGS", "admin_id": admin.user_id, "date": date, "limit": limit}
        )
        
        return jsend_success(
            code=status.HTTP_200_OK,
            message="System logs retrieved successfully",
            data=LogsResponse(
                date=date,
                files=log_files,
                logs=all_entries,
                total_entries=len(all_entries)
            )
        )
    except Exception as e:
        logger.error(
            f"Error retrieving syslogs: {str(e)}",
            extra={"event_type": "ADMIN_GET_SYSLOGS_ERROR", "admin_id": admin.user_id}
        )
        return jsend_error(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error retrieving system logs"
        )


@router.get(
    "/logs/asslogs",
    response_model=JSendResponse[LogsResponse],
    summary="Get assessment logs",
    description="Get assessment logs with optional date filtering and limit. Admin only."
)
async def get_asslogs(
    date: Optional[str] = Query(None, pattern=r"^\d{8}$", description="Date in YYYYMMDD format"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit to N latest entries from the latest log file"),
    admin: User = Depends(get_current_admin)
) -> JSONResponse:
    """
    Ambil assessment logs (hanya admin)
    
    - **date**: Filter tanggal opsional dalam format YYYYMMDD (misal, 20260411)
    - **limit**: Jika diberikan, hanya mengembalikan N entry terbaru dari file log terakhir
    """
    try:
        log_files = _get_log_files(ASSLOG_DIR, date)
        
        all_entries = []
        if limit and log_files:
            # Get the latest log file only and return last N entries
            latest_file = log_files[-1]  # Files are sorted, last is latest
            all_entries = _read_log_file_limited(ASSLOG_DIR, latest_file, limit)
            # Only include the file we read from
            log_files = [latest_file]
        else:
            # Read all log entries from all matching files
            for log_file in log_files:
                entries = _read_log_file(ASSLOG_DIR, log_file)
                all_entries.extend(entries)
        
        logger.info(
            f"Admin {admin.user_id} accessed asslogs: date={date}, limit={limit}, files={len(log_files)}, entries={len(all_entries)}",
            extra={"event_type": "ADMIN_GET_ASSLOGS", "admin_id": admin.user_id, "date": date, "limit": limit}
        )
        
        return jsend_success(
            code=status.HTTP_200_OK,
            message="Assessment logs retrieved successfully",
            data=LogsResponse(
                date=date,
                files=log_files,
                logs=all_entries,
                total_entries=len(all_entries)
            )
        )
    except Exception as e:
        logger.error(
            f"Error retrieving asslogs: {str(e)}",
            extra={"event_type": "ADMIN_GET_ASSLOGS_ERROR", "admin_id": admin.user_id}
        )
        return jsend_error(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error retrieving assessment logs"
        )
