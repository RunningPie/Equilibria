"""
Profile API Router
Technical Specifications v2 - Section 7.2
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Get user statistics - STUB"""
    return {"status": "success", "message": "Get stats - to be implemented"}


@router.get("/history")
async def get_history():
    """Get assessment history - STUB"""
    return {"status": "success", "message": "Get history - to be implemented"}