from fastapi import APIRouter, Response
from pydantic import BaseModel
import time

from utils.database import get_db
from utils.valkey_client import get_valkey_client
from utils.minio_client import get_minio_client
# Assuming celery_app might be reachable for inspection
try:
    from workers.celery_app import celery_app
    has_celery = True
except ImportError:
    has_celery = False

router = APIRouter(prefix="/health", tags=["health"])

class HealthResponse(BaseModel):
    status: str

class DetailedHealthResponse(BaseModel):
    status: str
    dependencies: dict
    version: str = "1.0.0"

@router.get("", response_model=HealthResponse)
async def health_check():
    """Basic alive check for load balancers."""
    return HealthResponse(status="ok")

@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(response: Response):
    """Detailed health check validating all external dependencies."""
    deps = {
        "mongodb": "unhealthy",
        "valkey": "unhealthy",
        "minio": "unhealthy",
        "celery": "unhealthy" if has_celery else "unavailable"
    }
    
    overall_status = "ok"
    
    # Check MongoDB
    try:
        db = await get_db()
        # Perform quick ping
        await db.command("ping")
        deps["mongodb"] = "ok"
    except Exception:
        overall_status = "degraded"
        
    # Check Valkey
    try:
        valkey = get_valkey_client()
        if valkey and valkey.ping():
            deps["valkey"] = "ok"
        else:
            overall_status = "degraded"
    except Exception as e:
        overall_status = "degraded"
        deps["valkey"] = f"error: {str(e)[:50]}"
        
    # Check MinIO
    try:
        minio = get_minio_client()
        if minio and minio.is_connected():
            deps["minio"] = "ok"
        else:
            overall_status = "degraded"
    except Exception as e:
        overall_status = "degraded"
        deps["minio"] = f"error: {str(e)[:50]}"

    # Check Celery
    if has_celery:
        try:
            # We just test connection to broker using valkey ping
            # Since celery uses valkey for this setup, we align with valkey status
            if deps["valkey"] == "ok":
                deps["celery"] = "ok"
            else:
                overall_status = "degraded"
        except Exception:
            pass

    if overall_status != "ok":
        response.status_code = 503

    return DetailedHealthResponse(status=overall_status, dependencies=deps)
