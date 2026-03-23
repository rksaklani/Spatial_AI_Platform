"""
Scene Difference Calculation Service

Provides detailed geometric difference calculation between two scenes.

Requirements: 32.6, 32.7, 32.10
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Point3D:
    """3D point with color"""
    x: float
    y: float
    z: float
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0


@dataclass
class DifferenceResult:
    """Result of scene difference calculation"""
    added_points: List[Point3D]
    removed_points: List[Point3D]
    changed_points: List[Tuple[Point3D, Point3D]]  # (old, new)
    volume_difference: float
    area_difference: float
    point_count_difference: int


class SceneDifferenceCalculator:
    """
    Calculate geometric differences between two scenes
    
    Uses spatial indexing (KD-tree) for efficient point matching
    """
    
    def __init__(self, distance_threshold: float = 0.1):
        """
        Initialize calculator
        
        Args:
            distance_threshold: Maximum distance for point matching (meters)
        """
        self.distance_threshold = distance_threshold
    
    def calculate_difference(
        self,
        points1: np.ndarray,
        colors1: np.ndarray,
        points2: np.ndarray,
        colors2: np.ndarray,
    ) -> DifferenceResult:
        """
        Calculate differences between two point clouds
        
        Args:
            points1: Points from scene 1 (Nx3 array)
            colors1: Colors from scene 1 (Nx3 array)
            points2: Points from scene 2 (Nx3 array)
            colors2: Colors from scene 2 (Nx3 array)
        
        Returns:
            DifferenceResult with added, removed, and changed points
        """
        # Build KD-tree for efficient nearest neighbor search
        from scipy.spatial import cKDTree
        
        tree1 = cKDTree(points1)
        tree2 = cKDTree(points2)
        
        # Find matches from scene 1 to scene 2
        distances1, indices1 = tree2.query(points1, k=1)
        matched1 = distances1 < self.distance_threshold
        
        # Find matches from scene 2 to scene 1
        distances2, indices2 = tree1.query(points2, k=1)
        matched2 = distances2 < self.distance_threshold
        
        # Removed points: in scene 1 but not in scene 2
        removed_mask = ~matched1
        removed_points = [
            Point3D(
                x=float(points1[i, 0]),
                y=float(points1[i, 1]),
                z=float(points1[i, 2]),
                r=float(colors1[i, 0]),
                g=float(colors1[i, 1]),
                b=float(colors1[i, 2]),
            )
            for i in np.where(removed_mask)[0]
        ]
        
        # Added points: in scene 2 but not in scene 1
        added_mask = ~matched2
        added_points = [
            Point3D(
                x=float(points2[i, 0]),
                y=float(points2[i, 1]),
                z=float(points2[i, 2]),
                r=float(colors2[i, 0]),
                g=float(colors2[i, 1]),
                b=float(colors2[i, 2]),
            )
            for i in np.where(added_mask)[0]
        ]
        
        # Changed points: matched but with different properties
        changed_points = []
        for i in np.where(matched1)[0]:
            j = indices1[i]
            
            # Check if color changed significantly
            color_diff = np.linalg.norm(colors1[i] - colors2[j])
            if color_diff > 0.1:  # Threshold for color change
                old_point = Point3D(
                    x=float(points1[i, 0]),
                    y=float(points1[i, 1]),
                    z=float(points1[i, 2]),
                    r=float(colors1[i, 0]),
                    g=float(colors1[i, 1]),
                    b=float(colors1[i, 2]),
                )
                new_point = Point3D(
                    x=float(points2[j, 0]),
                    y=float(points2[j, 1]),
                    z=float(points2[j, 2]),
                    r=float(colors2[j, 0]),
                    g=float(colors2[j, 1]),
                    b=float(colors2[j, 2]),
                )
                changed_points.append((old_point, new_point))
        
        # Calculate volume and area differences
        bounds1 = self._calculate_bounds(points1)
        bounds2 = self._calculate_bounds(points2)
        
        volume1 = self._calculate_volume(bounds1)
        volume2 = self._calculate_volume(bounds2)
        volume_diff = abs(volume2 - volume1)
        
        area1 = self._calculate_surface_area(bounds1)
        area2 = self._calculate_surface_area(bounds2)
        area_diff = abs(area2 - area1)
        
        return DifferenceResult(
            added_points=added_points,
            removed_points=removed_points,
            changed_points=changed_points,
            volume_difference=volume_diff,
            area_difference=area_diff,
            point_count_difference=len(points2) - len(points1),
        )
    
    def _calculate_bounds(self, points: np.ndarray) -> Dict[str, float]:
        """Calculate bounding box for points"""
        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        
        return {
            'min_x': float(min_coords[0]),
            'min_y': float(min_coords[1]),
            'min_z': float(min_coords[2]),
            'max_x': float(max_coords[0]),
            'max_y': float(max_coords[1]),
            'max_z': float(max_coords[2]),
        }
    
    def _calculate_volume(self, bounds: Dict[str, float]) -> float:
        """Calculate volume of bounding box"""
        dx = bounds['max_x'] - bounds['min_x']
        dy = bounds['max_y'] - bounds['min_y']
        dz = bounds['max_z'] - bounds['min_z']
        return dx * dy * dz
    
    def _calculate_surface_area(self, bounds: Dict[str, float]) -> float:
        """Calculate surface area of bounding box"""
        dx = bounds['max_x'] - bounds['min_x']
        dy = bounds['max_y'] - bounds['min_y']
        dz = bounds['max_z'] - bounds['min_z']
        return 2 * (dx * dy + dy * dz + dz * dx)


def create_difference_visualization(
    result: DifferenceResult,
    output_format: str = 'ply'
) -> bytes:
    """
    Create a visualization file with color-coded differences
    
    Args:
        result: DifferenceResult from calculation
        output_format: Output format ('ply', 'json')
    
    Returns:
        Bytes of the visualization file
    """
    if output_format == 'ply':
        return _create_ply_visualization(result)
    elif output_format == 'json':
        return _create_json_visualization(result)
    else:
        raise ValueError(f"Unsupported format: {output_format}")


def _create_ply_visualization(result: DifferenceResult) -> bytes:
    """Create PLY file with color-coded differences"""
    # Combine all points with their respective colors
    all_points = []
    
    # Red for removed points
    for point in result.removed_points:
        all_points.append(f"{point.x} {point.y} {point.z} 255 0 0")
    
    # Green for added points
    for point in result.added_points:
        all_points.append(f"{point.x} {point.y} {point.z} 0 255 0")
    
    # Yellow for changed points (use new position)
    for old_point, new_point in result.changed_points:
        all_points.append(f"{new_point.x} {new_point.y} {new_point.z} 255 255 0")
    
    # Create PLY header
    header = f"""ply
format ascii 1.0
element vertex {len(all_points)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
    
    # Combine header and points
    ply_content = header + "\n".join(all_points)
    return ply_content.encode('utf-8')


def _create_json_visualization(result: DifferenceResult) -> bytes:
    """Create JSON file with difference data"""
    import json
    
    data = {
        'added_points': [
            {'x': p.x, 'y': p.y, 'z': p.z, 'r': p.r, 'g': p.g, 'b': p.b}
            for p in result.added_points
        ],
        'removed_points': [
            {'x': p.x, 'y': p.y, 'z': p.z, 'r': p.r, 'g': p.g, 'b': p.b}
            for p in result.removed_points
        ],
        'changed_points': [
            {
                'old': {'x': old.x, 'y': old.y, 'z': old.z, 'r': old.r, 'g': old.g, 'b': old.b},
                'new': {'x': new.x, 'y': new.y, 'z': new.z, 'r': new.r, 'g': new.g, 'b': new.b},
            }
            for old, new in result.changed_points
        ],
        'metrics': {
            'volume_difference': result.volume_difference,
            'area_difference': result.area_difference,
            'point_count_difference': result.point_count_difference,
            'added_count': len(result.added_points),
            'removed_count': len(result.removed_points),
            'changed_count': len(result.changed_points),
        }
    }
    
    return json.dumps(data, indent=2).encode('utf-8')
