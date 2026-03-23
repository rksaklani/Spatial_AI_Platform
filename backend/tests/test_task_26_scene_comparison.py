"""
Tests for Task 26: Scene Comparison

Tests:
- Side-by-side rendering
- Camera synchronization
- Difference calculation
- Change metrics

Requirements: 32.1-32.10
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
import time

from services.scene_difference import SceneDifferenceCalculator, Point3D, create_difference_visualization


class TestSceneDifferenceCalculator:
    """Test scene difference calculation service"""
    
    def test_calculate_difference_basic(self):
        """
        Test basic difference calculation
        
        Requirements: 32.6, 32.10
        """
        # Create test point clouds
        np.random.seed(42)
        points1 = np.random.randn(100, 3)
        colors1 = np.random.rand(100, 3)
        points2 = np.random.randn(120, 3)
        colors2 = np.random.rand(120, 3)
        
        calculator = SceneDifferenceCalculator(distance_threshold=0.5)
        result = calculator.calculate_difference(points1, colors1, points2, colors2)
        
        # Verify result structure
        assert isinstance(result.added_points, list)
        assert isinstance(result.removed_points, list)
        assert isinstance(result.changed_points, list)
        assert result.volume_difference >= 0
        assert result.area_difference >= 0
        assert result.point_count_difference == 20  # 120 - 100
    
    def test_calculate_difference_identical_scenes(self):
        """
        Test difference calculation with identical scenes
        
        Requirements: 32.6, 32.10
        """
        # Create identical point clouds
        np.random.seed(42)
        points = np.random.randn(100, 3)
        colors = np.random.rand(100, 3)
        
        calculator = SceneDifferenceCalculator(distance_threshold=0.1)
        result = calculator.calculate_difference(points, colors, points, colors)
        
        # Should have no differences
        assert len(result.added_points) == 0
        assert len(result.removed_points) == 0
        assert result.volume_difference == 0
        assert result.area_difference == 0
        assert result.point_count_difference == 0
    
    def test_calculate_difference_with_threshold(self):
        """
        Test difference calculation with different thresholds
        
        Requirements: 32.6
        """
        # Create point clouds with small differences
        np.random.seed(42)
        points1 = np.random.randn(100, 3)
        colors1 = np.random.rand(100, 3)
        points2 = points1 + 0.05  # Small offset
        colors2 = colors1
        
        # With large threshold, should match all points
        calculator_large = SceneDifferenceCalculator(distance_threshold=0.5)
        result_large = calculator_large.calculate_difference(points1, colors1, points2, colors2)
        
        assert len(result_large.removed_points) == 0
        assert len(result_large.added_points) == 0
        
        # With small threshold, should not match
        calculator_small = SceneDifferenceCalculator(distance_threshold=0.01)
        result_small = calculator_small.calculate_difference(points1, colors1, points2, colors2)
        
        assert len(result_small.removed_points) > 0 or len(result_small.added_points) > 0
    
    def test_color_coded_visualization_ply(self):
        """
        Test PLY visualization with color-coded differences
        
        Requirements: 32.7
        """
        # Create mock difference result
        from services.scene_difference import DifferenceResult
        
        result = DifferenceResult(
            added_points=[Point3D(1.0, 2.0, 3.0, 0.0, 1.0, 0.0)],
            removed_points=[Point3D(4.0, 5.0, 6.0, 1.0, 0.0, 0.0)],
            changed_points=[(Point3D(7.0, 8.0, 9.0, 0.5, 0.5, 0.5), Point3D(7.1, 8.1, 9.1, 0.6, 0.6, 0.6))],
            volume_difference=10.0,
            area_difference=5.0,
            point_count_difference=1,
        )
        
        ply_data = create_difference_visualization(result, output_format='ply')
        ply_content = ply_data.decode('utf-8')
        
        # Verify PLY structure
        assert "ply" in ply_content
        assert "element vertex 3" in ply_content  # 1 added + 1 removed + 1 changed
        assert "property float x" in ply_content
        assert "property uchar red" in ply_content
        assert "end_header" in ply_content
        
        # Verify color coding
        lines = ply_content.split('\n')
        data_lines = [line for line in lines if line and not line.startswith('ply') and not line.startswith('format') and not line.startswith('element') and not line.startswith('property') and not line.startswith('end_header')]
        
        # Should have red (255 0 0), green (0 255 0), and yellow (255 255 0)
        assert any('255 0 0' in line for line in data_lines)  # Red for removed
        assert any('0 255 0' in line for line in data_lines)  # Green for added
        assert any('255 255 0' in line for line in data_lines)  # Yellow for changed
    
    def test_color_coded_visualization_json(self):
        """
        Test JSON visualization with difference data
        
        Requirements: 32.7, 32.10
        """
        from services.scene_difference import DifferenceResult
        
        result = DifferenceResult(
            added_points=[Point3D(1.0, 2.0, 3.0, 0.0, 1.0, 0.0)],
            removed_points=[Point3D(4.0, 5.0, 6.0, 1.0, 0.0, 0.0)],
            changed_points=[(Point3D(7.0, 8.0, 9.0, 0.5, 0.5, 0.5), Point3D(7.1, 8.1, 9.1, 0.6, 0.6, 0.6))],
            volume_difference=10.0,
            area_difference=5.0,
            point_count_difference=1,
        )
        
        json_data = create_difference_visualization(result, output_format='json')
        
        import json
        data = json.loads(json_data.decode('utf-8'))
        
        # Verify structure
        assert "added_points" in data
        assert "removed_points" in data
        assert "changed_points" in data
        assert "metrics" in data
        
        # Verify counts
        assert len(data["added_points"]) == 1
        assert len(data["removed_points"]) == 1
        assert len(data["changed_points"]) == 1
        
        # Verify metrics
        metrics = data["metrics"]
        assert metrics["volume_difference"] == 10.0
        assert metrics["area_difference"] == 5.0
        assert metrics["point_count_difference"] == 1
        assert metrics["added_count"] == 1
        assert metrics["removed_count"] == 1
        assert metrics["changed_count"] == 1


class TestChangeMetricsCalculation:
    """Test change metrics calculation"""
    
    def test_volume_difference_calculation(self):
        """
        Test volume difference calculation
        
        Requirements: 32.10
        """
        calculator = SceneDifferenceCalculator()
        
        # Create two point clouds with different volumes
        points1 = np.array([
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]
        ], dtype=float)
        colors1 = np.ones((8, 3))
        
        points2 = np.array([
            [0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2],
            [2, 2, 0], [2, 0, 2], [0, 2, 2], [2, 2, 2]
        ], dtype=float)
        colors2 = np.ones((8, 3))
        
        result = calculator.calculate_difference(points1, colors1, points2, colors2)
        
        # Volume of first box: 1x1x1 = 1
        # Volume of second box: 2x2x2 = 8
        # Difference: 7
        assert abs(result.volume_difference - 7.0) < 0.01
    
    def test_area_difference_calculation(self):
        """
        Test area difference calculation
        
        Requirements: 32.10
        """
        calculator = SceneDifferenceCalculator()
        
        # Create two point clouds with different surface areas
        points1 = np.array([
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]
        ], dtype=float)
        colors1 = np.ones((8, 3))
        
        points2 = np.array([
            [0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2],
            [2, 2, 0], [2, 0, 2], [0, 2, 2], [2, 2, 2]
        ], dtype=float)
        colors2 = np.ones((8, 3))
        
        result = calculator.calculate_difference(points1, colors1, points2, colors2)
        
        # Surface area of first box: 2*(1*1 + 1*1 + 1*1) = 6
        # Surface area of second box: 2*(2*2 + 2*2 + 2*2) = 24
        # Difference: 18
        assert abs(result.area_difference - 18.0) < 0.01
    
    def test_point_count_difference(self):
        """
        Test point count difference calculation
        
        Requirements: 32.10
        """
        calculator = SceneDifferenceCalculator()
        
        points1 = np.random.randn(500, 3)
        colors1 = np.random.rand(500, 3)
        points2 = np.random.randn(750, 3)
        colors2 = np.random.rand(750, 3)
        
        result = calculator.calculate_difference(points1, colors1, points2, colors2)
        
        assert result.point_count_difference == 250  # 750 - 500
        assert result.added_points >= 0
        assert result.removed_points >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
