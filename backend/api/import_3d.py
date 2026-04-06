"""
3D File Import API Endpoints

Task 14.1: Create import upload endpoint
- Multipart file upload for 3D files
- Format validation (PLY, LAS, LAZ, OBJ, GLB, GLTF, SPLAT, STL, FBX, DAE, E57, IFC)
- File size validation (max 5GB)
- Trigger async processing pipeline
"""

import os
import uuid
import shutil
import tempfile
from datetime import datetime
from typing import Optional, List
from enum import Enum

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field

from api.deps import get_current_user
from utils.database import get_db
from models.user import UserInDB
from models.scene import SceneInDB, SceneStatus
from services.tenant_context import TenantContext, get_tenant_context
from utils.minio_client import get_minio_client
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/import", tags=["3D Import"])


# =============================================================================
# Constants
# =============================================================================

# Supported 3D file formats with metadata
SUPPORTED_FORMATS = {
    ".ply": {"type": "point_cloud", "name": "PLY Point Cloud/Mesh", "parser": "ply"},
    ".las": {"type": "point_cloud", "name": "LAS Point Cloud", "parser": "las"},
    ".laz": {"type": "point_cloud", "name": "LAZ Compressed Point Cloud", "parser": "las"},
    ".obj": {"type": "mesh", "name": "Wavefront OBJ", "parser": "obj"},
    ".glb": {"type": "mesh", "name": "glTF Binary", "parser": "gltf"},
    ".gltf": {"type": "mesh", "name": "glTF JSON", "parser": "gltf"},
    ".splat": {"type": "gaussian", "name": "Gaussian Splatting", "parser": "splat"},
    ".stl": {"type": "mesh", "name": "STL Mesh", "parser": "stl"},
    ".fbx": {"type": "mesh", "name": "Autodesk FBX", "parser": "fbx"},
    ".dae": {"type": "mesh", "name": "COLLADA", "parser": "dae"},
    ".e57": {"type": "point_cloud", "name": "E57 Point Cloud", "parser": "e57"},
    ".ifc": {"type": "bim", "name": "IFC BIM Model", "parser": "ifc"},
}

# File size limits
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5GB
MAX_FILE_SIZE_MB = MAX_FILE_SIZE_BYTES / (1024 * 1024)

# Chunk size for streaming uploads
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks


# =============================================================================
# Enums and Models
# =============================================================================

class ImportFormatType(str, Enum):
    """Type of 3D format."""
    POINT_CLOUD = "point_cloud"
    MESH = "mesh"
    GAUSSIAN = "gaussian"
    BIM = "bim"


class ImportStatus(str, Enum):
    """Import job status."""
    QUEUED = "queued"
    PENDING = "pending"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    PROCESSING = "processing"
    OPTIMIZING = "optimizing"
    TILING = "tiling"
    COMPLETED = "completed"
    FAILED = "failed"


class SupportedFormatInfo(BaseModel):
    """Information about a supported format."""
    extension: str
    format_type: ImportFormatType
    name: str
    parser: str


class ImportUploadResponse(BaseModel):
    """Response from import upload endpoint."""
    scene_id: str = Field(..., description="Unique scene identifier")
    job_id: str = Field(..., description="Processing job identifier")
    filename: str = Field(..., description="Original filename")
    format: str = Field(..., description="Detected file format extension")
    format_type: ImportFormatType = Field(..., description="Type of 3D format")
    file_size_bytes: int = Field(..., description="File size in bytes")
    status: ImportStatus = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message")


class ImportStatusResponse(BaseModel):
    """Response for import status check."""
    scene_id: str
    job_id: str
    status: ImportStatus
    progress_percent: float = Field(0, ge=0, le=100)
    current_step: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SupportedFormatsResponse(BaseModel):
    """Response listing supported formats."""
    formats: List[SupportedFormatInfo]
    max_file_size_mb: float


# =============================================================================
# Helper Functions
# =============================================================================

def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension from filename."""
    if not filename:
        return ""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def validate_file_format(filename: str) -> tuple[str, dict]:
    """
    Validate file format is supported.
    
    Returns:
        Tuple of (extension, format_info)
        
    Raises:
        HTTPException if format not supported
    """
    ext = get_file_extension(filename)
    
    if not ext:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_format",
                "message": "File has no extension",
                "supported_formats": list(SUPPORTED_FORMATS.keys()),
            }
        )
    
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_format",
                "message": f"Format '{ext}' is not supported",
                "supported_formats": list(SUPPORTED_FORMATS.keys()),
            }
        )
    
    return ext, SUPPORTED_FORMATS[ext]


async def validate_file_size(file: UploadFile) -> int:
    """
    Validate file size is within limits.
    
    Returns:
        File size in bytes
        
    Raises:
        HTTPException if file too large
    """
    # Try to get size from content-length header first
    file_size = 0
    
    # Read file to get actual size (for streaming uploads)
    # We'll need to reset the file position after
    chunk = await file.read(UPLOAD_CHUNK_SIZE)
    while chunk:
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "file_too_large",
                    "message": f"File exceeds maximum size of {MAX_FILE_SIZE_MB:.0f}MB",
                    "max_size_bytes": MAX_FILE_SIZE_BYTES,
                }
            )
        chunk = await file.read(UPLOAD_CHUNK_SIZE)
    
    # Reset file position for actual upload
    await file.seek(0)
    
    return file_size


async def save_uploaded_file(
    file: UploadFile,
    scene_id: str,
    organization_id: str,
) -> tuple[str, int]:
    """
    Save uploaded file to MinIO storage.
    
    Returns:
        Tuple of (object_path, file_size)
    """
    minio = get_minio_client()
    
    # Ensure bucket exists
    if not minio.bucket_exists("imports"):
        minio.create_bucket("imports")
    
    # Generate object path
    ext = get_file_extension(file.filename)
    object_path = f"{organization_id}/{scene_id}/original{ext}"
    
    # Save to temporary file first (MinIO needs file path or bytes)
    temp_dir = tempfile.mkdtemp(prefix=f"import_{scene_id}_")
    temp_path = os.path.join(temp_dir, f"upload{ext}")
    
    try:
        file_size = 0
        with open(temp_path, "wb") as f:
            chunk = await file.read(UPLOAD_CHUNK_SIZE)
            while chunk:
                f.write(chunk)
                file_size += len(chunk)
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
        
        # Upload to MinIO
        success = minio.upload_file("imports", object_path, temp_path)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "upload_failed",
                    "message": "Failed to upload file to storage. Please check MinIO configuration.",
                }
            )
        
        logger.info(f"Uploaded {file.filename} to imports/{object_path} ({file_size} bytes)")
        
        return object_path, file_size
        
    finally:
        # Cleanup temp file
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp dir: {e}")


async def create_import_scene(
    db,
    organization_id: str,
    user_id: str,
    filename: str,
    file_size: int,
    format_ext: str,
    format_info: dict,
    object_path: str,
) -> tuple[str, str]:
    """
    Create scene and processing job records in MongoDB.
    
    Returns:
        Tuple of (scene_id, job_id)
    """
    scene_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Create scene record
    scene_doc = {
        "_id": scene_id,
        "organization_id": organization_id,
        "created_by": user_id,
        "owner_id": user_id,  # Add owner_id field
        "name": os.path.splitext(filename)[0],
        "description": f"Imported from {filename}",
        "status": SceneStatus.UPLOADING.value if hasattr(SceneStatus, 'UPLOADING') else "uploading",
        "source_type": "import",
        "source_format": format_ext,
        "source_format_type": format_info["type"],
        "original_filename": filename,
        "file_size_bytes": file_size,
        "storage_path": object_path,
        "is_public": False,  # Add is_public field
        "created_at": now,
        "updated_at": now,
        "processing_metrics": {},
    }
    
    await db.scenes.insert_one(scene_doc)
    
    # Create processing job record
    job_doc = {
        "_id": job_id,
        "scene_id": scene_id,
        "organization_id": organization_id,
        "job_type": "import",
        "status": "queued",
        "progress_percent": 0,
        "current_step": "queued",
        "created_at": now,
        "updated_at": now,
        "metadata": {
            "source_format": format_ext,
            "format_type": format_info["type"],
            "parser": format_info["parser"],
        }
    }
    
    await db.processing_jobs.insert_one(job_doc)
    
    logger.info(f"Created import scene {scene_id} and job {job_id}")
    
    return scene_id, job_id


def trigger_import_pipeline(scene_id: str, job_id: str, format_info: dict):
    """Trigger the async import processing pipeline."""
    try:
        from workers.import_pipeline import process_import
        
        # Queue the Celery task
        process_import.delay(
            scene_id=scene_id,
            job_id=job_id,
            parser_type=format_info["parser"],
        )
        
        logger.info(f"Queued import pipeline for scene {scene_id}")
        
    except ImportError:
        logger.warning("Import pipeline worker not available, processing will be deferred")
    except Exception as e:
        logger.error(f"Failed to queue import pipeline: {e}")


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/formats", response_model=SupportedFormatsResponse)
async def list_supported_formats():
    """
    List all supported 3D file formats for import.
    
    Returns format extensions, types, and parser information.
    """
    formats = [
        SupportedFormatInfo(
            extension=ext,
            format_type=ImportFormatType(info["type"]),
            name=info["name"],
            parser=info["parser"],
        )
        for ext, info in SUPPORTED_FORMATS.items()
    ]
    
    return SupportedFormatsResponse(
        formats=formats,
        max_file_size_mb=MAX_FILE_SIZE_MB,
    )


@router.post("/upload", response_model=ImportUploadResponse)
async def upload_3d_file(
    file: UploadFile = File(..., description="3D file to import"),
    name: Optional[str] = Query(None, description="Optional scene name override"),
    current_user: UserInDB = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context),
    db = Depends(get_db),
):
    """
    Upload a 3D file for import into the platform.
    
    Supported formats:
    - **Point Clouds:** PLY, LAS, LAZ, E57
    - **Meshes:** OBJ, GLB, GLTF, STL, FBX, DAE
    - **Gaussian Splatting:** SPLAT
    - **BIM:** IFC
    
    The file will be:
    1. Validated for format and size
    2. Stored in object storage
    3. Queued for async processing
    4. Converted to Gaussian Splatting representation
    5. Optimized and tiled for streaming
    
    Maximum file size: 5GB
    """
    logger.info(f"Import upload request: {file.filename} from user {current_user.id}")
    
    # Validate format
    format_ext, format_info = validate_file_format(file.filename)
    
    # Validate file size (this reads the file once)
    file_size = await validate_file_size(file)
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "empty_file",
                "message": "Uploaded file is empty",
            }
        )
    
    # Save file to storage
    object_path, actual_size = await save_uploaded_file(
        file=file,
        scene_id=str(uuid.uuid4()),  # Generate temp ID for path
        organization_id=tenant.organization_id,
    )
    
    # Extract actual scene_id from path
    scene_id = object_path.split("/")[1]
    
    # Create database records
    scene_id, job_id = await create_import_scene(
        db=db,
        organization_id=tenant.organization_id,
        user_id=str(current_user.id),
        filename=file.filename,
        file_size=actual_size,
        format_ext=format_ext,
        format_info=format_info,
        object_path=object_path,
    )
    
    # Trigger async processing
    trigger_import_pipeline(scene_id, job_id, format_info)
    
    return ImportUploadResponse(
        scene_id=scene_id,
        job_id=job_id,
        filename=file.filename,
        format=format_ext,
        format_type=ImportFormatType(format_info["type"]),
        file_size_bytes=actual_size,
        status=ImportStatus.PENDING,
        message=f"File uploaded successfully. Processing queued.",
    )


@router.get("/status/{job_id}", response_model=ImportStatusResponse)
async def get_import_status(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context),
    db = Depends(get_db),
):
    """
    Get the status of an import processing job.
    
    Returns current progress, step, and any errors.
    """
    job = await db.processing_jobs.find_one({
        "_id": job_id,
        "organization_id": tenant.organization_id,
    })
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": "job_not_found", "message": f"Job {job_id} not found"}
        )
    
    return ImportStatusResponse(
        scene_id=job["scene_id"],
        job_id=job_id,
        status=ImportStatus(job.get("status", "pending")),
        progress_percent=job.get("progress_percent", 0),
        current_step=job.get("current_step"),
        message=job.get("status_message"),
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@router.delete("/{scene_id}")
async def cancel_import(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context),
    db = Depends(get_db),
):
    """
    Cancel an in-progress import and delete the scene.
    
    This will:
    - Cancel any running processing tasks
    - Delete uploaded files from storage
    - Remove database records
    """
    # Find the scene
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": tenant.organization_id,
    })
    
    if not scene:
        raise HTTPException(
            status_code=404,
            detail={"error": "scene_not_found", "message": f"Scene {scene_id} not found"}
        )
    
    # Update job status to cancelled
    await db.processing_jobs.update_many(
        {"scene_id": scene_id},
        {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
    )
    
    # Delete from storage
    try:
        minio = get_minio_client()
        storage_path = scene.get("storage_path", "")
        if storage_path:
            # Delete the directory contents
            org_id = tenant.organization_id
            prefix = f"{org_id}/{scene_id}/"
            objects = minio.list_objects("imports", prefix=prefix, recursive=True)
            for obj in objects:
                minio.remove_object("imports", obj.object_name)
    except Exception as e:
        logger.warning(f"Failed to delete storage for scene {scene_id}: {e}")
    
    # Delete database records
    await db.scenes.delete_one({"_id": scene_id})
    await db.processing_jobs.delete_many({"scene_id": scene_id})
    
    logger.info(f"Cancelled and deleted import scene {scene_id}")
    
    return {"message": f"Import {scene_id} cancelled and deleted"}
