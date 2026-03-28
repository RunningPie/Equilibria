from fastapi import APIRouter
from .auth import router as auth_router
from .pretest import router as pretest_router
from .profile import router as profile_router
from .session import router as session_router
from .collaboration import router as collaboration_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(pretest_router)
api_router.include_router(profile_router)
api_router.include_router(session_router)
api_router.include_router(collaboration_router)