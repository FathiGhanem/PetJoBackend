"""Main FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from api.v1.api import api_router
from core.config import settings
from core.logging import setup_logging
from core.rate_limit import limiter
from core.token_blacklist import close_redis, init_redis
from db.base import Base
from db.session import engine
from exceptions import PetJoException
from middleware.csrf import CSRFMiddleware
from middleware.error_handler import (
    general_exception_handler,
    integrity_error_handler,
    petjo_exception_handler,
    validation_exception_handler,
)

# Setup logging
setup_logging(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting PetJo API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    
    # Initialize Redis for token blacklist
    init_redis()
    
    async with engine.begin() as conn:
        # Create tables (in production, use Alembic migrations)
        if settings.ENVIRONMENT == "development":
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
    
    logger.info("PetJo API started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down PetJo API...")
    await engine.dispose()
    close_redis()
    logger.info("PetJo API shut down successfully")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PetJo API - A comprehensive pet management platform",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add rate limiting state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CSRF protection middleware
app.add_middleware(CSRFMiddleware)

# Register exception handlers
app.add_exception_handler(PetJoException, petjo_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to PetJo API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION
    }


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
