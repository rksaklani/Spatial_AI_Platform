"""
Scene model for 3D scene management.

Represents a 3D scene created from video or 3D file upload,
tracking processing status, metadata, and organization ownership.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class SceneStatus(str, Enum):
    """Scene processing status."""
    UPLOADED = "uploaded"
    EXTRACTING_FRAMES = "extracting_frames"
    ESTIMATING_POSES = "estimating_poses"
    GENERATING_DEPTH = "generating_depth"
    RECONSTRUCTING = "reconstructing"
    TILING = "tiling"
    READY = "ready"
    FAILED = "failed"


class SceneType(str, Enum):
    """Type of scene source."""
    VIDEO = "video"
    IMAGES = "images"
    POINT_CLOUD = "point_cloud"
    MESH = "mesh"


class VideoMetadata(BaseModel):
    """Metadata for video source."""
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None


class ProcessingMetrics(BaseModel):
    """Processing pipeline metrics."""
    frame_count: int = 0
    valid_frame_count: int = 0
    depth_map_count: int = 0
    camera_count: int = 0
    point_count: int = 0
    tile_count: int = 0
    processing_time_seconds: float = 0.0


class SceneBase(BaseModel):
    """Base scene properties."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SceneCreate(SceneBase):
    """Schema for creating a new scene (via upload)."""
    pass


class SceneUpdate(BaseModel):
    """Schema for updating scene metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class SceneInDB(SceneBase):
    """Internal scene model stored in MongoDB."""
    id: str = Field(alias="_id")
    organization_id: str
    owner_id: str
    
    # Source info
    source_type: SceneType = SceneType.VIDEO
    original_filename: str
    file_size_bytes: int
    mime_type: str
    
    # Storage paths (MinIO keys)
    source_path: str  # videos/{org_id}/{scene_id}/original.{ext}
    frames_path: Optional[str] = None  # frames/{scene_id}/
    depth_path: Optional[str] = None  # depth/{scene_id}/
    sparse_path: Optional[str] = None  # scenes/{scene_id}/sparse/
    tiles_path: Optional[str] = None  # scenes/{scene_id}/tiles/
    
    # Processing status
    status: SceneStatus = SceneStatus.UPLOADED
    status_message: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    video_metadata: Optional[VideoMetadata] = None
    processing_metrics: ProcessingMetrics = Field(default_factory=ProcessingMetrics)
    
    # Visibility
    is_public: bool = False
    thumbnail_path: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class SceneResponse(SceneBase):
    """Response model for scene data."""
    id: str = Field(alias="_id")
    organization_id: str
    owner_id: str
    source_type: str
    original_filename: str
    file_size_bytes: int
    status: str
    status_message: Optional[str] = None
    error_message: Optional[str] = None
    video_metadata: Optional[VideoMetadata] = None
    processing_metrics: ProcessingMetrics
    is_public: bool
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class SceneListResponse(BaseModel):
    """Response model for scene list with pagination."""
    items: List[SceneResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
