"""
Geospatial API endpoints for coordinate management.

Handles coordinate storage, transformation, and georeferencing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from api.deps import get_current_user
from utils.database import get_db
from models.user import UserInDB
from models.geospatial import (
    SceneGeoreferencing,
    GroundControlPoint,
    CoordinateTransformRequest,
    CoordinateTransformResponse,
    GeoJSONFeatureCollection,
    GeospatialCoordinates,
    ProjectedCoordinates,
)
from models.point_coordinates import (
    PointCoordinatesCreate,
    PointCoordinatesUpdate,
    PointCoordinatesResponse,
    PointCoordinatesInDB,
)
from services.coordinate_transformer import coordinate_transformer

router = APIRouter(prefix="/api/v1/geospatial", tags=["geospatial"])


@router.post("/scenes/{scene_id}/georeferencing", response_model=SceneGeoreferencing)
async def set_scene_georeferencing(
    scene_id: str,
    georeferencing: SceneGeoreferencing,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Set or update georeferencing information for a scene.
    
    Stores GPS coordinates, coordinate system, and ground control points.
    """
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Update scene with georeferencing
    georeferencing.scene_id = scene_id
    georeferencing.updated_at = datetime.utcnow()
    
    await db.scenes.update_one(
        {"_id": scene_id},
        {
            "$set": {
                "georeferencing": georeferencing.dict(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return georeferencing


@router.get("/scenes/{scene_id}/georeferencing", response_model=Optional[SceneGeoreferencing])
async def get_scene_georeferencing(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get georeferencing information for a scene."""
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    georeferencing = scene.get("georeferencing")
    if georeferencing:
        return SceneGeoreferencing(**georeferencing)
    
    return None


@router.post("/scenes/{scene_id}/ground-control-points", response_model=GroundControlPoint)
async def add_ground_control_point(
    scene_id: str,
    gcp: GroundControlPoint,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Add a ground control point to a scene."""
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Add GCP to scene georeferencing
    gcp.created_at = datetime.utcnow()
    
    await db.scenes.update_one(
        {"_id": scene_id},
        {
            "$push": {"georeferencing.ground_control_points": gcp.dict()},
            "$set": {
                "georeferencing.updated_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return gcp


@router.post("/points", response_model=PointCoordinatesResponse)
async def create_point_coordinates(
    point_coords: PointCoordinatesCreate,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Store coordinates for a specific point in a scene.
    
    Associates scene points with GPS coordinates.
    """
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({
        "_id": point_coords.scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Create point coordinates document
    point_doc = PointCoordinatesInDB(
        _id=str(ObjectId()),
        **point_coords.dict()
    )
    
    await db.point_coordinates.insert_one(point_doc.dict(by_alias=True))
    
    return PointCoordinatesResponse(**point_doc.dict(by_alias=True))


@router.get("/points/{point_id}", response_model=PointCoordinatesResponse)
async def get_point_coordinates(
    point_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get coordinates for a specific point."""
    point = await db.point_coordinates.find_one({"_id": point_id})
    
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point coordinates not found"
        )
    
    # Verify user has access to the scene
    scene = await db.scenes.find_one({
        "_id": point["scene_id"],
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return PointCoordinatesResponse(**point)


@router.get("/scenes/{scene_id}/points", response_model=List[PointCoordinatesResponse])
async def get_scene_point_coordinates(
    scene_id: str,
    point_type: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get all point coordinates for a scene."""
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Build query
    query = {"scene_id": scene_id}
    if point_type:
        query["point_type"] = point_type
    
    # Get points
    cursor = db.point_coordinates.find(query)
    points = await cursor.to_list(length=None)
    
    return [PointCoordinatesResponse(**point) for point in points]


@router.put("/points/{point_id}", response_model=PointCoordinatesResponse)
async def update_point_coordinates(
    point_id: str,
    update: PointCoordinatesUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Update coordinates for a specific point."""
    point = await db.point_coordinates.find_one({"_id": point_id})
    
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point coordinates not found"
        )
    
    # Verify user has access to the scene
    scene = await db.scenes.find_one({
        "_id": point["scene_id"],
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update point
    update_data = update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.point_coordinates.update_one(
        {"_id": point_id},
        {"$set": update_data}
    )
    
    # Get updated point
    updated_point = await db.point_coordinates.find_one({"_id": point_id})
    return PointCoordinatesResponse(**updated_point)


@router.delete("/points/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_point_coordinates(
    point_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Delete coordinates for a specific point."""
    point = await db.point_coordinates.find_one({"_id": point_id})
    
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point coordinates not found"
        )
    
    # Verify user has access to the scene
    scene = await db.scenes.find_one({
        "_id": point["scene_id"],
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await db.point_coordinates.delete_one({"_id": point_id})



@router.post("/transform", response_model=CoordinateTransformResponse)
async def transform_coordinates(
    request: CoordinateTransformRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Transform coordinates between coordinate systems.
    
    Supports WGS84, UTM, State Plane, and custom projections.
    Validates accuracy within 0.1m for local projections.
    """
    try:
        source_coords = request.source_coordinates
        target_system = request.target_system
        
        # Handle different transformation types
        if isinstance(source_coords, GeospatialCoordinates):
            # WGS84 to projected
            target_coords = coordinate_transformer.transform_wgs84_to_projected(
                source_coords,
                target_epsg=request.target_epsg_code,
                target_proj_string=request.target_proj_string,
            )
            
            # Validate accuracy for local projections
            if request.target_epsg_code:
                accuracy = coordinate_transformer.validate_transformation_accuracy(
                    source_coords,
                    request.target_epsg_code,
                )
            else:
                accuracy = None
            
        elif isinstance(source_coords, ProjectedCoordinates):
            if target_system == CoordinateSystem.WGS84:
                # Projected to WGS84
                target_coords = coordinate_transformer.transform_projected_to_wgs84(
                    source_coords
                )
                accuracy = None
            else:
                # Projected to projected
                target_coords = coordinate_transformer.transform_projected_to_projected(
                    source_coords,
                    target_epsg=request.target_epsg_code,
                    target_proj_string=request.target_proj_string,
                )
                accuracy = None
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid source coordinates type"
            )
        
        return CoordinateTransformResponse(
            source_coordinates=source_coords,
            target_coordinates=target_coords,
            accuracy_meters=accuracy,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transformation failed: {str(e)}"
        )


@router.post("/distance", response_model=dict)
async def calculate_distance(
    coord1: GeospatialCoordinates,
    coord2: GeospatialCoordinates,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Calculate geodetic distance between two WGS84 coordinates.
    
    Uses Haversine formula for accurate distance calculation.
    """
    try:
        distance = coordinate_transformer.calculate_geodetic_distance(coord1, coord2)
        
        return {
            "distance_meters": distance,
            "distance_kilometers": distance / 1000.0,
            "distance_miles": distance / 1609.34,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Distance calculation failed: {str(e)}"
        )



@router.get("/scenes/{scene_id}/export/geojson", response_model=GeoJSONFeatureCollection)
async def export_scene_geojson(
    scene_id: str,
    include_annotations: bool = True,
    include_points: bool = True,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Export scene with coordinate metadata as GeoJSON.
    
    Includes:
    - Scene origin and bounding box
    - Ground control points
    - Annotations (if include_annotations=True)
    - Point coordinates (if include_points=True)
    - Coordinate system information in CRS property
    """
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    georeferencing = scene.get("georeferencing")
    if not georeferencing or not georeferencing.get("is_georeferenced"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scene is not georeferenced"
        )
    
    features = []
    
    # Add scene origin as a feature
    origin = georeferencing.get("origin_coordinates")
    if origin:
        features.append(GeoJSONFeature(
            geometry={
                "type": "Point",
                "coordinates": [
                    origin["longitude"],
                    origin["latitude"],
                    origin.get("altitude", 0)
                ]
            },
            properties={
                "type": "scene_origin",
                "scene_id": scene_id,
                "scene_name": scene.get("name", ""),
            }
        ))
    
    # Add ground control points
    gcps = georeferencing.get("ground_control_points", [])
    for gcp in gcps:
        coords = gcp.get("geospatial_coordinates", {})
        features.append(GeoJSONFeature(
            geometry={
                "type": "Point",
                "coordinates": [
                    coords.get("longitude"),
                    coords.get("latitude"),
                    coords.get("altitude", 0)
                ]
            },
            properties={
                "type": "ground_control_point",
                "gcp_id": gcp.get("id"),
                "gcp_name": gcp.get("name", ""),
                "accuracy": gcp.get("accuracy"),
            }
        ))
    
    # Add annotations if requested
    if include_annotations:
        annotations_cursor = db.annotations.find({
            "scene_id": scene_id,
            "organization_id": current_user.organization_id
        })
        annotations = await annotations_cursor.to_list(length=None)
        
        for annotation in annotations:
            # Get point coordinates for annotation
            point_coords = await db.point_coordinates.find_one({
                "scene_id": scene_id,
                "point_id": annotation["_id"],
                "point_type": "annotation"
            })
            
            if point_coords and point_coords.get("geospatial_coordinates"):
                coords = point_coords["geospatial_coordinates"]
                features.append(GeoJSONFeature(
                    geometry={
                        "type": "Point",
                        "coordinates": [
                            coords["longitude"],
                            coords["latitude"],
                            coords.get("altitude", 0)
                        ]
                    },
                    properties={
                        "type": "annotation",
                        "annotation_id": annotation["_id"],
                        "annotation_type": annotation.get("annotation_type"),
                        "content": annotation.get("content", ""),
                        "user_name": annotation.get("user_name", ""),
                        "created_at": annotation.get("created_at").isoformat() if annotation.get("created_at") else None,
                    }
                ))
    
    # Add point coordinates if requested
    if include_points:
        points_cursor = db.point_coordinates.find({
            "scene_id": scene_id
        })
        points = await points_cursor.to_list(length=1000)  # Limit to 1000 points
        
        for point in points:
            if point.get("geospatial_coordinates"):
                coords = point["geospatial_coordinates"]
                features.append(GeoJSONFeature(
                    geometry={
                        "type": "Point",
                        "coordinates": [
                            coords["longitude"],
                            coords["latitude"],
                            coords.get("altitude", 0)
                        ]
                    },
                    properties={
                        "type": "point",
                        "point_id": point["_id"],
                        "point_type": point.get("point_type"),
                    }
                ))
    
    # Build CRS (Coordinate Reference System) object
    crs = None
    if georeferencing.get("epsg_code"):
        crs = {
            "type": "name",
            "properties": {
                "name": f"EPSG:{georeferencing['epsg_code']}"
            }
        }
    elif georeferencing.get("wkt"):
        crs = {
            "type": "name",
            "properties": {
                "name": "Custom CRS",
                "wkt": georeferencing["wkt"]
            }
        }
    
    return GeoJSONFeatureCollection(
        features=features,
        crs=crs
    )
