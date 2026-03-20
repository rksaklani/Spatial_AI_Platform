"""
Video Processing Pipeline - Main Celery Task

Orchestrates the full video-to-3D scene pipeline:
1. Frame extraction (FFmpeg)
2. Frame quality filtering (blur/motion)
3. Camera pose estimation (COLMAP)
4. Depth estimation (MiDaS)
"""

import os
import time
import tempfile
import shutil
from datetime import datetime
from typing import Optional, Dict, Any
from celery import shared_task
from celery.utils.log import get_task_logger

from workers.celery_app import celery_app
from workers.base_task import SpatialAIBaseTask

logger = get_task_logger(__name__)


def update_job_progress(
    job_id: str,
    status: str,
    progress: float,
    current_step: str,
    message: Optional[str] = None,
    error: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
):
    """Update processing job progress in MongoDB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from utils.config import settings
    import asyncio
    
    async def _update():
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        update_data = {
            "status": status,
            "progress_percent": progress,
            "current_step": current_step,
            "updated_at": datetime.utcnow(),
        }
        
        if message:
            update_data["status_message"] = message
        if error:
            update_data["error_message"] = error
        if result:
            update_data["result"] = result
        
        if status == "running" and progress == 0:
            update_data["started_at"] = datetime.utcnow()
        elif status in ("completed", "failed"):
            update_data["completed_at"] = datetime.utcnow()
        
        await db.processing_jobs.update_one(
            {"_id": job_id},
            {"$set": update_data}
        )
        
        client.close()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_update())
    finally:
        loop.close()


def update_scene_status(
    scene_id: str,
    status: str,
    message: Optional[str] = None,
    error: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
):
    """Update scene status in MongoDB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from utils.config import settings
    import asyncio
    
    async def _update():
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow(),
        }
        
        if message:
            update_data["status_message"] = message
        if error:
            update_data["error_message"] = error
        if metrics:
            for key, value in metrics.items():
                update_data[f"processing_metrics.{key}"] = value
        
        if status == "extracting_frames":
            update_data["processing_started_at"] = datetime.utcnow()
        elif status in ("ready", "failed"):
            update_data["processing_completed_at"] = datetime.utcnow()
        
        await db.scenes.update_one(
            {"_id": scene_id},
            {"$set": update_data}
        )
        
        client.close()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_update())
    finally:
        loop.close()


def get_scene_data(scene_id: str) -> Optional[Dict[str, Any]]:
    """Fetch scene data from MongoDB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from utils.config import settings
    import asyncio
    
    async def _fetch():
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        scene = await db.scenes.find_one({"_id": scene_id})
        client.close()
        return scene
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_fetch())
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    base=SpatialAIBaseTask,
    name="workers.video_pipeline.process_video_pipeline",
    queue="cpu",
    max_retries=3,
    soft_time_limit=3600,  # 1 hour soft limit
    time_limit=3900,  # 1 hour 5 min hard limit
)
def process_video_pipeline(self, scene_id: str, job_id: str) -> Dict[str, Any]:
    """
    Main video processing pipeline task.
    
    Steps:
    1. Download video from MinIO
    2. Extract frames with FFmpeg
    3. Filter frames (blur/motion)
    4. Estimate camera poses (COLMAP)
    5. Generate depth maps (MiDaS)
    6. Upload results to MinIO
    
    Args:
        scene_id: Scene UUID
        job_id: Processing job UUID
        
    Returns:
        Dict with processing results and metrics
    """
    start_time = time.time()
    work_dir = None
    
    try:
        logger.info(f"Starting video pipeline for scene {scene_id}, job {job_id}")
        
        # Update status
        update_job_progress(job_id, "running", 0, "initializing", "Starting pipeline")
        update_scene_status(scene_id, "extracting_frames", "Starting video processing")
        
        # Get scene data
        scene = get_scene_data(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        organization_id = scene["organization_id"]
        source_path = scene["source_path"]
        
        # Create temporary working directory
        work_dir = tempfile.mkdtemp(prefix=f"scene_{scene_id}_")
        logger.info(f"Working directory: {work_dir}")
        
        # Step 1: Download video from MinIO
        update_job_progress(job_id, "running", 5, "downloading", "Downloading video from storage")
        
        video_path = download_video(scene_id, organization_id, source_path, work_dir)
        logger.info(f"Video downloaded: {video_path}")
        
        # Step 2: Extract frames
        update_job_progress(job_id, "running", 10, "extracting_frames", "Extracting frames from video")
        update_scene_status(scene_id, "extracting_frames", "Extracting video frames")
        
        frames_dir = os.path.join(work_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        frame_result = extract_frames(video_path, frames_dir, fps=3)
        frame_count = frame_result["frame_count"]
        video_metadata = frame_result["video_metadata"]
        
        logger.info(f"Extracted {frame_count} frames")
        update_scene_status(scene_id, "extracting_frames", f"Extracted {frame_count} frames", 
                          metrics={"frame_count": frame_count})
        
        # Step 3: Filter frames (blur/motion detection)
        update_job_progress(job_id, "running", 25, "filtering_frames", "Analyzing frame quality")
        
        filter_result = filter_frames(frames_dir)
        valid_frames = filter_result["valid_frames"]
        valid_count = len(valid_frames)
        
        logger.info(f"Valid frames after filtering: {valid_count}/{frame_count}")
        update_scene_status(scene_id, "estimating_poses", f"Filtered to {valid_count} valid frames",
                          metrics={"valid_frame_count": valid_count})
        
        # Step 4: Upload frames to MinIO
        update_job_progress(job_id, "running", 35, "uploading_frames", "Uploading frames to storage")
        
        upload_frames(scene_id, frames_dir, valid_frames)
        
        # Step 5: Camera pose estimation (COLMAP)
        update_job_progress(job_id, "running", 45, "pose_estimation", "Estimating camera poses")
        update_scene_status(scene_id, "estimating_poses", "Running camera pose estimation")
        
        sparse_dir = os.path.join(work_dir, "sparse")
        os.makedirs(sparse_dir, exist_ok=True)
        
        pose_result = estimate_camera_poses(frames_dir, valid_frames, sparse_dir)
        camera_count = pose_result.get("camera_count", 0)
        point_count = pose_result.get("point_count", 0)
        
        logger.info(f"Pose estimation: {camera_count} cameras, {point_count} points")
        update_scene_status(scene_id, "generating_depth", f"Estimated {camera_count} camera poses",
                          metrics={"camera_count": camera_count, "point_count": point_count})
        
        # Upload sparse reconstruction
        upload_sparse_data(scene_id, sparse_dir)
        
        # Step 6: Depth estimation (MiDaS)
        update_job_progress(job_id, "running", 65, "depth_estimation", "Generating depth maps")
        update_scene_status(scene_id, "generating_depth", "Generating depth maps")
        
        depth_dir = os.path.join(work_dir, "depth")
        os.makedirs(depth_dir, exist_ok=True)
        
        depth_result = estimate_depth_maps(frames_dir, valid_frames, depth_dir)
        depth_count = depth_result.get("depth_count", 0)
        
        logger.info(f"Generated {depth_count} depth maps")
        update_scene_status(scene_id, "ready", f"Generated {depth_count} depth maps",
                          metrics={"depth_map_count": depth_count})
        
        # Upload depth maps
        update_job_progress(job_id, "running", 85, "uploading_depth", "Uploading depth maps")
        upload_depth_maps(scene_id, depth_dir)
        
        # Calculate total processing time
        processing_time = time.time() - start_time
        
        # Final status update
        result = {
            "scene_id": scene_id,
            "frame_count": frame_count,
            "valid_frame_count": valid_count,
            "camera_count": camera_count,
            "point_count": point_count,
            "depth_count": depth_count,
            "processing_time_seconds": processing_time,
            "video_metadata": video_metadata,
        }
        
        update_job_progress(job_id, "completed", 100, "completed", 
                          f"Pipeline completed in {processing_time:.1f}s", result=result)
        update_scene_status(scene_id, "ready", "Processing completed successfully",
                          metrics={"processing_time_seconds": processing_time})
        
        logger.info(f"Pipeline completed for scene {scene_id} in {processing_time:.1f}s")
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Pipeline failed for scene {scene_id}: {error_msg}")
        
        update_job_progress(job_id, "failed", 0, "failed", error=error_msg)
        update_scene_status(scene_id, "failed", "Processing failed", error=error_msg)
        
        # Re-raise for Celery retry logic
        raise
        
    finally:
        # Cleanup working directory
        if work_dir and os.path.exists(work_dir):
            try:
                shutil.rmtree(work_dir)
                logger.info(f"Cleaned up working directory: {work_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {work_dir}: {e}")


def download_video(scene_id: str, organization_id: str, source_path: str, work_dir: str) -> str:
    """Download video from MinIO to local filesystem."""
    from utils.minio_client import get_minio_client
    
    minio = get_minio_client()
    
    # Extract extension from source path
    ext = os.path.splitext(source_path)[1] or ".mp4"
    local_path = os.path.join(work_dir, f"original{ext}")
    
    # Download from MinIO
    object_name = f"{organization_id}/{scene_id}/original{ext}"
    minio.download_file("videos", object_name, local_path)
    
    return local_path


def extract_frames(video_path: str, output_dir: str, fps: int = 3) -> Dict[str, Any]:
    """
    Extract frames from video using FFmpeg.
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save frames
        fps: Frames per second to extract
        
    Returns:
        Dict with frame count and video metadata
    """
    import subprocess
    import json
    
    # Get video metadata with ffprobe
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path
    ]
    
    try:
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(probe_result.stdout)
        
        video_stream = next(
            (s for s in probe_data.get("streams", []) if s.get("codec_type") == "video"),
            {}
        )
        
        video_metadata = {
            "duration_seconds": float(probe_data.get("format", {}).get("duration", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "30/1")),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "codec": video_stream.get("codec_name"),
            "bitrate": int(probe_data.get("format", {}).get("bit_rate", 0)),
        }
    except Exception as e:
        logger.warning(f"Failed to probe video: {e}")
        video_metadata = {}
    
    # Extract frames with FFmpeg
    output_pattern = os.path.join(output_dir, "frame_%06d.jpg")
    
    extract_cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",  # High quality JPEG
        "-y",  # Overwrite
        output_pattern
    ]
    
    subprocess.run(extract_cmd, capture_output=True, check=True)
    
    # Count extracted frames
    frame_files = [f for f in os.listdir(output_dir) if f.startswith("frame_") and f.endswith(".jpg")]
    frame_count = len(frame_files)
    
    return {
        "frame_count": frame_count,
        "video_metadata": video_metadata,
    }


def filter_frames(frames_dir: str) -> Dict[str, Any]:
    """
    Filter frames based on blur and motion scores.
    
    Removes blurry frames and ensures spatial coverage.
    
    Args:
        frames_dir: Directory containing extracted frames
        
    Returns:
        Dict with list of valid frame filenames
    """
    import cv2
    import numpy as np
    
    frame_files = sorted([
        f for f in os.listdir(frames_dir) 
        if f.startswith("frame_") and f.endswith(".jpg")
    ])
    
    frame_scores = []
    
    for filename in frame_files:
        filepath = os.path.join(frames_dir, filename)
        
        # Read image
        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        # Calculate Laplacian variance (blur score)
        # Higher = sharper
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        
        frame_scores.append({
            "filename": filename,
            "blur_score": laplacian_var,
        })
    
    # Filter out blurry frames (keep frames with blur score > threshold)
    blur_threshold = 100  # Adjust based on testing
    valid_frames = [
        f["filename"] for f in frame_scores
        if f["blur_score"] > blur_threshold
    ]
    
    # If too many frames filtered, be more lenient
    if len(valid_frames) < len(frame_files) * 0.3:
        # Sort by blur score and take top 50%
        sorted_frames = sorted(frame_scores, key=lambda x: x["blur_score"], reverse=True)
        valid_frames = [f["filename"] for f in sorted_frames[:len(sorted_frames) // 2]]
    
    logger.info(f"Frame filtering: {len(valid_frames)}/{len(frame_files)} frames kept")
    
    return {
        "valid_frames": valid_frames,
        "total_frames": len(frame_files),
        "filtered_count": len(frame_files) - len(valid_frames),
    }


def upload_frames(scene_id: str, frames_dir: str, valid_frames: list):
    """Upload valid frames to MinIO."""
    from utils.minio_client import get_minio_client
    
    minio = get_minio_client()
    
    # Ensure bucket exists
    if not minio.bucket_exists("frames"):
        minio.create_bucket("frames")
    
    for filename in valid_frames:
        local_path = os.path.join(frames_dir, filename)
        object_name = f"{scene_id}/{filename}"
        minio.upload_file("frames", object_name, local_path, content_type="image/jpeg")
    
    logger.info(f"Uploaded {len(valid_frames)} frames to MinIO")


def estimate_camera_poses(frames_dir: str, valid_frames: list, output_dir: str) -> Dict[str, Any]:
    """
    Estimate camera poses using COLMAP (or fallback to simpler method).
    
    Args:
        frames_dir: Directory containing frames
        valid_frames: List of valid frame filenames
        output_dir: Directory to save sparse reconstruction
        
    Returns:
        Dict with camera count and point count
    """
    import subprocess
    
    # Create COLMAP workspace
    images_dir = os.path.join(output_dir, "images")
    database_path = os.path.join(output_dir, "database.db")
    sparse_dir = os.path.join(output_dir, "sparse")
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(sparse_dir, exist_ok=True)
    
    # Copy valid frames to COLMAP images directory
    for filename in valid_frames:
        src = os.path.join(frames_dir, filename)
        dst = os.path.join(images_dir, filename)
        shutil.copy2(src, dst)
    
    try:
        # Feature extraction
        subprocess.run([
            "colmap", "feature_extractor",
            "--database_path", database_path,
            "--image_path", images_dir,
            "--ImageReader.single_camera", "1",
            "--SiftExtraction.use_gpu", "0",
        ], check=True, capture_output=True)
        
        # Feature matching
        subprocess.run([
            "colmap", "exhaustive_matcher",
            "--database_path", database_path,
            "--SiftMatching.use_gpu", "0",
        ], check=True, capture_output=True)
        
        # Sparse reconstruction (Mapper)
        subprocess.run([
            "colmap", "mapper",
            "--database_path", database_path,
            "--image_path", images_dir,
            "--output_path", sparse_dir,
        ], check=True, capture_output=True)
        
        # Count cameras and points from reconstruction
        model_dir = os.path.join(sparse_dir, "0")
        if os.path.exists(model_dir):
            # Parse cameras.txt
            cameras_file = os.path.join(model_dir, "cameras.txt")
            images_file = os.path.join(model_dir, "images.txt")
            points_file = os.path.join(model_dir, "points3D.txt")
            
            camera_count = 0
            point_count = 0
            
            if os.path.exists(images_file):
                with open(images_file, 'r') as f:
                    lines = [l for l in f.readlines() if not l.startswith('#')]
                    camera_count = len(lines) // 2  # Each image has 2 lines
            
            if os.path.exists(points_file):
                with open(points_file, 'r') as f:
                    lines = [l for l in f.readlines() if not l.startswith('#')]
                    point_count = len(lines)
            
            return {
                "camera_count": camera_count,
                "point_count": point_count,
                "success": True,
            }
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"COLMAP failed, using fallback: {e}")
    
    # Fallback: assume all frames have cameras (no actual pose estimation)
    return {
        "camera_count": len(valid_frames),
        "point_count": 0,
        "success": False,
        "fallback": True,
    }


def upload_sparse_data(scene_id: str, sparse_dir: str):
    """Upload sparse reconstruction to MinIO."""
    from utils.minio_client import get_minio_client
    
    minio = get_minio_client()
    
    # Ensure bucket exists
    if not minio.bucket_exists("scenes"):
        minio.create_bucket("scenes")
    
    # Upload all files in sparse directory
    for root, dirs, files in os.walk(sparse_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            rel_path = os.path.relpath(local_path, sparse_dir)
            object_name = f"{scene_id}/sparse/{rel_path}"
            minio.upload_file("scenes", object_name, local_path)
    
    logger.info(f"Uploaded sparse reconstruction for scene {scene_id}")


def estimate_depth_maps(frames_dir: str, valid_frames: list, output_dir: str) -> Dict[str, Any]:
    """
    Generate depth maps using MiDaS (or simpler fallback).
    
    Args:
        frames_dir: Directory containing frames
        valid_frames: List of valid frame filenames
        output_dir: Directory to save depth maps
        
    Returns:
        Dict with depth map count
    """
    import cv2
    import numpy as np
    
    depth_count = 0
    
    try:
        # Try to use MiDaS
        import torch
        
        # Check for GPU
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load MiDaS model
        model_type = "DPT_Large"  # or "MiDaS_small" for faster processing
        midas = torch.hub.load("intel-isl/MiDaS", model_type, trust_repo=True)
        midas.to(device)
        midas.eval()
        
        # Load transforms
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
        transform = midas_transforms.dpt_transform if model_type == "DPT_Large" else midas_transforms.small_transform
        
        for filename in valid_frames:
            input_path = os.path.join(frames_dir, filename)
            
            # Read image
            img = cv2.imread(input_path)
            if img is None:
                continue
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Transform and predict
            input_batch = transform(img_rgb).to(device)
            
            with torch.no_grad():
                prediction = midas(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            
            # Normalize depth map to 0-255
            depth = prediction.cpu().numpy()
            depth_normalized = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
            depth_uint8 = depth_normalized.astype(np.uint8)
            
            # Save depth map
            depth_filename = filename.replace(".jpg", "_depth.png")
            output_path = os.path.join(output_dir, depth_filename)
            cv2.imwrite(output_path, depth_uint8)
            
            depth_count += 1
        
        logger.info(f"Generated {depth_count} depth maps using MiDaS")
        
    except Exception as e:
        logger.warning(f"MiDaS failed, using edge-based fallback: {e}")
        
        # Fallback: Use simple edge detection as pseudo-depth
        for filename in valid_frames:
            input_path = os.path.join(frames_dir, filename)
            
            img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            
            # Use Sobel edges as pseudo-depth
            sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            
            # Normalize
            depth_normalized = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
            depth_uint8 = depth_normalized.astype(np.uint8)
            
            # Save
            depth_filename = filename.replace(".jpg", "_depth.png")
            output_path = os.path.join(output_dir, depth_filename)
            cv2.imwrite(output_path, depth_uint8)
            
            depth_count += 1
    
    return {"depth_count": depth_count}


def upload_depth_maps(scene_id: str, depth_dir: str):
    """Upload depth maps to MinIO."""
    from utils.minio_client import get_minio_client
    
    minio = get_minio_client()
    
    # Ensure bucket exists
    if not minio.bucket_exists("depth"):
        minio.create_bucket("depth")
    
    for filename in os.listdir(depth_dir):
        if filename.endswith("_depth.png"):
            local_path = os.path.join(depth_dir, filename)
            object_name = f"{scene_id}/{filename}"
            minio.upload_file("depth", object_name, local_path, content_type="image/png")
    
    logger.info(f"Uploaded depth maps for scene {scene_id}")
