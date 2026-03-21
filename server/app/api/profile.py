from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK
from app.db.models import User
from app.core.dependencies import get_current_user
from app.schemas.jsend import JSendResponse, jsend_success
from app.schemas.profile import ProfileStats
from app.core.logging_config import get_loggers

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

logger = get_loggers()[0]


@router.get(
    "/stats",
    response_model=JSendResponse[ProfileStats],
    summary="Get user profile statistics",
    description="Returns theta_individu, theta_social, and theta_display values for the current user."
)
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get profile statistics for current user.
    
    Returns:
    - theta_individu: Individual Elo rating [0, 2000]
    - theta_social: Social Elo rating [0, 2000] 
    - theta_display: Weighted average (0.8 × θ_individu) + (0.2 × θ_social)
    """
    logger.info(
        f"Fetched profile stats for user: {current_user.user_id}",
        extra={"event_type": "PROFILE_STATS", "user_id": current_user.user_id}
    )
    
    return jsend_success(
        code=HTTP_200_OK,
        message="Profile statistics retrieved successfully",
        data=ProfileStats(
            theta_individu=current_user.theta_individu,
            theta_social=current_user.theta_social,
            theta_display=current_user.theta_display
        )
    )
