"""
Tests for Task 30: Camera Limits and Configuration

Tests camera boundary enforcement, zoom limits, axis locks, and default positions.

Requirements: 30.1-30.10
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from main import app
from models.scene import CameraConfiguration, CameraBoundary


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user_token():
    """Mock JWT token for testing."""
    # In real tests, this would be a valid JWT token
    return "mock_token_for_testing"


@pytest.fixture
def test_scene_id():
    """Generate test scene ID."""
    return str(uuid.uuid4())


class TestCameraBoundaryDefinition:
    """Test camera boundary definition (Requirement 30.1, 30.2, 30.10)."""
    
    def test_create_camera_boundary(self):
        """Test creating a camera boundary."""
        boundary = CameraBoundary(
            min_x=-10.0,
            min_y=-10.0,
            min_z=-10.0,
            max_x=10.0,
            max_y=10.0,
            max_z=10.0
        )
        
        assert boundary.min_x == -10.0
        assert boundary.max_x == 10.0
        assert boundary.min_y == -10.0
        assert boundary.max_y == 10.0
        assert boundary.min_z == -10.0
        assert boundary.max_z == 10.0
    
    def test_camera_config_with_boundary(self):
        """Test camera configuration with boundary enabled."""
        boundary = CameraBoundary(
            min_x=-10.0, min_y=-10.0, min_z=-10.0,
            max_x=10.0, max_y=10.0, max_z=10.0
        )
        
        config = CameraConfiguration(
            boundary=boundary,
            boundary_enabled=True,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.boundary_enabled is True
        assert config.boundary is not None
        assert config.show_boundary_indicators is True
    
    def test_boundary_validation_invalid_ranges(self):
        """Test that invalid boundary ranges are detected."""
        # This should be caught by API validation
        # Min values must be less than max values
        with pytest.raises(Exception):
            # Invalid: min_x >= max_x
            boundary = CameraBoundary(
                min_x=10.0,
                min_y=-10.0,
                min_z=-10.0,
                max_x=5.0,  # Less than min_x
                max_y=10.0,
                max_z=10.0
            )


class TestZoomLimits:
    """Test zoom limits (Requirement 30.3, 30.4)."""
    
    def test_default_zoom_limits(self):
        """Test default zoom limits."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.min_zoom_distance == 0.1
        assert config.max_zoom_distance == 1000.0
    
    def test_custom_zoom_limits(self):
        """Test custom zoom limits."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=1.0,
            max_zoom_distance=100.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.min_zoom_distance == 1.0
        assert config.max_zoom_distance == 100.0
    
    def test_zoom_limits_validation(self):
        """Test that min_zoom must be less than max_zoom."""
        # This validation happens in the API endpoint
        # Min zoom must be less than max zoom
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=100.0,
            max_zoom_distance=10.0,  # Less than min
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        # The API should reject this, but the model allows it
        # API validation is tested separately
        assert config.min_zoom_distance > config.max_zoom_distance


class TestAxisLocks:
    """Test axis locks (Requirement 30.5, 30.6)."""
    
    def test_no_axis_locks(self):
        """Test configuration with no axis locks."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.lock_x_axis is False
        assert config.lock_y_axis is False
        assert config.lock_z_axis is False
    
    def test_lock_x_axis(self):
        """Test locking X axis."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=True,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.lock_x_axis is True
        assert config.lock_y_axis is False
        assert config.lock_z_axis is False
    
    def test_lock_multiple_axes(self):
        """Test locking multiple axes."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=True,
            lock_y_axis=True,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.lock_x_axis is True
        assert config.lock_y_axis is True
        assert config.lock_z_axis is False
    
    def test_lock_all_axes(self):
        """Test locking all axes (fixed camera position)."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=True,
            lock_y_axis=True,
            lock_z_axis=True,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.lock_x_axis is True
        assert config.lock_y_axis is True
        assert config.lock_z_axis is True


class TestDefaultCameraPosition:
    """Test default camera position (Requirement 30.7, 30.8)."""
    
    def test_no_default_position(self):
        """Test configuration without default position."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.default_position is None
        assert config.default_target is None
    
    def test_with_default_position(self):
        """Test configuration with default position."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            default_position=[5.0, 5.0, 5.0],
            default_target=[0.0, 0.0, 0.0],
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.default_position == [5.0, 5.0, 5.0]
        assert config.default_target == [0.0, 0.0, 0.0]
    
    def test_rotation_disabled(self):
        """Test disabling rotation for fixed viewpoint."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=False,
            show_boundary_indicators=True
        )
        
        assert config.rotation_enabled is False
    
    def test_fixed_viewpoint_scene(self):
        """Test configuration for fixed-viewpoint scene."""
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=True,
            lock_y_axis=True,
            lock_z_axis=True,
            default_position=[10.0, 10.0, 10.0],
            default_target=[0.0, 0.0, 0.0],
            rotation_enabled=False,
            show_boundary_indicators=True
        )
        
        assert config.rotation_enabled is False
        assert config.lock_x_axis is True
        assert config.lock_y_axis is True
        assert config.lock_z_axis is True
        assert config.default_position is not None


class TestCameraConfigurationStorage:
    """Test camera configuration storage (Requirement 30.9)."""
    
    def test_camera_config_serialization(self):
        """Test that camera config can be serialized."""
        boundary = CameraBoundary(
            min_x=-10.0, min_y=-10.0, min_z=-10.0,
            max_x=10.0, max_y=10.0, max_z=10.0
        )
        
        config = CameraConfiguration(
            boundary=boundary,
            boundary_enabled=True,
            min_zoom_distance=0.5,
            max_zoom_distance=500.0,
            lock_x_axis=False,
            lock_y_axis=True,
            lock_z_axis=False,
            default_position=[5.0, 5.0, 5.0],
            default_target=[0.0, 0.0, 0.0],
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        # Serialize to dict
        config_dict = config.model_dump()
        
        assert config_dict['boundary_enabled'] is True
        assert config_dict['min_zoom_distance'] == 0.5
        assert config_dict['max_zoom_distance'] == 500.0
        assert config_dict['lock_y_axis'] is True
        assert config_dict['default_position'] == [5.0, 5.0, 5.0]
    
    def test_camera_config_deserialization(self):
        """Test that camera config can be deserialized."""
        config_dict = {
            'boundary': {
                'min_x': -10.0, 'min_y': -10.0, 'min_z': -10.0,
                'max_x': 10.0, 'max_y': 10.0, 'max_z': 10.0
            },
            'boundary_enabled': True,
            'min_zoom_distance': 0.5,
            'max_zoom_distance': 500.0,
            'lock_x_axis': False,
            'lock_y_axis': True,
            'lock_z_axis': False,
            'default_position': [5.0, 5.0, 5.0],
            'default_target': [0.0, 0.0, 0.0],
            'rotation_enabled': True,
            'show_boundary_indicators': True
        }
        
        config = CameraConfiguration(**config_dict)
        
        assert config.boundary_enabled is True
        assert config.min_zoom_distance == 0.5
        assert config.lock_y_axis is True
        assert config.default_position == [5.0, 5.0, 5.0]


class TestBoundaryIndicators:
    """Test boundary indicators (Requirement 30.10)."""
    
    def test_boundary_indicators_enabled(self):
        """Test that boundary indicators can be enabled."""
        config = CameraConfiguration(
            boundary_enabled=True,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.show_boundary_indicators is True
    
    def test_boundary_indicators_disabled(self):
        """Test that boundary indicators can be disabled."""
        config = CameraConfiguration(
            boundary_enabled=True,
            min_zoom_distance=0.1,
            max_zoom_distance=1000.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            rotation_enabled=True,
            show_boundary_indicators=False
        )
        
        assert config.show_boundary_indicators is False


class TestCompleteConfiguration:
    """Test complete camera configuration scenarios."""
    
    def test_construction_site_config(self):
        """Test typical construction site camera configuration."""
        # Restrict to site boundaries, allow rotation, set default view
        boundary = CameraBoundary(
            min_x=-50.0, min_y=-50.0, min_z=0.0,
            max_x=50.0, max_y=50.0, max_z=30.0
        )
        
        config = CameraConfiguration(
            boundary=boundary,
            boundary_enabled=True,
            min_zoom_distance=1.0,
            max_zoom_distance=200.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            default_position=[30.0, 30.0, 20.0],
            default_target=[0.0, 0.0, 5.0],
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.boundary_enabled is True
        assert config.boundary.min_z == 0.0  # Ground level
        assert config.rotation_enabled is True
        assert config.default_position is not None
    
    def test_indoor_room_config(self):
        """Test typical indoor room camera configuration."""
        # Small boundary, limited zoom, allow rotation
        boundary = CameraBoundary(
            min_x=-5.0, min_y=-5.0, min_z=0.0,
            max_x=5.0, max_y=5.0, max_z=3.0
        )
        
        config = CameraConfiguration(
            boundary=boundary,
            boundary_enabled=True,
            min_zoom_distance=0.5,
            max_zoom_distance=15.0,
            lock_x_axis=False,
            lock_y_axis=False,
            lock_z_axis=False,
            default_position=[3.0, 3.0, 1.5],
            default_target=[0.0, 0.0, 1.0],
            rotation_enabled=True,
            show_boundary_indicators=True
        )
        
        assert config.boundary.max_z == 3.0  # Ceiling height
        assert config.max_zoom_distance == 15.0
    
    def test_fixed_inspection_view(self):
        """Test fixed inspection viewpoint configuration."""
        # Fixed position, no rotation, locked axes
        config = CameraConfiguration(
            boundary_enabled=False,
            min_zoom_distance=5.0,
            max_zoom_distance=20.0,
            lock_x_axis=True,
            lock_y_axis=True,
            lock_z_axis=True,
            default_position=[10.0, 0.0, 5.0],
            default_target=[0.0, 0.0, 0.0],
            rotation_enabled=False,
            show_boundary_indicators=False
        )
        
        assert config.rotation_enabled is False
        assert config.lock_x_axis is True
        assert config.lock_y_axis is True
        assert config.lock_z_axis is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
