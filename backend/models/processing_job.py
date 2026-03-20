"""
Processing job model for tracking async processing tasks.

Tracks Celery task execution, progress, and results for
video processing pipeline stages.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class JobType(str, Enum):
    """Type of processing job."""
    FRAME_EXTRACTION = "frame_extraction"
    POSE_ESTIMATION = "pose_estimation"
    DEPTH_ESTIMATION = "depth_estimation"
    SCENE_RECONSTRUCTION = "scene_reconstruction"
    TILE_GENERATION = "tile_generation"
    FULL_PIPELINE = "full_pipeline"


class JobStatus(str, Enum):
    """Processing job status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    """Job priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class JobStep(BaseModel):
    """Individual step within a processing job."""
    name: str
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percent: float = 0.0
    message: Optional[str] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ProcessingJobCreate(BaseModel):
    """Schema for creating a processing job."""
    scene_id: str
    job_type: JobType
    priority: JobPriority = JobPriority.NORMAL
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ProcessingJobInDB(BaseModel):
    """Internal processing job model stored in MongoDB."""
    id: str = Field(alias="_id")
    scene_id: str
    organization_id: str
    
    # Job configuration
    job_type: JobType
    priority: JobPriority = JobPriority.NORMAL
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Celery task tracking
    celery_task_id: Optional[str] = None
    worker_id: Optional[str] = None
    queue: str = "cpu"  # cpu or gpu
    
    # Status
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Progress tracking
    progress_percent: float = 0.0
    current_step: Optional[str] = None
    steps: List[JobStep] = Field(default_factory=list)
    
    # Results
    result: Optional[Dict[str, Any]] = None
    output_paths: Dict[str, str] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Duration tracking
    wait_time_seconds: Optional[float] = None
    run_time_seconds: Optional[float] = None
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class ProcessingJobResponse(BaseModel):
    """Response model for processing job data."""
    id: str = Field(alias="_id")
    scene_id: str
    organization_id: str
    job_type: str
    priority: str
    status: str
    progress_percent: float
    current_step: Optional[str] = None
    steps: List[JobStep]
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    wait_time_seconds: Optional[float] = None
    run_time_seconds: Optional[float] = None
    
    class Config:
        populate_by_name = True


class ProcessingJobListResponse(BaseModel):
    """Response model for job list with pagination."""
    items: List[ProcessingJobResponse]
    total: int
    page: int
    page_size: int


class JobProgressUpdate(BaseModel):
    """Schema for updating job progress."""
    status: Optional[JobStatus] = None
    progress_percent: Optional[float] = None
    current_step: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
