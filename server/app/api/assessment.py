"""
Assessment API Router
Technical Specifications v2 - Section 6.2, 6.3, 7.2
"""
from fastapi import APIRouter, HTTPException, status
from app.core.logging_config import log_assessment_event

router = APIRouter()


@router.post("/start")
async def start_session():
    """Start adaptive session - STUB"""
    return {"status": "success", "message": "Start session - to be implemented"}


@router.post("/{session_id}/submit")
async def submit_answer(session_id: str):
    """
    Submit answer - STUB
    This endpoint will trigger:
    1. Sandbox execution
    2. Elo update
    3. Stagnation detection
    4. Assessment logging (DB + flat file)
    """
    # Example logging call (will be implemented)
    # log_assessment_event(
    #     user_id="uuid",
    #     session_id=session_id,
    #     question_id="CH01-Q001",
    #     theta_before=0.0,
    #     theta_after=0.1,
    #     is_correct=True,
    #     execution_time_ms=1200
    # )
    return {"status": "success", "message": "Submit answer - to be implemented"}