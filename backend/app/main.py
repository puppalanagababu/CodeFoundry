import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate configuration on startup
    validation_errors = settings.validate_production_configuration()
    if validation_errors:
        for err in validation_errors:
            logger.error("Configuration validation warning/error: %s", err)
        if settings.ENVIRONMENT.lower() in ["production", "prod"] and not settings.DEBUG:
            raise RuntimeError(
                f"Production configuration validation failed: {'; '.join(validation_errors)}"
            )
    yield


app = FastAPI(
    title="CodeFoundry API",
    description="Software Engineering Readiness & Simulation Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Appends standard security headers to HTTP responses.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not settings.DEBUG or settings.ENVIRONMENT.lower() in ["production", "prod"]:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Global catch-all exception handler to prevent leaking internal stack traces in production.
    """
    logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
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
        "environment": "development" if settings.DEBUG else settings.ENVIRONMENT,
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
