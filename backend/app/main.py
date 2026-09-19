from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import check_db_connection
from app.routers.auth import router as auth_router
from app.routers.challenges import router as challenges_router
from app.routers.dashboard import router as dashboard_router
from app.routers.execution import router as execution_router
from app.routers.leaderboard import router as leaderboard_router
from app.routers.recruiter import router as recruiter_router
from app.routers.submissions import router as submissions_router
from app.routers.users import router as users_router

app = FastAPI(
    title="CodeFoundry API",
    description="Software Engineering Readiness & Simulation Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(challenges_router)
app.include_router(dashboard_router)
app.include_router(execution_router)
app.include_router(leaderboard_router)
app.include_router(recruiter_router)
app.include_router(submissions_router)
app.include_router(users_router)


@app.get("/api/health/", tags=["Health"], status_code=status.HTTP_200_OK)
@app.get("/api/health", tags=["Health"], status_code=status.HTTP_200_OK)
@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health_check():
    """
    Basic health check endpoint reporting service, environment, and database connectivity status.
    """
    db_connected = check_db_connection()
    return {
        "status": "healthy",
        "service": "CodeFoundry API",
        "environment": "development" if settings.DEBUG else "production",
        "database": "connected" if db_connected else "disconnected",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to CodeFoundry API",
        "docs": "/api/docs",
        "health": "/api/health/",
    }
