"""
Coordinate transformation service using PROJ library.

Supports transformations between WGS84, UTM, State Plane, and custom projections.
"""

import math
from typing import Optional, Tuple
from pyproj import Transformer, CRS
from pyproj.exceptions import CRSError
import structlog

from models.geospatial import (
    GeospatialCoordinates,
    ProjectedCoordinates,
    CoordinateSystem,
    CoordinateTransformRequest,
    CoordinateTransformResponse,
)

logger = structlog.get_logger(__name__)


class CoordinateTransformerService:
    """Service for coordinate system transformations."""
    
    # Common EPSG codes
    WGS84_EPSG = 4326  # WGS84 geographic
    WEB_MERCATOR_EPSG = 3857  # Web Mercator
    
    @staticmethod
    def get_utm_zone(longitude: float, latitude: float) -> int:
        """
        Calculate UTM zone from longitude and latitude.
        
        Args:
            longitude: Longitude in decimal degrees
            latitude: Latitude in decimal degrees
            
        Returns:
            UTM zone number (1-60)
        """
        zone = int((longitude + 180) / 6) + 1
        return zone
    
    @staticmethod
    def get_utm_epsg(longitude: float, latitude: float) -> int:
        """
        Get EPSG code for UTM zone.
        
        Args:
            longitude: Longitude in decimal degrees
            latitude: Latitude in decimal degrees
            
        Returns:
            EPSG code for the UTM zone
        """
        zone = CoordinateTransformerService.get_utm_zone(longitude, latitude)
        
        # Northern hemisphere: 32600 + zone
        # Southern hemisphere: 32700 + zone
        if latitude >= 0:
            return 32600 + zone
        else:
            return 32700 + zone
    
    @staticmethod
    def transform_wgs84_to_projected(
        coords: GeospatialCoordinates,
        target_epsg: Optional[int] = None,
        target_proj_string: Optional[str] = None,
        target_wkt: Optional[str] = None,
    ) -> ProjectedCoordinates:
        """
        Transform WGS84 coordinates to projected coordinates.
        
        Args:
            coords: WGS84 coordinates
            target_epsg: Target EPSG code
            target_proj_string: Target PROJ string
            target_wkt: Target WKT string
            
        Returns:
            Projected coordinates
            
        Raises:
            ValueError: If transformation fails
        """
        try:
            # Create source CRS (WGS84)
            source_crs = CRS.from_epsg(CoordinateTransformerService.WGS84_EPSG)
            
            # Create target CRS
            if target_epsg:
                target_crs = CRS.from_epsg(target_epsg)
            elif target_proj_string:
                target_crs = CRS.from_proj4(target_proj_string)
            elif target_wkt:
                target_crs = CRS.from_wkt(target_wkt)
            else:
                # Default to UTM zone for the coordinates
                target_epsg = CoordinateTransformerService.get_utm_epsg(
                    coords.longitude, coords.latitude
                )
                target_crs = CRS.from_epsg(target_epsg)
            
            # Create transformer
            transformer = Transformer.from_crs(
                source_crs,
                target_crs,
                always_xy=True  # Ensure lon, lat order
            )
            
            # Transform coordinates
            x, y, z = transformer.transform(
                coords.longitude,
                coords.latitude,
                coords.altitude if coords.altitude is not None else 0.0
            )
            
            # Determine coordinate system type
            coord_system = CoordinateSystem.CUSTOM
            if target_epsg:
                if 32601 <= target_epsg <= 32660 or 32701 <= target_epsg <= 32760:
                    coord_system = CoordinateSystem.UTM
                elif target_epsg in range(2200, 2300):  # State Plane NAD83
                    coord_system = CoordinateSystem.STATE_PLANE
            
            return ProjectedCoordinates(
                x=x,
                y=y,
                z=z if coords.altitude is not None else None,
                coordinate_system=coord_system,
                epsg_code=target_epsg,
                proj_string=target_proj_string,
                wkt=target_wkt or target_crs.to_wkt(),
            )
            
        except CRSError as e:
            logger.error("CRS error during transformation", error=str(e))
            raise ValueError(f"Invalid coordinate system: {e}")
        except Exception as e:
            logger.error("Transformation error", error=str(e))
            raise ValueError(f"Coordinate transformation failed: {e}")
    
    @staticmethod
    def transform_projected_to_wgs84(
        coords: ProjectedCoordinates,
    ) -> GeospatialCoordinates:
        """
        Transform projected coordinates to WGS84.
        
        Args:
            coords: Projected coordinates
            
        Returns:
            WGS84 coordinates
            
        Raises:
            ValueError: If transformation fails
        """
        try:
            # Create source CRS
            if coords.epsg_code:
                source_crs = CRS.from_epsg(coords.epsg_code)
            elif coords.proj_string:
                source_crs = CRS.from_proj4(coords.proj_string)
            elif coords.wkt:
                source_crs = CRS.from_wkt(coords.wkt)
            else:
                raise ValueError("No coordinate system definition provided")
            
            # Create target CRS (WGS84)
            target_crs = CRS.from_epsg(CoordinateTransformerService.WGS84_EPSG)
            
            # Create transformer
            transformer = Transformer.from_crs(
                source_crs,
                target_crs,
                always_xy=True
            )
            
            # Transform coordinates
            lon, lat, alt = transformer.transform(
                coords.x,
                coords.y,
                coords.z if coords.z is not None else 0.0
            )
            
            return GeospatialCoordinates(
                latitude=lat,
                longitude=lon,
                altitude=alt if coords.z is not None else None,
            )
            
        except CRSError as e:
            logger.error("CRS error during transformation", error=str(e))
            raise ValueError(f"Invalid coordinate system: {e}")
        except Exception as e:
            logger.error("Transformation error", error=str(e))
            raise ValueError(f"Coordinate transformation failed: {e}")
    
    @staticmethod
    def transform_projected_to_projected(
        coords: ProjectedCoordinates,
        target_epsg: Optional[int] = None,
        target_proj_string: Optional[str] = None,
        target_wkt: Optional[str] = None,
    ) -> ProjectedCoordinates:
        """
        Transform between projected coordinate systems.
        
        Args:
            coords: Source projected coordinates
            target_epsg: Target EPSG code
            target_proj_string: Target PROJ string
            target_wkt: Target WKT string
            
        Returns:
            Target projected coordinates
            
        Raises:
            ValueError: If transformation fails
        """
        try:
            # Create source CRS
            if coords.epsg_code:
                source_crs = CRS.from_epsg(coords.epsg_code)
            elif coords.proj_string:
                source_crs = CRS.from_proj4(coords.proj_string)
            elif coords.wkt:
                source_crs = CRS.from_wkt(coords.wkt)
            else:
                raise ValueError("No source coordinate system definition provided")
            
            # Create target CRS
            if target_epsg:
                target_crs = CRS.from_epsg(target_epsg)
            elif target_proj_string:
                target_crs = CRS.from_proj4(target_proj_string)
            elif target_wkt:
                target_crs = CRS.from_wkt(target_wkt)
            else:
                raise ValueError("No target coordinate system definition provided")
            
            # Create transformer
            transformer = Transformer.from_crs(
                source_crs,
                target_crs,
                always_xy=True
            )
            
            # Transform coordinates
            x, y, z = transformer.transform(
                coords.x,
                coords.y,
                coords.z if coords.z is not None else 0.0
            )
            
            # Determine coordinate system type
            coord_system = CoordinateSystem.CUSTOM
            if target_epsg:
                if 32601 <= target_epsg <= 32660 or 32701 <= target_epsg <= 32760:
                    coord_system = CoordinateSystem.UTM
                elif target_epsg in range(2200, 2300):
                    coord_system = CoordinateSystem.STATE_PLANE
            
            return ProjectedCoordinates(
                x=x,
                y=y,
                z=z if coords.z is not None else None,
                coordinate_system=coord_system,
                epsg_code=target_epsg,
                proj_string=target_proj_string,
                wkt=target_wkt or target_crs.to_wkt(),
            )
            
        except CRSError as e:
            logger.error("CRS error during transformation", error=str(e))
            raise ValueError(f"Invalid coordinate system: {e}")
        except Exception as e:
            logger.error("Transformation error", error=str(e))
            raise ValueError(f"Coordinate transformation failed: {e}")
    
    @staticmethod
    def calculate_geodetic_distance(
        coord1: GeospatialCoordinates,
        coord2: GeospatialCoordinates,
    ) -> float:
        """
        Calculate geodetic distance between two WGS84 coordinates using Haversine formula.
        
        Args:
            coord1: First coordinate
            coord2: Second coordinate
            
        Returns:
            Distance in meters
        """
        # Earth radius in meters
        R = 6371000.0
        
        # Convert to radians
        lat1 = math.radians(coord1.latitude)
        lon1 = math.radians(coord1.longitude)
        lat2 = math.radians(coord2.latitude)
        lon2 = math.radians(coord2.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        
        # Add altitude difference if available
        if coord1.altitude is not None and coord2.altitude is not None:
            dalt = coord2.altitude - coord1.altitude
            distance = math.sqrt(distance ** 2 + dalt ** 2)
        
        return distance
    
    @staticmethod
    def validate_transformation_accuracy(
        source: GeospatialCoordinates,
        target_epsg: int,
    ) -> float:
        """
        Validate transformation accuracy by round-trip transformation.
        
        Args:
            source: Source WGS84 coordinates
            target_epsg: Target EPSG code
            
        Returns:
            Accuracy in meters (round-trip error)
        """
        try:
            # Forward transformation
            projected = CoordinateTransformerService.transform_wgs84_to_projected(
                source, target_epsg=target_epsg
            )
            
            # Reverse transformation
            back_to_wgs84 = CoordinateTransformerService.transform_projected_to_wgs84(
                projected
            )
            
            # Calculate error
            error = CoordinateTransformerService.calculate_geodetic_distance(
                source, back_to_wgs84
            )
            
            return error
            
        except Exception as e:
            logger.error("Accuracy validation failed", error=str(e))
            return float('inf')


# Singleton instance
coordinate_transformer = CoordinateTransformerService()
