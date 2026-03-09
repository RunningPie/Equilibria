from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from app.db.session import get_db
from app.schemas.jsend import jsend_success, jsend_error
from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.models.module import Module

router = APIRouter(prefix="/modules", tags=["Modules"])

@router.get("/")
async def list_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    '''
    Ambil semua modul dan status pengerjaannya
    Logikanya: CH01 selalu terbuka. CH02 terkunci kalau CH01 belum selesai
    '''
    try:
        result = await db.execute(select(Module).order_by(Module.module_id))
        modules = result.scalars().all()
        
        data = [
            {
                "module_id": m.module_id,
                "title": m.title,
                "description": m.description,
                "is_locked": m.is_locked,
                "difficulty_range": [m.difficulty_min, m.difficulty_max]
            } for m in modules
        ]
        
        return jsend_success(
            code=HTTP_200_OK,
            message="Modules retrieved",
            data=data
        )
        
    except Exception as e:
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving modules"
            logger.info(f"[MODULES Endpoint] Error retrieving modules: {str(e)}")
        )