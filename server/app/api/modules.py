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
from app.db.models.user_module_progress import UserModuleProgress

router = APIRouter(prefix="/modules", tags=["Modules"])

@router.get("")
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
        
        # Cek progress user
        progress_result = await db.execute(
            select(UserModuleProgress).where(
                UserModuleProgress.user_id == current_user.user_id
            )
        )
        user_progress = {p.module_id: p for p in progress_result.scalars().all()}
        
        data = []
        
        previous_completed = True
        
        for module in modules:
            if module.module_id == "CH01":
                is_locked = False
            else:
                is_locked = not previous_completed
                
            progress = user_progress.get(module.module_id)
            is_completed = progress.is_completed if progress else False
            
            if is_completed:
                previous_completed = True
            elif not is_locked:
                # bisa diakses tapi blm beres
                previous_completed = False
        
            data.append(
                {
                    "module_id": module.module_id,
                    "title": module.title,
                    "description": module.description,
                    "is_locked": is_locked,
                    "difficulty_range": [module.difficulty_min, module.difficulty_max]
                }
            )
        
        return jsend_success(
            code=HTTP_200_OK,
            message="Modules retrieved",
            data=data
        )
        
    except Exception as e:
        logger.info(f"[MODULES Endpoint] Error retrieving modules: {str(e)}")
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving modules"
        )