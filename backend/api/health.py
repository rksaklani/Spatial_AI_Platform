"""
Health check endpoints for monitoring platform status.

Provides basic liveness check and detailed dependency health checks
for MongoDB, Valkey, MinIO, and Celery workers.
"""

from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Optional
import logging

from utils.database import get_db
from utils.valkey_client import get_valkey_client
from utils.minio_client import get_minio_client

logger = logging.getLogger(__name__)

# Try to import Celery app for worker inspection
try:
    from workers.celery_app import celery_app
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    celery_app = None

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Basic health check response."""
    status: str


class DependencyStatus(BaseModel):
    """Individual dependency status."""
    mongodb: str = "unhealthy"
    valkey: str = "unhealthy"
    minio: str = "unhealthy"
    celery: str = "unavailable"


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with dependency status."""
    status: str
    dependencies: DependencyStatus
    version: str = "1.0.0"
    celery_workers: Optional[int] = None


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Basic liveness check for load balancers and orchestrators.
    
    Returns 200 OK if the API is responsive.
    """
    return HealthResponse(status="ok")


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(response: Response):
    """
    Detailed health check validating all external dependencies.
    
    Checks:
    - MongoDB: Connection and ping
    - Valkey: Connection and ping
    - MinIO: Connection and bucket listing
    - Celery: Worker availability via broker inspection
    
    Returns 503 if any critical dependency is unhealthy.
    """
    deps = DependencyStatus()
    overall_status = "ok"
    celery_worker_count = None
    
    # Check MongoDB
    try:
        db = await get_db()
        await db.command("ping")
        deps.mongodb = "ok"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        overall_status = "degraded"
        deps.mongodb = f"error: {str(e)[:50]}"
    
    # Check Valkey (Redis-compatible)
    try:
        valkey = get_valkey_client()
        if valkey and valkey.ping():
            deps.valkey = "ok"
        else:
            overall_status = "degraded"
            deps.valkey = "ping failed"
    except Exception as e:
        logger.error(f"Valkey health check failed: {e}")
        overall_status = "degraded"
        deps.valkey = f"error: {str(e)[:50]}"
    
    # Check MinIO
    try:
        minio = get_minio_client()
        if minio and minio.is_connected():
            deps.minio = "ok"
        else:
            overall_status = "degraded"
            deps.minio = "connection failed"
    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        overall_status = "degraded"
        deps.minio = f"error: {str(e)[:50]}"
    
    # Check Celery workers
    if HAS_CELERY and celery_app:
        try:
            # Inspect active workers via control ping
            inspect = celery_app.control.inspect(timeout=2)
            active_workers = inspect.ping()
            
            if active_workers:
                celery_worker_count = len(active_workers)
                deps.celery = "ok"
            else:
                # No workers responded, but broker might be fine
                # Check if valkey is ok (which is the broker)
                if deps.valkey == "ok":
                    deps.celery = "no workers"
                    # This is degraded but not critical
                    if overall_status == "ok":
                        overall_status = "degraded"
                else:
                    deps.celery = "broker unreachable"
                    overall_status = "degraded"
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            # If Valkey is ok, Celery broker is likely ok
            if deps.valkey == "ok":
                deps.celery = "inspection timeout"
            else:
                deps.celery = f"error: {str(e)[:50]}"
                overall_status = "degraded"
    else:
        deps.celery = "unavailable"
    
    if overall_status != "ok":
        response.status_code = 503
    
    return DetailedHealthResponse(
        status=overall_status,
        dependencies=deps,
        celery_workers=celery_worker_count
    )


@router.get("/ready")
async def readiness_check(response: Response):
    """
    Kubernetes-style readiness check.
    
    Returns 200 only if all critical dependencies are available.
    Returns 503 if the service should not receive traffic.
    """
    # Check critical dependencies
    try:
        # MongoDB must be available
        db = await get_db()
        await db.command("ping")
    except Exception:
        response.status_code = 503
        return {"ready": False, "reason": "mongodb unavailable"}
    
    try:
        # Valkey must be available for caching and auth
        valkey = get_valkey_client()
        if not valkey or not valkey.ping():
            response.status_code = 503
            return {"ready": False, "reason": "valkey unavailable"}
    except Exception:
        response.status_code = 503
        return {"ready": False, "reason": "valkey connection error"}
    
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness check.
    
    Returns 200 if the application is running (even if degraded).
    Used to detect if the container should be restarted.
    """
    return {"alive": True}
