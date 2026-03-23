"""
Point coordinates model for storing geospatial data for individual points.

Associates scene points with GPS coordinates.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from models.geospatial import GeospatialCoordinates, ProjectedCoordinates


class PointCoordinatesInDB(BaseModel):
    """Point coordinates stored in MongoDB."""
    id: str = Field(alias="_id")
    scene_id: str = Field(..., description="Scene identifier")
    point_id: str = Field(..., description="Point identifier (e.g., annotation_id, object_id)")
    point_type: str = Field(..., description="Type of point (annotation, object, gcp, etc.)")
    
    # Scene coordinates
    scene_x: float = Field(..., description="X coordinate in scene space")
    scene_y: float = Field(..., description="Y coordinate in scene space")
    scene_z: float = Field(..., description="Z coordinate in scene space")
    
    # Geospatial coordinates
    geospatial_coordinates: Optional[GeospatialCoordinates] = Field(None, description="GPS coordinates")
    projected_coordinates: Optional[ProjectedCoordinates] = Field(None, description="Projected coordinates")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class PointCoordinatesCreate(BaseModel):
    """Schema for creating point coordinates."""
    scene_id: str
    point_id: str
    point_type: str
    scene_x: float
    scene_y: float
    scene_z: float
    geospatial_coordinates: Optional[GeospatialCoordinates] = None
    projected_coordinates: Optional[ProjectedCoordinates] = None


class PointCoordinatesUpdate(BaseModel):
    """Schema for updating point coordinates."""
    geospatial_coordinates: Optional[GeospatialCoordinates] = None
    projected_coordinates: Optional[ProjectedCoordinates] = None


class PointCoordinatesResponse(BaseModel):
    """Response model for point coordinates."""
    id: str = Field(alias="_id")
    scene_id: str
    point_id: str
    point_type: str
    scene_x: float
    scene_y: float
    scene_z: float
    geospatial_coordinates: Optional[GeospatialCoordinates] = None
    projected_coordinates: Optional[ProjectedCoordinates] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
