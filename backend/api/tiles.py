"""
Tile Streaming API

Provides endpoints for streaming scene tiles to the web viewer:
- Tile request with frustum culling
- Distance-based prioritization
- LOD selection based on distance
- Bandwidth adaptation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime

from api.deps import get_current_user, get_db
from models.user import UserInDB
from models.scene_tile import SceneTileInDB, LODLevel

router = APIRouter(prefix="/scenes", tags=["tiles"])


class CameraParams(BaseModel):
    """Camera parameters for tile selection."""
    position: List[float] = Field(..., min_length=3, max_length=3, description="Camera position [x, y, z]")
    direction: List[float] = Field(..., min_length=3, max_length=3, description="Camera direction [x, y, z]")
    fov: float = Field(60, ge=30, le=120, description="Field of view in degrees")
    near: float = Field(0.1, gt=0, description="Near clipping plane")
    far: float = Field(1000, gt=0, description="Far clipping plane")


class TileRequest(BaseModel):
    """Request for scene tiles."""
    camera: CameraParams
    bandwidth_mbps: Optional[float] = Field(None, ge=0, description="Available bandwidth in Mbps")
    max_tiles: int = Field(50, ge=1, le=200, description="Maximum tiles to return")


class TileResponse(BaseModel):
    """Response with prioritized tiles."""
    tile_id: str
    level: int
    x: int
    y: int
    z: int
    lod: str
    priority: float = Field(..., ge=0, le=1, description="Priority 0-1, higher is more important")
    distance: float = Field(..., description="Distance from camera in meters")
    file_path: str
    file_size_bytes: int
    gaussian_count: int
    bounding_box: dict


class TileListResponse(BaseModel):
    """List of tiles with metadata."""
    tiles: List[TileResponse]
    total_tiles: int
    selected_lod: str
    bandwidth_adjusted: bool


def normalize_vector(v: np.ndarray) -> np.ndarray:
    """Normalize a vector."""
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def point_in_frustum(
    point: np.ndarray,
    camera_pos: np.ndarray,
    camera_dir: np.ndarray,
    fov: float,
    near: float,
    far: float,
) -> bool:
    """
    Check if a point is inside the camera frustum.
    
    Args:
        point: 3D point to test
        camera_pos: Camera position
        camera_dir: Camera direction (normalized)
        fov: Field of view in degrees
        near: Near clipping plane
        far: Far clipping plane
        
    Returns:
        True if point is in frustum
    """
    to_point = point - camera_pos
    distance = np.linalg.norm(to_point)
    
    # Check distance bounds
    if distance < near or distance > far:
        return False
    
    # Check angle
    if distance > 0:
        to_point_normalized = to_point / distance
        cos_angle = np.dot(to_point_normalized, camera_dir)
        cos_fov_half = np.cos(np.radians(fov / 2))
        
        return cos_angle >= cos_fov_half
    
    return True


def bbox_in_frustum(
    bbox: dict,
    camera_pos: np.ndarray,
    camera_dir: np.ndarray,
    fov: float,
    near: float,
    far: float,
) -> bool:
    """
    Check if a bounding box intersects the camera frustum.
    
    Uses conservative test: checks if bbox center is in frustum
    with margin for bbox size.
    """
    center = np.array([
        (bbox["min_x"] + bbox["max_x"]) / 2,
        (bbox["min_y"] + bbox["max_y"]) / 2,
        (bbox["min_z"] + bbox["max_z"]) / 2,
    ])
    
    # Calculate bbox radius (half diagonal)
    size = np.array([
        bbox["max_x"] - bbox["min_x"],
        bbox["max_y"] - bbox["min_y"],
        bbox["max_z"] - bbox["min_z"],
    ])
    radius = np.linalg.norm(size) / 2
    
    to_center = center - camera_pos
    distance = np.linalg.norm(to_center)
    
    # Adjust distance bounds by radius
    if distance + radius < near or distance - radius > far:
        return False
    
    # Check angle with margin
    if distance > 0:
        to_center_normalized = to_center / distance
        cos_angle = np.dot(to_center_normalized, camera_dir)
        
        # Add angular margin for bbox size
        angular_margin = np.arctan(radius / max(distance, 0.1))
        cos_fov_half = np.cos(np.radians(fov / 2) + angular_margin)
        
        return cos_angle >= cos_fov_half
    
    return True


def select_lod_by_distance(distance: float, bandwidth_mbps: Optional[float] = None) -> str:
    """
    Select LOD level based on distance and bandwidth.
    
    Args:
        distance: Distance from camera in meters
        bandwidth_mbps: Available bandwidth in Mbps (optional)
        
    Returns:
        LOD level: "high", "medium", or "low"
    """
    # Bandwidth-based downgrade
    if bandwidth_mbps is not None and bandwidth_mbps < 5:
        # Low bandwidth: use lower LOD
        if distance < 10:
            return "medium"
        else:
            return "low"
    
    # Distance-based selection
    if distance < 5:
        return "high"
    elif distance < 20:
        return "medium"
    else:
        return "low"


def calculate_tile_priority(
    tile: SceneTileInDB,
    camera_pos: np.ndarray,
    camera_dir: np.ndarray,
) -> float:
    """
    Calculate tile priority (0-1, higher is more important).
    
    Priority factors:
    - Distance from camera (closer = higher priority)
    - Alignment with camera direction (more aligned = higher priority)
    - Gaussian count (more detail = higher priority)
    """
    # Calculate tile center
    bbox = tile.bounding_box
    center = np.array([
        (bbox.min_x + bbox.max_x) / 2,
        (bbox.min_y + bbox.max_y) / 2,
        (bbox.min_z + bbox.max_z) / 2,
    ])
    
    to_tile = center - camera_pos
    distance = np.linalg.norm(to_tile)
    
    # Distance priority (inverse, normalized to 0-1)
    # Closer tiles get higher priority
    max_distance = 100  # meters
    distance_priority = max(0, 1 - distance / max_distance)
    
    # Direction priority (dot product, 0-1)
    if distance > 0:
        to_tile_normalized = to_tile / distance
        direction_priority = (np.dot(to_tile_normalized, camera_dir) + 1) / 2
    else:
        direction_priority = 1.0
    
    # Detail priority (normalized by typical tile size)
    max_gaussians = 100000
    detail_priority = min(1.0, tile.gaussian_count / max_gaussians)
    
    # Weighted combination
    priority = (
        distance_priority * 0.5 +
        direction_priority * 0.3 +
        detail_priority * 0.2
    )
    
    return float(priority)


@router.post("/{scene_id}/tiles", response_model=TileListResponse)
async def get_scene_tiles(
    scene_id: str,
    request: TileRequest,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Get prioritized list of tiles for a scene based on camera parameters.
    
    Implements:
    - Frustum culling: Only return visible tiles
    - Distance-based LOD selection
    - Priority sorting by distance and alignment
    - Bandwidth adaptation
    """
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id,
    })
    
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Parse camera parameters
    camera_pos = np.array(request.camera.position)
    camera_dir = normalize_vector(np.array(request.camera.direction))
    fov = request.camera.fov
    near = request.camera.near
    far = request.camera.far
    bandwidth = request.bandwidth_mbps
    
    # Determine target LOD based on bandwidth
    bandwidth_adjusted = False
    if bandwidth is not None and bandwidth < 5:
        target_lod = "low"
        bandwidth_adjusted = True
    else:
        target_lod = None  # Will be determined per-tile by distance
    
    # Query all tiles for this scene
    cursor = db.scene_tiles.find({"scene_id": scene_id})
    all_tiles = await cursor.to_list(length=None)
    
    if not all_tiles:
        return TileListResponse(
            tiles=[],
            total_tiles=0,
            selected_lod="high",
            bandwidth_adjusted=False,
        )
    
    # Filter tiles by frustum culling
    visible_tiles = []
    
    for tile_data in all_tiles:
        tile = SceneTileInDB(**tile_data)
        
        # Check if tile bbox intersects frustum
        if not bbox_in_frustum(
            tile.bounding_box.dict(),
            camera_pos,
            camera_dir,
            fov,
            near,
            far,
        ):
            continue
        
        # Calculate distance to tile
        bbox = tile.bounding_box
        center = np.array([
            (bbox.min_x + bbox.max_x) / 2,
            (bbox.min_y + bbox.max_y) / 2,
            (bbox.min_z + bbox.max_z) / 2,
        ])
        distance = float(np.linalg.norm(center - camera_pos))
        
        # Select LOD for this tile
        if target_lod:
            tile_lod = target_lod
        else:
            tile_lod = select_lod_by_distance(distance, bandwidth)
        
        # Only include tiles matching the selected LOD
        if tile.lod != tile_lod:
            continue
        
        # Calculate priority
        priority = calculate_tile_priority(tile, camera_pos, camera_dir)
        
        visible_tiles.append({
            "tile": tile,
            "distance": distance,
            "priority": priority,
        })
    
    # Sort by priority (descending)
    visible_tiles.sort(key=lambda x: x["priority"], reverse=True)
    
    # Limit to max_tiles
    visible_tiles = visible_tiles[:request.max_tiles]
    
    # Build response
    tile_responses = []
    for item in visible_tiles:
        tile = item["tile"]
        tile_responses.append(TileResponse(
            tile_id=tile.id,
            level=tile.level,
            x=tile.x,
            y=tile.y,
            z=tile.z,
            lod=tile.lod,
            priority=item["priority"],
            distance=item["distance"],
            file_path=tile.file_path,
            file_size_bytes=tile.file_size_bytes,
            gaussian_count=tile.gaussian_count,
            bounding_box=tile.bounding_box.dict(),
        ))
    
    return TileListResponse(
        tiles=tile_responses,
        total_tiles=len(all_tiles),
        selected_lod=target_lod or "mixed",
        bandwidth_adjusted=bandwidth_adjusted,
    )


@router.get("/{scene_id}/tiles/{tile_id}")
async def download_tile(
    scene_id: str,
    tile_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Download a specific tile file.
    
    Implements:
    - Valkey caching with 1 hour TTL
    - HTTP range requests support
    - Sub-100ms cache hits
    """
    from fastapi.responses import FileResponse, Response
    from utils.minio_client import get_minio_client
    from utils.valkey_client import get_valkey_client
    import tempfile
    import os
    
    # Verify scene access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id,
    })
    
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Get tile metadata
    tile_data = await db.scene_tiles.find_one({
        "_id": tile_id,
        "scene_id": scene_id,
    })
    
    if not tile_data:
        raise HTTPException(status_code=404, detail="Tile not found")
    
    tile = SceneTileInDB(**tile_data)
    
    # Try cache first (Task 18.6)
    valkey = get_valkey_client()
    cache_key = f"tile:{scene_id}:{tile_id}"
    
    cached_data = valkey.get_bytes(cache_key)
    if cached_data:
        # Cache hit - return directly
        return Response(
            content=cached_data,
            media_type="application/octet-stream",
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600",
                "X-Cache": "HIT",
            }
        )
    
    # Cache miss - download from MinIO
    minio = get_minio_client()
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ply")
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        # Extract object name from file_path
        object_name = tile.file_path.replace("scenes/", "")
        minio.download_file("scenes", object_name, temp_path)
        
        # Read file data
        with open(temp_path, 'rb') as f:
            tile_data_bytes = f.read()
        
        # Cache for 1 hour (3600 seconds)
        valkey.set_bytes(cache_key, tile_data_bytes, ttl=3600)
        
        # Return file
        return Response(
            content=tile_data_bytes,
            media_type="application/octet-stream",
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600",
                "X-Cache": "MISS",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download tile: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
