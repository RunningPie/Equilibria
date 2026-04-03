"""
Leaderboard API Endpoint - Tech Specs v4 Section 7.6-F

GET /api/v1/leaderboard - Returns paginated leaderboard sorted by theta_display
dengan display_name yang diobfuscate untuk privasi (kecuali untuk diri sendiri).
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from typing import Optional

from app.db.models import User
from app.db.session import get_db
from app.core.dependencies import get_current_user, get_current_optional_user
from app.schemas.jsend import JSendResponse, jsend_success
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse
from app.core.logging_config import get_loggers

router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"]
)

logger = get_loggers()[0]


def obfuscate_display_name(full_name: str) -> str:
    """
    Obfuscate display name untuk privasi.
    Contoh: "Dama Daliman" -> "D***n" (first char + *** + last char)
    
    Rules:
    - Jika nama <= 2 karakter: return as-is
    - Jika nama 3 karakter: first + ** + last (tapi tengah jadi *)
    - Jika nama > 3 karakter: first + *** + last
    """
    if len(full_name) <= 2:
        return full_name
    
    first_char = full_name[0]
    last_char = full_name[-1]
    
    return f"{first_char}***{last_char}"


@router.get(
    "",
    response_model=JSendResponse[LeaderboardResponse],
    summary="Get leaderboard rankings",
    description="Returns paginated leaderboard sorted by theta_display descending. "
                "Display names are obfuscated for privacy (except for the current user)."
)
async def get_leaderboard(
    limit: int = Query(default=20, ge=1, le=100, description="Number of entries to return (max 100)"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_optional_user),
) -> JSONResponse:
    """
    Get leaderboard rankings sorted by theta_display.
    
    Query Parameters:
    - limit: Number of entries to return (default 20, max 100)
    - offset: Pagination offset (default 0)
    
    Returns:
    - entries: List of LeaderboardEntry with rank, user_id, display_name, theta_display, is_self
    - total: Total number of users on the leaderboard
    - limit: Limit used in the query
    - offset: Offset used in the query
    
    Display names are obfuscated (e.g., "D***a") except for the current user's own entry.
    """
    
    # Get total count of users
    total_result = await db.execute(select(func.count()).select_from(User))
    total = total_result.scalar()
    
    # Get users sorted by theta_display descending with pagination
    # Note: theta_display is a computed property, so we use the formula directly
    # theta_display = (0.8 * theta_individu) + (0.2 * theta_social)
    stmt = (
        select(User)
        .order_by(desc((0.8 * User.theta_individu) + (0.2 * User.theta_social)))
        .offset(offset)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    # Build leaderboard entries
    entries: list[LeaderboardEntry] = []
    current_user_id = current_user.user_id if current_user else None
    
    for idx, user in enumerate(users):
        rank = offset + idx + 1
        is_self = user.user_id == current_user_id
        
        # Obfuscate display name except for self
        if is_self:
            display_name = user.full_name
        else:
            display_name = obfuscate_display_name(user.full_name)
        
        entries.append(
            LeaderboardEntry(
                rank=rank,
                user_id=user.user_id,
                display_name=display_name,
                theta_display=user.theta_display,
                is_self=is_self
            )
        )
    
    # Log the request
    logger.info(
        f"Leaderboard fetched: limit={limit}, offset={offset}, total={total}",
        extra={
            "event_type": "LEADERBOARD_FETCH",
            "user_id": str(current_user_id) if current_user_id else None,
            "limit": limit,
            "offset": offset
        }
    )
    
    return jsend_success(
        code=HTTP_200_OK,
        message="Leaderboard retrieved successfully",
        data=LeaderboardResponse(
            entries=entries,
            total=total,
            limit=limit,
            offset=offset
        )
    )
