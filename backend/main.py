"""Main FastAPI application entry point."""
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

from utils.config import settings
from utils.database import Database, init_database_async
from utils.logger import setup_logging
from api.health import router as health_router
from api.auth import router as auth_router
from api.organizations import router as org_router
from api.scenes import router as scenes_router
from api.import_3d import router as import_router

setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting application...")
    try:
        # Connect to MongoDB
        await Database.connect()
        
        # Initialize database (create collections and indexes)
        await init_database_async()
        
        logger.info("Application startup completed")
    except Exception as e:
        logger.error("Failed to start application", exc_info=e)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await Database.disconnect()
    logger.info("Application shutdown completed")


# Initialize FastAPI app
app = FastAPI(
    title="Ultimate Spatial AI Platform",
    description="Transform phone videos and 3D files into streamable, interactive 3D scenes",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware for structured logging of all HTTP requests."""
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown"
    )
    
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration=process_time
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error(
            "request_failed",
            duration=process_time,
            exc_info=e
        )
        raise
    finally:
        structlog.contextvars.clear_contextvars()


# Expose Prometheus metrics on /metrics
Instrumentator().instrument(app).expose(app)

# Include Routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(org_router, prefix="/api/v1", tags=["Organizations"])
app.include_router(scenes_router, prefix="/api/v1", tags=["Scenes"])
app.include_router(import_router, prefix="/api/v1/scenes", tags=["3D Import"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Ultimate Spatial AI Platform API",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )

