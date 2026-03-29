"""
Tests for Task 23: Scene Annotations

Tests annotation creation, measurement calculations, rendering,
editing, and defect annotations with photo attachments.
"""

import pytest
import uuid
from datetime import datetime
from models.annotation import (
    AnnotationCreate,
    AnnotationType,
    DefectCategory,
    SeverityLevel,
    Position3D,
    MeasurementData,
    DefectData,
)
from api.annotations import calculate_distance, calculate_polygon_area


class TestAnnotationModels:
    """Test annotation data models."""
    
    def test_position_3d_model(self):
        """Test Position3D model."""
        pos = Position3D(x=1.0, y=2.0, z=3.0)
        assert pos.x == 1.0
        assert pos.y == 2.0
        assert pos.z == 3.0
    
    def test_measurement_data_model(self):
        """Test MeasurementData model."""
        points = [
            Position3D(x=0.0, y=0.0, z=0.0),
            Position3D(x=1.0, y=0.0, z=0.0),
        ]
        measurement = MeasurementData(
            measurement_type="distance",
            value=1.0,
            unit="m",
            points=points
        )
        assert measurement.measurement_type == "distance"
        assert measurement.value == 1.0
        assert measurement.unit == "m"
        assert len(measurement.points) == 2
    
    def test_defect_data_model(self):
        """Test DefectData model."""
        defect = DefectData(
            category=DefectCategory.CRACK,
            severity=SeverityLevel.HIGH,
            photo_paths=["defects/scene1/ann1/photo1.jpg"]
        )
        assert defect.category == DefectCategory.CRACK
        assert defect.severity == SeverityLevel.HIGH
        assert len(defect.photo_paths) == 1
    
    def test_annotation_create_comment(self):
        """Test creating a comment annotation."""
        annotation = AnnotationCreate(
            annotation_type=AnnotationType.COMMENT,
            position=Position3D(x=1.0, y=2.0, z=3.0),
            content="This is a test comment"
        )
        assert annotation.annotation_type == AnnotationType.COMMENT
        assert annotation.content == "This is a test comment"
    
    def test_annotation_create_measurement(self):
        """Test creating a measurement annotation."""
        points = [
            Position3D(x=0.0, y=0.0, z=0.0),
            Position3D(x=3.0, y=4.0, z=0.0),
        ]
        measurement = MeasurementData(
            measurement_type="distance",
            value=5.0,
            unit="m",
            points=points
        )
        annotation = AnnotationCreate(
            annotation_type=AnnotationType.MEASUREMENT,
            position=Position3D(x=1.5, y=2.0, z=0.0),
            content="Distance measurement",
            measurement_data=measurement
        )
        assert annotation.annotation_type == AnnotationType.MEASUREMENT
        assert annotation.measurement_data is not None
        assert annotation.measurement_data.value == 5.0
    
    def test_annotation_create_defect(self):
        """Test creating a defect annotation."""
        defect = DefectData(
            category=DefectCategory.CRACK,
            severity=SeverityLevel.CRITICAL,
            photo_paths=[]
        )
        annotation = AnnotationCreate(
            annotation_type=AnnotationType.DEFECT,
            position=Position3D(x=5.0, y=1.0, z=2.0),
            content="Critical crack detected",
            defect_data=defect
        )
        assert annotation.annotation_type == AnnotationType.DEFECT
        assert annotation.defect_data is not None
        assert annotation.defect_data.category == DefectCategory.CRACK
        assert annotation.defect_data.severity == SeverityLevel.CRITICAL


class TestMeasurementCalculations:
    """Test measurement calculation functions."""
    
    def test_calculate_distance_simple(self):
        """Test distance calculation between two points."""
        p1 = Position3D(x=0.0, y=0.0, z=0.0)
        p2 = Position3D(x=3.0, y=4.0, z=0.0)
        distance = calculate_distance(p1, p2)
        assert abs(distance - 5.0) < 0.001  # 3-4-5 triangle
    
    def test_calculate_distance_3d(self):
        """Test distance calculation in 3D space."""
        p1 = Position3D(x=0.0, y=0.0, z=0.0)
        p2 = Position3D(x=1.0, y=1.0, z=1.0)
        distance = calculate_distance(p1, p2)
        expected = (1**2 + 1**2 + 1**2) ** 0.5  # sqrt(3)
        assert abs(distance - expected) < 0.001
    
    def test_calculate_distance_negative_coords(self):
        """Test distance with negative coordinates."""
        p1 = Position3D(x=-1.0, y=-1.0, z=-1.0)
        p2 = Position3D(x=1.0, y=1.0, z=1.0)
        distance = calculate_distance(p1, p2)
        expected = (2**2 + 2**2 + 2**2) ** 0.5  # sqrt(12)
        assert abs(distance - expected) < 0.001
    
    def test_calculate_polygon_area_triangle(self):
        """Test area calculation for a triangle."""
        points = [
            Position3D(x=0.0, y=0.0, z=0.0),
            Position3D(x=4.0, y=0.0, z=0.0),
            Position3D(x=0.0, y=3.0, z=0.0),
        ]
        area = calculate_polygon_area(points)
        assert abs(area - 6.0) < 0.001  # (4 * 3) / 2 = 6
    
    def test_calculate_polygon_area_square(self):
        """Test area calculation for a square."""
        points = [
            Position3D(x=0.0, y=0.0, z=0.0),
            Position3D(x=2.0, y=0.0, z=0.0),
            Position3D(x=2.0, y=2.0, z=0.0),
            Position3D(x=0.0, y=2.0, z=0.0),
        ]
        area = calculate_polygon_area(points)
        assert abs(area - 4.0) < 0.001  # 2 * 2 = 4
    
    def test_calculate_polygon_area_insufficient_points(self):
        """Test area calculation with insufficient points."""
        points = [
            Position3D(x=0.0, y=0.0, z=0.0),
            Position3D(x=1.0, y=0.0, z=0.0),
        ]
        area = calculate_polygon_area(points)
        assert area == 0.0


class TestAnnotationTypes:
    """Test different annotation types."""
    
    def test_annotation_type_enum(self):
        """Test AnnotationType enum values."""
        assert AnnotationType.COMMENT.value == "comment"
        assert AnnotationType.MEASUREMENT.value == "measurement"
        assert AnnotationType.MARKER.value == "marker"
        assert AnnotationType.DEFECT.value == "defect"
    
    def test_defect_category_enum(self):
        """Test DefectCategory enum values."""
        assert DefectCategory.CRACK.value == "crack"
        assert DefectCategory.DAMAGE.value == "damage"
        assert DefectCategory.CORROSION.value == "corrosion"
        assert DefectCategory.WATER_DAMAGE.value == "water_damage"
        assert DefectCategory.STRUCTURAL_ISSUE.value == "structural_issue"
        assert DefectCategory.CUSTOM.value == "custom"
    
    def test_severity_level_enum(self):
        """Test SeverityLevel enum values."""
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.CRITICAL.value == "critical"


class TestDefectAnnotations:
    """Test defect-specific annotation features."""
    
    def test_defect_with_all_categories(self):
        """Test defect annotations with all categories."""
        categories = [
            DefectCategory.CRACK,
            DefectCategory.DAMAGE,
            DefectCategory.CORROSION,
            DefectCategory.WATER_DAMAGE,
            DefectCategory.STRUCTURAL_ISSUE,
            DefectCategory.CUSTOM,
        ]
        
        for category in categories:
            defect = DefectData(
                category=category,
                severity=SeverityLevel.MEDIUM,
                photo_paths=[]
            )
            assert defect.category == category
    
    def test_defect_with_all_severities(self):
        """Test defect annotations with all severity levels."""
        severities = [
            SeverityLevel.LOW,
            SeverityLevel.MEDIUM,
            SeverityLevel.HIGH,
            SeverityLevel.CRITICAL,
        ]
        
        for severity in severities:
            defect = DefectData(
                category=DefectCategory.CRACK,
                severity=severity,
                photo_paths=[]
            )
            assert defect.severity == severity
    
    def test_defect_with_custom_category(self):
        """Test defect with custom category."""
        defect = DefectData(
            category=DefectCategory.CUSTOM,
            severity=SeverityLevel.MEDIUM,
            custom_category="Unusual discoloration",
            photo_paths=[]
        )
        assert defect.category == DefectCategory.CUSTOM
        assert defect.custom_category == "Unusual discoloration"
    
    def test_defect_with_multiple_photos(self):
        """Test defect with multiple photo attachments."""
        photo_paths = [
            "defects/scene1/ann1/photo1.jpg",
            "defects/scene1/ann1/photo2.jpg",
            "defects/scene1/ann1/photo3.jpg",
        ]
        defect = DefectData(
            category=DefectCategory.CRACK,
            severity=SeverityLevel.HIGH,
            photo_paths=photo_paths
        )
        assert len(defect.photo_paths) == 3
        assert defect.photo_paths[0] == "defects/scene1/ann1/photo1.jpg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
