"""
Modules API Router
Technical Specifications v2 - Section 4, 7.2
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_modules():
    """Get all modules - STUB"""
    return {"status": "success", "message": "Get modules - to be implemented"}


@router.get("/{module_id}")
async def get_module_detail(module_id: str):
    """Get module detail - STUB"""
    return {"status": "success", "message": f"Get module {module_id} - to be implemented"}