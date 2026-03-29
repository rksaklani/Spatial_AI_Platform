"""
Geospatial models for coordinate storage and transformation.

Supports WGS84, UTM, State Plane, and custom coordinate systems.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator


class CoordinateSystem(str, Enum):
    """Supported coordinate systems."""
    WGS84 = "WGS84"  # EPSG:4326
    UTM = "UTM"
    STATE_PLANE = "STATE_PLANE"
    CUSTOM = "CUSTOM"


class GeospatialCoordinates(BaseModel):
    """GPS coordinates in WGS84 format."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    altitude: Optional[float] = Field(None, description="Altitude in meters above sea level")
    accuracy: Optional[float] = Field(None, description="Horizontal accuracy in meters")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v


class ProjectedCoordinates(BaseModel):
    """Projected coordinates in a specific coordinate system."""
    x: float = Field(..., description="X coordinate (easting)")
    y: float = Field(..., description="Y coordinate (northing)")
    z: Optional[float] = Field(None, description="Z coordinate (elevation)")
    coordinate_system: CoordinateSystem = Field(..., description="Coordinate system")
    epsg_code: Optional[int] = Field(None, description="EPSG code for the coordinate system")
    proj_string: Optional[str] = Field(None, description="PROJ string for custom projections")
    wkt: Optional[str] = Field(None, description="Well-Known Text representation")


class GroundControlPoint(BaseModel):
    """Ground control point with known coordinates."""
    id: str = Field(..., description="Unique identifier for the GCP")
    name: Optional[str] = Field(None, description="Human-readable name")
    scene_position: List[float] = Field(..., min_items=3, max_items=3, description="Position in scene coordinates [x, y, z]")
    geospatial_coordinates: GeospatialCoordinates = Field(..., description="GPS coordinates")
    accuracy: Optional[float] = Field(None, description="Measurement accuracy in meters")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SceneGeoreferencing(BaseModel):
    """Georeferencing information for a scene."""
    scene_id: str = Field(..., description="Scene identifier")
    origin_coordinates: Optional[GeospatialCoordinates] = Field(None, description="Scene origin in GPS coordinates")
    coordinate_system: CoordinateSystem = Field(default=CoordinateSystem.WGS84, description="Primary coordinate system")
    epsg_code: Optional[int] = Field(None, description="EPSG code")
    proj_string: Optional[str] = Field(None, description="PROJ string for transformations")
    wkt: Optional[str] = Field(None, description="Well-Known Text coordinate system definition")
    ground_control_points: List[GroundControlPoint] = Field(default_factory=list, description="Ground control points")
    transformation_matrix: Optional[List[List[float]]] = Field(None, description="4x4 transformation matrix")
    is_georeferenced: bool = Field(default=False, description="Whether scene has valid georeferencing")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PointCoordinates(BaseModel):
    """Coordinates for a specific point in a scene."""
    scene_id: str = Field(..., description="Scene identifier")
    point_id: str = Field(..., description="Point identifier")
    scene_position: List[float] = Field(..., min_items=3, max_items=3, description="Position in scene coordinates [x, y, z]")
    geospatial_coordinates: Optional[GeospatialCoordinates] = Field(None, description="GPS coordinates if georeferenced")
    projected_coordinates: Optional[ProjectedCoordinates] = Field(None, description="Projected coordinates")


class GeoJSONFeature(BaseModel):
    """GeoJSON feature for export."""
    type: Literal["Feature"] = "Feature"
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Feature properties")


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON feature collection for scene export."""
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoJSONFeature] = Field(default_factory=list)
    crs: Optional[Dict[str, Any]] = Field(None, description="Coordinate reference system")


class CoordinateTransformRequest(BaseModel):
    """Request for coordinate transformation."""
    source_coordinates: GeospatialCoordinates | ProjectedCoordinates
    target_system: CoordinateSystem
    target_epsg_code: Optional[int] = None
    target_proj_string: Optional[str] = None


class CoordinateTransformResponse(BaseModel):
    """Response from coordinate transformation."""
    source_coordinates: GeospatialCoordinates | ProjectedCoordinates
    target_coordinates: GeospatialCoordinates | ProjectedCoordinates
    accuracy_meters: Optional[float] = None
