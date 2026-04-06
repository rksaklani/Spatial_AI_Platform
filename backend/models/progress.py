"""
Progress tracking models for real-time training updates.

Defines response models for REST API progress endpoints and
WebSocket progress events.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ProgressResponse(BaseModel):
    """Response model for progress endpoint."""
    scene_id: str
    progress_percent: float
    current_step: str
    status_message: str
    current_iteration: Optional[int] = None
    total_iterations: Optional[int] = None
    estimated_seconds_remaining: Optional[float] = None
    started_at: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "scene_id": "550e8400-e29b-41d4-a716-446655440000",
                "progress_percent": 45.5,
                "current_step": "reconstructing",
                "status_message": "Training Gaussian Splatting (7000 iterations)",
                "current_iteration": 3185,
                "total_iterations": 7000,
                "estimated_seconds_remaining": 420.0,
                "started_at": "2024-01-15T10:30:00Z",
                "elapsed_seconds": 380.0
            }
        }


class ProgressEvent(BaseModel):
    """WebSocket progress update event."""
    type: Literal["progress_update", "training_complete", "training_failed", "error"]
    scene_id: str
    progress_percent: Optional[float] = None
    current_step: Optional[str] = None
    status_message: Optional[str] = None
    current_iteration: Optional[int] = None
    total_iterations: Optional[int] = None
    estimated_seconds_remaining: Optional[float] = None
    error_message: Optional[str] = None
    total_time_seconds: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "progress_update",
                "scene_id": "550e8400-e29b-41d4-a716-446655440000",
                "progress_percent": 45.5,
                "current_step": "reconstructing",
                "status_message": "Training Gaussian Splatting (7000 iterations)",
                "current_iteration": 3185,
                "total_iterations": 7000,
                "estimated_seconds_remaining": 420.0,
                "timestamp": "2024-01-15T10:35:20Z"
            }
        }


def format_iteration_count(count: int) -> str:
    """
    Format iteration count with thousands separators.
    
    Args:
        count: Iteration count
        
    Returns:
        Formatted string with commas (e.g., "3,500")
    """
    return f"{count:,}"


def format_time_remaining(seconds: Optional[float]) -> str:
    """
    Format time remaining in human-readable format.
    
    Args:
        seconds: Time remaining in seconds
        
    Returns:
        Human-readable time string
    """
    if seconds is None:
        return "Calculating..."
    
    if seconds < 60:
        return "Less than 1 minute remaining"
    
    minutes = int(seconds / 60)
    
    if minutes < 60:
        return f"~{minutes} minute{'s' if minutes != 1 else ''} remaining"
    
    hours = int(minutes / 60)
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"~{hours} hour{'s' if hours != 1 else ''} remaining"
    else:
        return f"~{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''} remaining"
