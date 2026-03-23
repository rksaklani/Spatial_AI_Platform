"""
BIM Clash Detection
Detects geometric conflicts between BIM elements.
Uses 0.01m tolerance for clash detection.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from workers.parsers.base import BIMElement


@dataclass
class Clash:
    """Represents a clash between two BIM elements"""
    element1_id: str
    element2_id: str
    element1_type: str
    element2_type: str
    clash_type: str  # 'overlap', 'intersection', 'clearance'
    severity: str  # 'critical', 'major', 'minor'
    overlap_volume: float  # m³
    clash_point: Tuple[float, float, float]  # Center of clash
    distance: float  # Distance between elements (negative for overlap)


class BIMClashDetector:
    """
    Detects clashes between BIM elements.
    Uses bounding box intersection and detailed geometry checks.
    """
    
    def __init__(self, tolerance: float = 0.01):
        """
        Initialize clash detector.
        
        Args:
            tolerance: Clash detection tolerance in meters (default 0.01m = 1cm)
        """
        self.tolerance = tolerance
        self.clashes = []
    
    def detect_clashes(self, elements: List[BIMElement]) -> List[Clash]:
        """
        Detect clashes between BIM elements.
        
        Args:
            elements: List of BIM elements to check
            
        Returns:
            List of detected clashes
        """
        self.clashes = []
        
        # Check all pairs of elements
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                elem1 = elements[i]
                elem2 = elements[j]
                
                # Skip if same element
                if elem1.ifc_guid == elem2.ifc_guid:
                    continue
                
                # Check if elements should be tested for clashes
                if not self._should_check_clash(elem1, elem2):
                    continue
                
                # Perform clash detection
                clash = self._check_element_clash(elem1, elem2)
                if clash:
                    self.clashes.append(clash)
        
        return self.clashes
    
    def _should_check_clash(self, elem1: BIMElement, elem2: BIMElement) -> bool:
        """
        Determine if two elements should be checked for clashes.
        Some element combinations are expected to overlap (e.g., wall and door).
        """
        # Don't check clashes between certain element pairs
        skip_pairs = [
            ('IfcWall', 'IfcDoor'),
            ('IfcWall', 'IfcWindow'),
            ('IfcSlab', 'IfcColumn'),  # Columns typically penetrate slabs
            ('IfcBeam', 'IfcColumn'),  # Beams connect to columns
        ]
        
        pair = (elem1.ifc_type, elem2.ifc_type)
        reverse_pair = (elem2.ifc_type, elem1.ifc_type)
        
        if pair in skip_pairs or reverse_pair in skip_pairs:
            return False
        
        return True
    
    def _check_element_clash(self, elem1: BIMElement, elem2: BIMElement) -> Optional[Clash]:
        """
        Check if two elements clash.
        
        Returns:
            Clash object if clash detected, None otherwise
        """
        # First check bounding box intersection (fast)
        if not self._bounding_boxes_intersect(elem1.bounds, elem2.bounds):
            return None
        
        # Calculate overlap volume and clash details
        overlap_volume = self._calculate_overlap_volume(elem1.bounds, elem2.bounds)
        
        if overlap_volume > self.tolerance ** 3:  # Minimum volume threshold
            # Calculate clash center point
            clash_point = self._calculate_clash_center(elem1.bounds, elem2.bounds)
            
            # Calculate distance (negative for overlap)
            distance = -self._calculate_penetration_depth(elem1.bounds, elem2.bounds)
            
            # Determine clash type and severity
            clash_type = self._determine_clash_type(overlap_volume, distance)
            severity = self._determine_severity(overlap_volume, distance, elem1, elem2)
            
            return Clash(
                element1_id=elem1.ifc_guid,
                element2_id=elem2.ifc_guid,
                element1_type=elem1.ifc_type,
                element2_type=elem2.ifc_type,
                clash_type=clash_type,
                severity=severity,
                overlap_volume=overlap_volume,
                clash_point=clash_point,
                distance=distance
            )
        
        return None
    
    def _bounding_boxes_intersect(self, bounds1: Dict, bounds2: Dict) -> bool:
        """Check if two bounding boxes intersect"""
        min1 = np.array(bounds1['min'])
        max1 = np.array(bounds1['max'])
        min2 = np.array(bounds2['min'])
        max2 = np.array(bounds2['max'])
        
        # Expand by tolerance
        min1 -= self.tolerance
        max1 += self.tolerance
        min2 -= self.tolerance
        max2 += self.tolerance
        
        # Check for separation on any axis
        if max1[0] < min2[0] or min1[0] > max2[0]:
            return False
        if max1[1] < min2[1] or min1[1] > max2[1]:
            return False
        if max1[2] < min2[2] or min1[2] > max2[2]:
            return False
        
        return True
    
    def _calculate_overlap_volume(self, bounds1: Dict, bounds2: Dict) -> float:
        """Calculate overlap volume between two bounding boxes"""
        min1 = np.array(bounds1['min'])
        max1 = np.array(bounds1['max'])
        min2 = np.array(bounds2['min'])
        max2 = np.array(bounds2['max'])
        
        # Calculate intersection box
        intersection_min = np.maximum(min1, min2)
        intersection_max = np.minimum(max1, max2)
        
        # Check if there's an intersection
        if np.any(intersection_max <= intersection_min):
            return 0.0
        
        # Calculate volume
        dimensions = intersection_max - intersection_min
        volume = np.prod(dimensions)
        
        return float(volume)
    
    def _calculate_clash_center(self, bounds1: Dict, bounds2: Dict) -> Tuple[float, float, float]:
        """Calculate center point of clash"""
        min1 = np.array(bounds1['min'])
        max1 = np.array(bounds1['max'])
        min2 = np.array(bounds2['min'])
        max2 = np.array(bounds2['max'])
        
        # Calculate intersection box
        intersection_min = np.maximum(min1, min2)
        intersection_max = np.minimum(max1, max2)
        
        # Center of intersection
        center = (intersection_min + intersection_max) / 2
        
        return tuple(center.tolist())
    
    def _calculate_penetration_depth(self, bounds1: Dict, bounds2: Dict) -> float:
        """Calculate maximum penetration depth"""
        min1 = np.array(bounds1['min'])
        max1 = np.array(bounds1['max'])
        min2 = np.array(bounds2['min'])
        max2 = np.array(bounds2['max'])
        
        # Calculate overlap on each axis
        overlap_x = min(max1[0], max2[0]) - max(min1[0], min2[0])
        overlap_y = min(max1[1], max2[1]) - max(min1[1], min2[1])
        overlap_z = min(max1[2], max2[2]) - max(min1[2], min2[2])
        
        # Maximum penetration is the minimum overlap
        penetration = min(overlap_x, overlap_y, overlap_z)
        
        return max(0.0, penetration)
    
    def _determine_clash_type(self, overlap_volume: float, distance: float) -> str:
        """Determine type of clash"""
        if overlap_volume > 0.001:  # > 1 liter
            return 'overlap'
        elif abs(distance) < self.tolerance:
            return 'clearance'
        else:
            return 'intersection'
    
    def _determine_severity(self, overlap_volume: float, distance: float,
                           elem1: BIMElement, elem2: BIMElement) -> str:
        """Determine severity of clash"""
        # Critical: Large overlap or structural elements
        structural_types = ['IfcBeam', 'IfcColumn', 'IfcSlab', 'IfcWall']
        
        if overlap_volume > 0.01:  # > 10 liters
            return 'critical'
        
        if elem1.ifc_type in structural_types and elem2.ifc_type in structural_types:
            if overlap_volume > 0.001:  # > 1 liter
                return 'critical'
        
        # Major: Moderate overlap
        if overlap_volume > 0.001:
            return 'major'
        
        # Minor: Small clearance issues
        return 'minor'
    
    def generate_clash_report(self) -> Dict:
        """
        Generate clash detection report.
        
        Returns:
            Dictionary with clash statistics and details
        """
        if not self.clashes:
            return {
                'total_clashes': 0,
                'by_severity': {'critical': 0, 'major': 0, 'minor': 0},
                'by_type': {},
                'clashes': []
            }
        
        # Count by severity
        severity_counts = {
            'critical': sum(1 for c in self.clashes if c.severity == 'critical'),
            'major': sum(1 for c in self.clashes if c.severity == 'major'),
            'minor': sum(1 for c in self.clashes if c.severity == 'minor')
        }
        
        # Count by type
        type_counts = {}
        for clash in self.clashes:
            clash_type = clash.clash_type
            type_counts[clash_type] = type_counts.get(clash_type, 0) + 1
        
        # Convert clashes to dict format
        clash_list = [
            {
                'element1_id': c.element1_id,
                'element2_id': c.element2_id,
                'element1_type': c.element1_type,
                'element2_type': c.element2_type,
                'clash_type': c.clash_type,
                'severity': c.severity,
                'overlap_volume': c.overlap_volume,
                'clash_point': c.clash_point,
                'distance': c.distance
            }
            for c in self.clashes
        ]
        
        return {
            'total_clashes': len(self.clashes),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'clashes': clash_list
        }
    
    def export_to_bcf(self, output_path: str):
        """
        Export clashes to BCF (BIM Collaboration Format).
        BCF is an industry standard for issue tracking in BIM.
        """
        # BCF export is complex - this is a placeholder
        # Full implementation would require bcfxml library
        import json
        
        report = self.generate_clash_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_path


def detect_clashes(elements: List[BIMElement], tolerance: float = 0.01) -> Dict:
    """
    Convenience function to detect clashes.
    
    Args:
        elements: List of BIM elements
        tolerance: Clash detection tolerance in meters
        
    Returns:
        Clash detection report
    """
    detector = BIMClashDetector(tolerance=tolerance)
    detector.detect_clashes(elements)
    return detector.generate_clash_report()
