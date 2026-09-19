from app.routers.auth import router as auth_router
from app.routers.challenges import router as challenges_router
from app.routers.execution import router as execution_router

__all__ = ["auth_router", "challenges_router", "execution_router"]
