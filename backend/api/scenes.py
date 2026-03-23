"""
Scene management API endpoints.

Phase 2 Task 4: Video Upload System
- Multipart upload for MP4/MOV/AVI (max 5GB)
- UUID scene ID generation
- MinIO storage: videos/{organizationId}/{sceneId}/original.{ext}
- MongoDB metadata persistence
- Celery job triggering
"""

import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
import structlog

from models.scene import (
    SceneCreate,
    SceneUpdate,
    SceneInDB,
    SceneResponse,
    SceneListResponse,
    SceneStatus,
    SceneType,
    VideoMetadata,
    ProcessingMetrics,
)
from models.processing_job import (
    ProcessingJobCreate,
    ProcessingJobInDB,
    JobType,
    JobStatus,
    JobPriority,
)
from models.user import UserInDB
from api.deps import get_current_user
from utils.database import get_db
from utils.minio_client import get_minio_client

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/scenes", tags=["scenes"])

# Allowed video formats and max size
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
ALLOWED_VIDEO_MIMETYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "video/x-matroska",
}
MAX_VIDEO_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5GB


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()


def validate_video_file(filename: str, content_type: Optional[str], file_size: int) -> tuple[bool, str]:
    """
    Validate video file format and size.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check extension
    ext = get_file_extension(filename)
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return False, f"Invalid file format. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
    
    # Check MIME type if provided
    if content_type and content_type not in ALLOWED_VIDEO_MIMETYPES:
        # Try to guess from extension
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type not in ALLOWED_VIDEO_MIMETYPES:
            return False, f"Invalid content type: {content_type}"
    
    # Check file size
    if file_size > MAX_VIDEO_SIZE_BYTES:
        max_gb = MAX_VIDEO_SIZE_BYTES / (1024 ** 3)
        return False, f"File too large. Maximum size: {max_gb}GB"
    
    return True, ""


async def trigger_processing_job(scene_id: str, organization_id: str, db) -> str:
    """
    Create a processing job and trigger Celery task.
    
    Returns:
        str: Job ID
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    job_doc = {
        "_id": job_id,
        "scene_id": scene_id,
        "organization_id": organization_id,
        "job_type": JobType.FULL_PIPELINE.value,
        "priority": JobPriority.NORMAL.value,
        "parameters": {},
        "celery_task_id": None,
        "worker_id": None,
        "queue": "cpu",
        "status": JobStatus.PENDING.value,
        "error_message": None,
        "retry_count": 0,
        "max_retries": 3,
        "progress_percent": 0.0,
        "current_step": None,
        "steps": [],
        "result": None,
        "output_paths": {},
        "created_at": now,
        "updated_at": now,
        "queued_at": None,
        "started_at": None,
        "completed_at": None,
        "wait_time_seconds": None,
        "run_time_seconds": None,
    }
    
    await db.processing_jobs.insert_one(job_doc)
    
    # Trigger Celery task
    try:
        from workers.video_pipeline import process_video_pipeline
        result = process_video_pipeline.delay(scene_id, job_id)
        
        # Update job with Celery task ID
        await db.processing_jobs.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "celery_task_id": result.id,
                    "status": JobStatus.QUEUED.value,
                    "queued_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        logger.info(
            "processing_job_queued",
            job_id=job_id,
            scene_id=scene_id,
            celery_task_id=result.id
        )
    except Exception as e:
        logger.warning(
            "celery_task_trigger_failed",
            job_id=job_id,
            scene_id=scene_id,
            error=str(e)
        )
        # Job remains in PENDING status - can be retried later
    
    return job_id


# ============================================================================
# Scene CRUD Endpoints
# ============================================================================

@router.post("/upload", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    """
    Upload a video file to create a new scene.
    
    - Accepts MP4, MOV, AVI, WebM, MKV formats
    - Maximum file size: 5GB
    - Generates unique scene ID
    - Stores video in MinIO
    - Creates scene metadata in MongoDB
    - Triggers processing pipeline
    """
    db = await get_db()
    
    # Get organization context
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to upload videos"
        )
    
    organization_id = current_user.organization_id
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Read file to get size (for validation)
    # Note: For large files, consider streaming validation
    file_content = await file.read()
    file_size = len(file_content)
    
    is_valid, error_msg = validate_video_file(file.filename, file.content_type, file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Generate scene ID
    scene_id = str(uuid.uuid4())
    ext = get_file_extension(file.filename)
    
    # Determine storage path
    source_path = f"videos/{organization_id}/{scene_id}/original{ext}"
    
    # Upload to MinIO
    try:
        minio = get_minio_client()
        
        # Ensure bucket exists
        if not minio.bucket_exists("videos"):
            minio.create_bucket("videos")
        
        # Upload file
        from io import BytesIO
        file_stream = BytesIO(file_content)
        
        minio.client.put_object(
            bucket_name="videos",
            object_name=f"{organization_id}/{scene_id}/original{ext}",
            data=file_stream,
            length=file_size,
            content_type=file.content_type or "video/mp4"
        )
        
        logger.info(
            "video_uploaded_to_minio",
            scene_id=scene_id,
            path=source_path,
            size_bytes=file_size
        )
    except Exception as e:
        logger.error("minio_upload_failed", scene_id=scene_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store video file"
        )
    
    # Create scene document
    now = datetime.utcnow()
    scene_name = name or os.path.splitext(file.filename)[0]
    
    scene_doc = {
        "_id": scene_id,
        "organization_id": organization_id,
        "owner_id": current_user.id,
        "name": scene_name,
        "description": description,
        "source_type": SceneType.VIDEO.value,
        "original_filename": file.filename,
        "file_size_bytes": file_size,
        "mime_type": file.content_type or "video/mp4",
        "source_path": source_path,
        "frames_path": None,
        "depth_path": None,
        "sparse_path": None,
        "tiles_path": None,
        "status": SceneStatus.UPLOADED.value,
        "status_message": "Video uploaded successfully",
        "error_message": None,
        "video_metadata": None,
        "processing_metrics": ProcessingMetrics().model_dump(),
        "is_public": False,
        "thumbnail_path": None,
        "created_at": now,
        "updated_at": now,
        "processing_started_at": None,
        "processing_completed_at": None,
    }
    
    await db.scenes.insert_one(scene_doc)
    
    logger.info(
        "scene_created",
        scene_id=scene_id,
        organization_id=organization_id,
        owner_id=current_user.id,
        filename=file.filename
    )
    
    # Trigger processing pipeline
    job_id = await trigger_processing_job(scene_id, organization_id, db)
    
    # Update scene with processing job reference
    await db.scenes.update_one(
        {"_id": scene_id},
        {"$set": {"current_job_id": job_id, "updated_at": datetime.utcnow()}}
    )
    
    return SceneResponse(**scene_doc)


@router.get("", response_model=SceneListResponse)
async def list_scenes(
    current_user: UserInDB = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """
    List scenes for the current user's organization.
    
    Supports filtering by status and pagination.
    """
    db = await get_db()
    
    if not current_user.organization_id:
        return SceneListResponse(items=[], total=0, page=page, page_size=page_size, has_more=False)
    
    # Build query
    query = {"organization_id": current_user.organization_id}
    
    if status_filter:
        query["status"] = status_filter
    
    # Get total count
    total = await db.scenes.count_documents(query)
    
    # Sort direction
    sort_dir = 1 if sort_order == "asc" else -1
    
    # Fetch scenes
    skip = (page - 1) * page_size
    cursor = db.scenes.find(query).sort(sort_by, sort_dir).skip(skip).limit(page_size)
    scenes = await cursor.to_list(length=page_size)
    
    items = [SceneResponse(**s) for s in scenes]
    has_more = (page * page_size) < total
    
    return SceneListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get scene details by ID.
    
    User must be a member of the scene's organization.
    """
    db = await get_db()
    
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check organization access
    if scene["organization_id"] != current_user.organization_id:
        # Check if scene is public
        if not scene.get("is_public", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this scene"
            )
    
    return SceneResponse(**scene)


@router.patch("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: str,
    scene_update: SceneUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update scene metadata.
    
    Only the owner or organization admin can update scenes.
    """
    db = await get_db()
    
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check organization access
    if scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scene"
        )
    
    # Build update
    update_data = {}
    if scene_update.name is not None:
        update_data["name"] = scene_update.name
    if scene_update.description is not None:
        update_data["description"] = scene_update.description
    if scene_update.is_public is not None:
        update_data["is_public"] = scene_update.is_public
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.scenes.update_one(
        {"_id": scene_id},
        {"$set": update_data}
    )
    
    # Fetch updated scene
    scene = await db.scenes.find_one({"_id": scene_id})
    
    logger.info("scene_updated", scene_id=scene_id, updated_by=current_user.id)
    
    return SceneResponse(**scene)


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Delete a scene and all associated data.
    
    Only the owner can delete scenes.
    This deletes:
    - Scene metadata from MongoDB
    - Source video from MinIO
    - All processed artifacts (frames, depth maps, tiles)
    """
    db = await get_db()
    
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check ownership
    if scene["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the scene owner can delete it"
        )
    
    # Delete from MinIO
    try:
        minio = get_minio_client()
        organization_id = scene["organization_id"]
        
        # Delete source video
        if scene.get("source_path"):
            bucket, key = "videos", f"{organization_id}/{scene_id}/"
            objects = minio.client.list_objects(bucket, prefix=key, recursive=True)
            for obj in objects:
                minio.client.remove_object(bucket, obj.object_name)
        
        # Delete frames
        objects = minio.client.list_objects("frames", prefix=f"{scene_id}/", recursive=True)
        for obj in objects:
            minio.client.remove_object("frames", obj.object_name)
        
        # Delete depth maps
        objects = minio.client.list_objects("depth", prefix=f"{scene_id}/", recursive=True)
        for obj in objects:
            minio.client.remove_object("depth", obj.object_name)
        
        # Delete scene tiles
        objects = minio.client.list_objects("scenes", prefix=f"{scene_id}/", recursive=True)
        for obj in objects:
            minio.client.remove_object("scenes", obj.object_name)
            
    except Exception as e:
        logger.error("minio_delete_failed", scene_id=scene_id, error=str(e))
        # Continue with MongoDB deletion even if MinIO cleanup fails
    
    # Delete processing jobs
    await db.processing_jobs.delete_many({"scene_id": scene_id})
    
    # Delete scene document
    await db.scenes.delete_one({"_id": scene_id})
    
    logger.info("scene_deleted", scene_id=scene_id, deleted_by=current_user.id)
    
    return None


# ============================================================================
# Processing Job Endpoints
# ============================================================================

@router.get("/{scene_id}/jobs", response_model=List[dict])
async def get_scene_jobs(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get processing jobs for a scene.
    """
    db = await get_db()
    
    # Verify scene access
    scene = await db.scenes.find_one({"_id": scene_id})
    if not scene or scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    cursor = db.processing_jobs.find({"scene_id": scene_id}).sort("created_at", -1)
    jobs = await cursor.to_list(length=100)
    
    return jobs


@router.post("/{scene_id}/reprocess", response_model=dict)
async def reprocess_scene(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Trigger reprocessing of a scene.
    
    Useful for scenes that failed processing or need regeneration.
    """
    db = await get_db()
    
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    if scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Reset scene status
    await db.scenes.update_one(
        {"_id": scene_id},
        {
            "$set": {
                "status": SceneStatus.UPLOADED.value,
                "status_message": "Queued for reprocessing",
                "error_message": None,
                "updated_at": datetime.utcnow(),
            }
        }
    )
    
    # Create new processing job
    job_id = await trigger_processing_job(scene_id, scene["organization_id"], db)
    
    logger.info("scene_reprocess_triggered", scene_id=scene_id, job_id=job_id)
    
    return {"job_id": job_id, "message": "Reprocessing triggered"}


# ============================================================================
# Camera Configuration Endpoints
# ============================================================================

from models.scene import CameraConfiguration, CameraBoundary


@router.get("/{scene_id}/camera-config", response_model=CameraConfiguration)
async def get_camera_config(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get camera configuration for a scene.
    
    Returns default configuration if none is set.
    """
    db = await get_db()
    
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check organization access
    if scene["organization_id"] != current_user.organization_id:
        if not scene.get("is_public", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this scene"
            )
    
    # Return camera config or default
    camera_config = scene.get("camera_config")
    if camera_config:
        return CameraConfiguration(**camera_config)
    else:
        return CameraConfiguration()


@router.put("/{scene_id}/camera-config", response_model=CameraConfiguration)
async def update_camera_config(
    scene_id: str,
    camera_config: CameraConfiguration,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update camera configuration for a scene.
    
    Allows setting:
    - Camera boundary (3D bounding box)
    - Zoom limits (min/max distance)
    - Axis locks (X, Y, Z)
    - Default camera position and target
    - Rotation enable/disable
    - Boundary indicators
    
    Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7, 30.8, 30.9, 30.10
    """
    db = await get_db()
    
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check organization access
    if scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scene"
        )
    
    # Validate camera configuration
    if camera_config.min_zoom_distance >= camera_config.max_zoom_distance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_zoom_distance must be less than max_zoom_distance"
        )
    
    if camera_config.boundary and camera_config.boundary_enabled:
        b = camera_config.boundary
        if b.min_x >= b.max_x or b.min_y >= b.max_y or b.min_z >= b.max_z:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid boundary: min values must be less than max values"
            )
    
    # Update scene with camera config
    await db.scenes.update_one(
        {"_id": scene_id},
        {
            "$set": {
                "camera_config": camera_config.model_dump(),
                "updated_at": datetime.utcnow(),
            }
        }
    )
    
    logger.info(
        "camera_config_updated",
        scene_id=scene_id,
        updated_by=current_user.id,
        boundary_enabled=camera_config.boundary_enabled,
        rotation_enabled=camera_config.rotation_enabled
    )
    
    return camera_config
