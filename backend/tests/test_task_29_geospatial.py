"""
Unit tests for geospatial features.

Task 29.10: Write geospatial tests
- Test coordinate transformations
- Test geodetic calculations
- Test GeoJSON export
- Test orthophoto overlay
"""

import pytest
import math
from backend.models.geospatial import (
    GeospatialCoordinates,
    ProjectedCoordinates,
    CoordinateSystem,
    GroundControlPoint,
    SceneGeoreferencing,
)
from backend.services.coordinate_transformer import CoordinateTransformerService


class TestCoordinateTransformations:
    """Test coordinate system transformations."""
    
    def test_get_utm_zone(self):
        """Test UTM zone calculation."""
        # Test various longitudes
        assert CoordinateTransformerService.get_utm_zone(-123.0, 45.0) == 10
        assert CoordinateTransformerService.get_utm_zone(0.0, 45.0) == 31
        assert CoordinateTransformerService.get_utm_zone(179.0, 45.0) == 60
        assert CoordinateTransformerService.get_utm_zone(-180.0, 45.0) == 1
    
    def test_get_utm_epsg(self):
        """Test UTM EPSG code calculation."""
        # Northern hemisphere
        assert CoordinateTransformerService.get_utm_epsg(-123.0, 45.0) == 32610
        
        # Southern hemisphere
        assert CoordinateTransformerService.get_utm_epsg(-123.0, -45.0) == 32710
    
    def test_transform_wgs84_to_utm(self):
        """Test WGS84 to UTM transformation."""
        coords = GeospatialCoordinates(
            latitude=45.0,
            longitude=-123.0,
            altitude=100.0
        )
        
        # Transform to UTM
        projected = CoordinateTransformerService.transform_wgs84_to_projected(
            coords,
            target_epsg=32610  # UTM Zone 10N
        )
        
        assert projected.coordinate_system == CoordinateSystem.UTM
        assert projected.epsg_code == 32610
        assert projected.x is not None
        assert projected.y is not None
        assert projected.z is not None
    
    def test_transform_utm_to_wgs84(self):
        """Test UTM to WGS84 transformation."""
        projected = ProjectedCoordinates(
            x=500000.0,
            y=4982950.0,
            z=100.0,
            coordinate_system=CoordinateSystem.UTM,
            epsg_code=32610
        )
        
        # Transform to WGS84
        wgs84 = CoordinateTransformerService.transform_projected_to_wgs84(projected)
        
        assert -90 <= wgs84.latitude <= 90
        assert -180 <= wgs84.longitude <= 180
        assert wgs84.altitude is not None
    
    def test_transform_round_trip(self):
        """Test round-trip transformation accuracy."""
        original = GeospatialCoordinates(
            latitude=45.5,
            longitude=-122.5,
            altitude=50.0
        )
        
        # Forward transformation
        projected = CoordinateTransformerService.transform_wgs84_to_projected(
            original,
            target_epsg=32610
        )
        
        # Reverse transformation
        back_to_wgs84 = CoordinateTransformerService.transform_projected_to_wgs84(
            projected
        )
        
        # Check accuracy (should be within 1mm)
        assert abs(original.latitude - back_to_wgs84.latitude) < 1e-7
        assert abs(original.longitude - back_to_wgs84.longitude) < 1e-7
        assert abs(original.altitude - back_to_wgs84.altitude) < 0.001


class TestGeodeticCalculations:
    """Test geodetic distance calculations."""
    
    def test_calculate_geodetic_distance_same_point(self):
        """Test distance between same point is zero."""
        coord = GeospatialCoordinates(latitude=45.0, longitude=-122.0)
        
        distance = CoordinateTransformerService.calculate_geodetic_distance(coord, coord)
        
        assert distance == 0.0
    
    def test_calculate_geodetic_distance_equator(self):
        """Test distance along equator."""
        coord1 = GeospatialCoordinates(latitude=0.0, longitude=0.0)
        coord2 = GeospatialCoordinates(latitude=0.0, longitude=1.0)
        
        distance = CoordinateTransformerService.calculate_geodetic_distance(coord1, coord2)
        
        # 1 degree at equator ≈ 111.32 km
        assert 111000 < distance < 112000
    
    def test_calculate_geodetic_distance_with_altitude(self):
        """Test distance calculation with altitude difference."""
        coord1 = GeospatialCoordinates(latitude=45.0, longitude=-122.0, altitude=0.0)
        coord2 = GeospatialCoordinates(latitude=45.0, longitude=-122.0, altitude=100.0)
        
        distance = CoordinateTransformerService.calculate_geodetic_distance(coord1, coord2)
        
        # Should be approximately 100m (vertical distance)
        assert 99 < distance < 101
    
    def test_calculate_geodetic_distance_antipodal(self):
        """Test distance between antipodal points."""
        coord1 = GeospatialCoordinates(latitude=0.0, longitude=0.0)
        coord2 = GeospatialCoordinates(latitude=0.0, longitude=180.0)
        
        distance = CoordinateTransformerService.calculate_geodetic_distance(coord1, coord2)
        
        # Half Earth's circumference ≈ 20,000 km
        assert 19900000 < distance < 20100000


class TestGeospatialModels:
    """Test geospatial data models."""
    
    def test_geospatial_coordinates_validation(self):
        """Test coordinate validation."""
        # Valid coordinates
        coords = GeospatialCoordinates(latitude=45.0, longitude=-122.0)
        assert coords.latitude == 45.0
        assert coords.longitude == -122.0
        
        # Invalid latitude
        with pytest.raises(ValueError):
            GeospatialCoordinates(latitude=91.0, longitude=0.0)
        
        with pytest.raises(ValueError):
            GeospatialCoordinates(latitude=-91.0, longitude=0.0)
        
        # Invalid longitude
        with pytest.raises(ValueError):
            GeospatialCoordinates(latitude=0.0, longitude=181.0)
        
        with pytest.raises(ValueError):
            GeospatialCoordinates(latitude=0.0, longitude=-181.0)
    
    def test_ground_control_point_creation(self):
        """Test GCP creation."""
        gcp = GroundControlPoint(
            id="gcp1",
            name="Control Point 1",
            scene_position=[10.0, 20.0, 5.0],
            geospatial_coordinates=GeospatialCoordinates(
                latitude=45.0,
                longitude=-122.0,
                altitude=100.0
            ),
            accuracy=0.05
        )
        
        assert gcp.id == "gcp1"
        assert gcp.name == "Control Point 1"
        assert len(gcp.scene_position) == 3
        assert gcp.accuracy == 0.05
    
    def test_scene_georeferencing_creation(self):
        """Test scene georeferencing."""
        georef = SceneGeoreferencing(
            scene_id="scene123",
            origin_coordinates=GeospatialCoordinates(
                latitude=45.0,
                longitude=-122.0,
                altitude=50.0
            ),
            coordinate_system=CoordinateSystem.WGS84,
            epsg_code=4326,
            is_georeferenced=True
        )
        
        assert georef.scene_id == "scene123"
        assert georef.is_georeferenced is True
        assert georef.coordinate_system == CoordinateSystem.WGS84
        assert georef.epsg_code == 4326


class TestTransformationAccuracy:
    """Test transformation accuracy requirements."""
    
    def test_local_projection_accuracy(self):
        """Test accuracy within 0.1m for local projections."""
        coords = GeospatialCoordinates(
            latitude=45.5,
            longitude=-122.5,
            altitude=100.0
        )
        
        # Validate transformation accuracy
        accuracy = CoordinateTransformerService.validate_transformation_accuracy(
            coords,
            target_epsg=32610  # UTM Zone 10N
        )
        
        # Should be within 0.1m (Requirement 33.11)
        assert accuracy < 0.1


class TestGeoJSONExport:
    """Test GeoJSON export functionality."""
    
    def test_geojson_feature_creation(self):
        """Test GeoJSON feature creation."""
        from backend.models.geospatial import GeoJSONFeature
        
        feature = GeoJSONFeature(
            geometry={
                "type": "Point",
                "coordinates": [-122.0, 45.0, 100.0]
            },
            properties={
                "name": "Test Point",
                "type": "annotation"
            }
        )
        
        assert feature.type == "Feature"
        assert feature.geometry["type"] == "Point"
        assert len(feature.geometry["coordinates"]) == 3
        assert feature.properties["name"] == "Test Point"
    
    def test_geojson_feature_collection_creation(self):
        """Test GeoJSON feature collection creation."""
        from backend.models.geospatial import GeoJSONFeature, GeoJSONFeatureCollection
        
        features = [
            GeoJSONFeature(
                geometry={"type": "Point", "coordinates": [-122.0, 45.0]},
                properties={"id": 1}
            ),
            GeoJSONFeature(
                geometry={"type": "Point", "coordinates": [-123.0, 46.0]},
                properties={"id": 2}
            ),
        ]
        
        collection = GeoJSONFeatureCollection(features=features)
        
        assert collection.type == "FeatureCollection"
        assert len(collection.features) == 2
        assert collection.features[0].properties["id"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
