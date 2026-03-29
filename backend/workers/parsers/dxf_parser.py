"""
DXF Parser for 2D Overlay Support
Parses DXF format for CAD linework.
Extracts lines, polylines, circles, arcs, and layers.
"""
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DXFEntity:
    """DXF entity (line, polyline, circle, arc)"""
    entity_type: str  # 'LINE', 'POLYLINE', 'CIRCLE', 'ARC'
    layer: str
    color: int
    points: List[Tuple[float, float, float]]  # 3D points
    radius: Optional[float] = None  # For circles/arcs
    start_angle: Optional[float] = None  # For arcs
    end_angle: Optional[float] = None  # For arcs


class DXFParser:
    """
    Parser for DXF (Drawing Exchange Format) files.
    Extracts 2D linework for overlay on 3D scenes.
    """
    
    def __init__(self):
        self.entities = []
        self.layers = {}
    
    def parse(self, file_path: str) -> Dict:
        """
        Parse DXF file and extract entities.
        
        Args:
            file_path: Path to DXF file
            
        Returns:
            Dictionary with parsed entities
        """
        self.entities = []
        self.layers = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Parse DXF structure
            self._parse_dxf_content(lines)
            
            return {
                'entity_count': len(self.entities),
                'entities': self.entities,
                'layers': list(self.layers.keys()),
                'format': 'dxf'
            }
        
        except Exception as e:
            return {
                'entity_count': 0,
                'entities': [],
                'layers': [],
                'format': 'dxf',
                'error': str(e)
            }
    
    def _parse_dxf_content(self, lines: List[str]):
        """Parse DXF file content"""
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for entity sections
            if line == '0':
                i += 1
                if i < len(lines):
                    entity_type = lines[i].strip()
                    
                    if entity_type == 'LINE':
                        entity, i = self._parse_line(lines, i)
                        if entity:
                            self.entities.append(entity)
                    
                    elif entity_type == 'LWPOLYLINE' or entity_type == 'POLYLINE':
                        entity, i = self._parse_polyline(lines, i)
                        if entity:
                            self.entities.append(entity)
                    
                    elif entity_type == 'CIRCLE':
                        entity, i = self._parse_circle(lines, i)
                        if entity:
                            self.entities.append(entity)
                    
                    elif entity_type == 'ARC':
                        entity, i = self._parse_arc(lines, i)
                        if entity:
                            self.entities.append(entity)
            
            i += 1
    
    def _parse_line(self, lines: List[str], start_idx: int) -> Tuple[Optional[DXFEntity], int]:
        """Parse LINE entity"""
        i = start_idx + 1
        layer = '0'
        color = 7  # Default white
        x1, y1, z1 = 0.0, 0.0, 0.0
        x2, y2, z2 = 0.0, 0.0, 0.0
        
        while i < len(lines):
            code = lines[i].strip()
            i += 1
            if i >= len(lines):
                break
            value = lines[i].strip()
            
            if code == '0':  # Next entity
                i -= 1
                break
            elif code == '8':  # Layer
                layer = value
                self.layers[layer] = True
            elif code == '62':  # Color
                color = int(value)
            elif code == '10':  # Start X
                x1 = float(value)
            elif code == '20':  # Start Y
                y1 = float(value)
            elif code == '30':  # Start Z
                z1 = float(value)
            elif code == '11':  # End X
                x2 = float(value)
            elif code == '21':  # End Y
                y2 = float(value)
            elif code == '31':  # End Z
                z2 = float(value)
            
            i += 1
        
        entity = DXFEntity(
            entity_type='LINE',
            layer=layer,
            color=color,
            points=[(x1, y1, z1), (x2, y2, z2)]
        )
        
        return entity, i
    
    def _parse_polyline(self, lines: List[str], start_idx: int) -> Tuple[Optional[DXFEntity], int]:
        """Parse POLYLINE/LWPOLYLINE entity"""
        i = start_idx + 1
        layer = '0'
        color = 7
        points = []
        x, y, z = 0.0, 0.0, 0.0
        
        while i < len(lines):
            code = lines[i].strip()
            i += 1
            if i >= len(lines):
                break
            value = lines[i].strip()
            
            if code == '0':  # Next entity
                i -= 1
                break
            elif code == '8':  # Layer
                layer = value
                self.layers[layer] = True
            elif code == '62':  # Color
                color = int(value)
            elif code == '10':  # Vertex X
                x = float(value)
            elif code == '20':  # Vertex Y
                y = float(value)
                points.append((x, y, z))
            elif code == '30':  # Vertex Z
                z = float(value)
                if points:
                    points[-1] = (points[-1][0], points[-1][1], z)
            
            i += 1
        
        if len(points) < 2:
            return None, i
        
        entity = DXFEntity(
            entity_type='POLYLINE',
            layer=layer,
            color=color,
            points=points
        )
        
        return entity, i
    
    def _parse_circle(self, lines: List[str], start_idx: int) -> Tuple[Optional[DXFEntity], int]:
        """Parse CIRCLE entity"""
        i = start_idx + 1
        layer = '0'
        color = 7
        cx, cy, cz = 0.0, 0.0, 0.0
        radius = 1.0
        
        while i < len(lines):
            code = lines[i].strip()
            i += 1
            if i >= len(lines):
                break
            value = lines[i].strip()
            
            if code == '0':  # Next entity
                i -= 1
                break
            elif code == '8':  # Layer
                layer = value
                self.layers[layer] = True
            elif code == '62':  # Color
                color = int(value)
            elif code == '10':  # Center X
                cx = float(value)
            elif code == '20':  # Center Y
                cy = float(value)
            elif code == '30':  # Center Z
                cz = float(value)
            elif code == '40':  # Radius
                radius = float(value)
            
            i += 1
        
        entity = DXFEntity(
            entity_type='CIRCLE',
            layer=layer,
            color=color,
            points=[(cx, cy, cz)],
            radius=radius
        )
        
        return entity, i
    
    def _parse_arc(self, lines: List[str], start_idx: int) -> Tuple[Optional[DXFEntity], int]:
        """Parse ARC entity"""
        i = start_idx + 1
        layer = '0'
        color = 7
        cx, cy, cz = 0.0, 0.0, 0.0
        radius = 1.0
        start_angle = 0.0
        end_angle = 360.0
        
        while i < len(lines):
            code = lines[i].strip()
            i += 1
            if i >= len(lines):
                break
            value = lines[i].strip()
            
            if code == '0':  # Next entity
                i -= 1
                break
            elif code == '8':  # Layer
                layer = value
                self.layers[layer] = True
            elif code == '62':  # Color
                color = int(value)
            elif code == '10':  # Center X
                cx = float(value)
            elif code == '20':  # Center Y
                cy = float(value)
            elif code == '30':  # Center Z
                cz = float(value)
            elif code == '40':  # Radius
                radius = float(value)
            elif code == '50':  # Start angle
                start_angle = float(value)
            elif code == '51':  # End angle
                end_angle = float(value)
            
            i += 1
        
        entity = DXFEntity(
            entity_type='ARC',
            layer=layer,
            color=color,
            points=[(cx, cy, cz)],
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle
        )
        
        return entity, i
    
    def to_three_js_format(self) -> Dict:
        """
        Convert DXF entities to Three.js-compatible format.
        
        Returns:
            Dictionary with line segments for rendering
        """
        line_segments = []
        
        for entity in self.entities:
            if entity.entity_type == 'LINE':
                line_segments.append({
                    'type': 'line',
                    'points': entity.points,
                    'layer': entity.layer,
                    'color': self._dxf_color_to_hex(entity.color)
                })
            
            elif entity.entity_type == 'POLYLINE':
                line_segments.append({
                    'type': 'polyline',
                    'points': entity.points,
                    'layer': entity.layer,
                    'color': self._dxf_color_to_hex(entity.color)
                })
            
            elif entity.entity_type == 'CIRCLE':
                # Approximate circle with line segments
                center = entity.points[0]
                circle_points = self._circle_to_points(center, entity.radius, 32)
                line_segments.append({
                    'type': 'circle',
                    'points': circle_points,
                    'layer': entity.layer,
                    'color': self._dxf_color_to_hex(entity.color)
                })
            
            elif entity.entity_type == 'ARC':
                # Approximate arc with line segments
                center = entity.points[0]
                arc_points = self._arc_to_points(
                    center, entity.radius,
                    entity.start_angle, entity.end_angle, 32
                )
                line_segments.append({
                    'type': 'arc',
                    'points': arc_points,
                    'layer': entity.layer,
                    'color': self._dxf_color_to_hex(entity.color)
                })
        
        return {
            'line_segments': line_segments,
            'layers': list(self.layers.keys())
        }
    
    def _circle_to_points(self, center: Tuple[float, float, float], 
                         radius: float, segments: int) -> List[Tuple[float, float, float]]:
        """Convert circle to line segments"""
        points = []
        for i in range(segments + 1):
            angle = (i / segments) * 2 * np.pi
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            z = center[2]
            points.append((x, y, z))
        return points
    
    def _arc_to_points(self, center: Tuple[float, float, float], 
                      radius: float, start_angle: float, end_angle: float,
                      segments: int) -> List[Tuple[float, float, float]]:
        """Convert arc to line segments"""
        points = []
        start_rad = np.radians(start_angle)
        end_rad = np.radians(end_angle)
        
        # Handle angle wrapping
        if end_rad < start_rad:
            end_rad += 2 * np.pi
        
        angle_range = end_rad - start_rad
        
        for i in range(segments + 1):
            angle = start_rad + (i / segments) * angle_range
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            z = center[2]
            points.append((x, y, z))
        return points
    
    def _dxf_color_to_hex(self, color_index: int) -> str:
        """Convert DXF color index to hex color"""
        # Simplified DXF color palette
        colors = {
            1: '#FF0000',  # Red
            2: '#FFFF00',  # Yellow
            3: '#00FF00',  # Green
            4: '#00FFFF',  # Cyan
            5: '#0000FF',  # Blue
            6: '#FF00FF',  # Magenta
            7: '#FFFFFF',  # White
            8: '#808080',  # Gray
        }
        return colors.get(color_index, '#FFFFFF')


def get_dxf_parser():
    """Get DXF parser instance"""
    return DXFParser()
