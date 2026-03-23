"""
Camera Metadata Parser
Parses camera data from CSV, XML, TXT, FBX, and ABC formats.
Extracts camera positions, orientations, and intrinsics.
Supports up to 10,000 camera positions.
"""
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import xml.etree.ElementTree as ET
import struct
from dataclasses import dataclass


@dataclass
class CameraData:
    """Camera data structure"""
    frame_id: int
    position: np.ndarray  # [x, y, z]
    orientation: np.ndarray  # Quaternion [w, x, y, z] or Euler [rx, ry, rz]
    intrinsics: Optional[Dict[str, float]] = None  # focal_length, cx, cy, etc.
    timestamp: Optional[float] = None


class CameraParser:
    """
    Parser for camera metadata from various formats.
    Supports: CSV, XML, TXT, FBX camera tracks, ABC camera tracks
    """
    
    def __init__(self):
        self.max_cameras = 10000
    
    def parse(self, file_path: str) -> Dict:
        """
        Parse camera data from file.
        
        Args:
            file_path: Path to camera data file
            
        Returns:
            Dictionary with camera data
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return self.parse_csv(file_path)
        elif suffix == '.xml':
            return self.parse_xml(file_path)
        elif suffix == '.txt':
            return self.parse_txt(file_path)
        elif suffix == '.fbx':
            return self.parse_fbx(file_path)
        elif suffix == '.abc':
            return self.parse_abc(file_path)
        else:
            raise ValueError(f"Unsupported camera file format: {suffix}")
    
    def parse_csv(self, file_path: str) -> Dict:
        """
        Parse CSV camera data.
        Expected format: frame, x, y, z, qw, qx, qy, qz, [focal_length, cx, cy]
        """
        cameras = []
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if i >= self.max_cameras:
                    break
                
                # Parse position
                position = np.array([
                    float(row.get('x', row.get('pos_x', 0))),
                    float(row.get('y', row.get('pos_y', 0))),
                    float(row.get('z', row.get('pos_z', 0)))
                ])
                
                # Parse orientation (quaternion or Euler)
                if 'qw' in row:
                    # Quaternion format
                    orientation = np.array([
                        float(row['qw']),
                        float(row['qx']),
                        float(row['qy']),
                        float(row['qz'])
                    ])
                elif 'rx' in row:
                    # Euler angles format
                    orientation = np.array([
                        float(row['rx']),
                        float(row['ry']),
                        float(row['rz'])
                    ])
                else:
                    # Default identity orientation
                    orientation = np.array([1, 0, 0, 0])
                
                # Parse intrinsics if available
                intrinsics = None
                if 'focal_length' in row:
                    intrinsics = {
                        'focal_length': float(row['focal_length']),
                        'cx': float(row.get('cx', 0)),
                        'cy': float(row.get('cy', 0))
                    }
                
                camera = CameraData(
                    frame_id=int(row.get('frame', i)),
                    position=position,
                    orientation=orientation,
                    intrinsics=intrinsics,
                    timestamp=float(row['timestamp']) if 'timestamp' in row else None
                )
                
                cameras.append(camera)
        
        return {
            'camera_count': len(cameras),
            'cameras': cameras,
            'format': 'csv'
        }
    
    def parse_xml(self, file_path: str) -> Dict:
        """
        Parse XML camera data.
        Expected structure:
        <cameras>
            <camera frame="0">
                <position x="0" y="0" z="0"/>
                <orientation qw="1" qx="0" qy="0" qz="0"/>
                <intrinsics focal_length="800" cx="320" cy="240"/>
            </camera>
        </cameras>
        """
        cameras = []
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for i, camera_elem in enumerate(root.findall('camera')):
            if i >= self.max_cameras:
                break
            
            # Parse position
            pos_elem = camera_elem.find('position')
            position = np.array([
                float(pos_elem.get('x', 0)),
                float(pos_elem.get('y', 0)),
                float(pos_elem.get('z', 0))
            ])
            
            # Parse orientation
            orient_elem = camera_elem.find('orientation')
            if orient_elem is not None:
                if 'qw' in orient_elem.attrib:
                    orientation = np.array([
                        float(orient_elem.get('qw')),
                        float(orient_elem.get('qx')),
                        float(orient_elem.get('qy')),
                        float(orient_elem.get('qz'))
                    ])
                else:
                    orientation = np.array([
                        float(orient_elem.get('rx', 0)),
                        float(orient_elem.get('ry', 0)),
                        float(orient_elem.get('rz', 0))
                    ])
            else:
                orientation = np.array([1, 0, 0, 0])
            
            # Parse intrinsics
            intrinsics = None
            intr_elem = camera_elem.find('intrinsics')
            if intr_elem is not None:
                intrinsics = {
                    'focal_length': float(intr_elem.get('focal_length', 800)),
                    'cx': float(intr_elem.get('cx', 0)),
                    'cy': float(intr_elem.get('cy', 0))
                }
            
            camera = CameraData(
                frame_id=int(camera_elem.get('frame', i)),
                position=position,
                orientation=orientation,
                intrinsics=intrinsics
            )
            
            cameras.append(camera)
        
        return {
            'camera_count': len(cameras),
            'cameras': cameras,
            'format': 'xml'
        }
    
    def parse_txt(self, file_path: str) -> Dict:
        """
        Parse TXT camera data.
        Expected format (space-separated):
        frame x y z qw qx qy qz [focal_length cx cy]
        """
        cameras = []
        
        with open(file_path, 'r') as f:
            for i, line in enumerate(f):
                if i >= self.max_cameras:
                    break
                
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) < 8:
                    continue
                
                frame_id = int(parts[0])
                position = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
                orientation = np.array([float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7])])
                
                intrinsics = None
                if len(parts) >= 11:
                    intrinsics = {
                        'focal_length': float(parts[8]),
                        'cx': float(parts[9]),
                        'cy': float(parts[10])
                    }
                
                camera = CameraData(
                    frame_id=frame_id,
                    position=position,
                    orientation=orientation,
                    intrinsics=intrinsics
                )
                
                cameras.append(camera)
        
        return {
            'camera_count': len(cameras),
            'cameras': cameras,
            'format': 'txt'
        }
    
    def parse_fbx(self, file_path: str) -> Dict:
        """
        Parse FBX camera tracks.
        Uses trimesh to extract camera animation data.
        """
        try:
            import trimesh
        except ImportError:
            return self._fallback_fbx_parse(file_path)
        
        try:
            scene = trimesh.load(file_path)
            cameras = []
            
            # Extract camera nodes
            if hasattr(scene, 'graph'):
                camera_nodes = [node for node in scene.graph.nodes if 'camera' in node.lower()]
                
                for i, node_name in enumerate(camera_nodes[:self.max_cameras]):
                    # Get transform
                    transform = scene.graph.get(node_name)[0]
                    
                    # Extract position
                    position = transform[:3, 3]
                    
                    # Extract orientation (convert rotation matrix to quaternion)
                    rotation_matrix = transform[:3, :3]
                    orientation = self._matrix_to_quaternion(rotation_matrix)
                    
                    camera = CameraData(
                        frame_id=i,
                        position=position,
                        orientation=orientation
                    )
                    
                    cameras.append(camera)
            
            return {
                'camera_count': len(cameras),
                'cameras': cameras,
                'format': 'fbx'
            }
        
        except Exception as e:
            print(f"FBX parsing error: {e}")
            return self._fallback_fbx_parse(file_path)
    
    def _fallback_fbx_parse(self, file_path: str) -> Dict:
        """Fallback FBX parser"""
        return {
            'camera_count': 0,
            'cameras': [],
            'format': 'fbx',
            'error': 'FBX parsing not fully supported, install trimesh'
        }
    
    def parse_abc(self, file_path: str) -> Dict:
        """
        Parse Alembic (ABC) camera tracks.
        ABC is a complex format - this is a simplified parser.
        """
        # Alembic requires specialized library (alembic-python)
        # For now, provide a placeholder
        return {
            'camera_count': 0,
            'cameras': [],
            'format': 'abc',
            'error': 'ABC parsing requires alembic library'
        }
    
    def _matrix_to_quaternion(self, matrix: np.ndarray) -> np.ndarray:
        """Convert 3x3 rotation matrix to quaternion [w, x, y, z]"""
        trace = np.trace(matrix)
        
        if trace > 0:
            s = 0.5 / np.sqrt(trace + 1.0)
            w = 0.25 / s
            x = (matrix[2, 1] - matrix[1, 2]) * s
            y = (matrix[0, 2] - matrix[2, 0]) * s
            z = (matrix[1, 0] - matrix[0, 1]) * s
        else:
            if matrix[0, 0] > matrix[1, 1] and matrix[0, 0] > matrix[2, 2]:
                s = 2.0 * np.sqrt(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2])
                w = (matrix[2, 1] - matrix[1, 2]) / s
                x = 0.25 * s
                y = (matrix[0, 1] + matrix[1, 0]) / s
                z = (matrix[0, 2] + matrix[2, 0]) / s
            elif matrix[1, 1] > matrix[2, 2]:
                s = 2.0 * np.sqrt(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2])
                w = (matrix[0, 2] - matrix[2, 0]) / s
                x = (matrix[0, 1] + matrix[1, 0]) / s
                y = 0.25 * s
                z = (matrix[1, 2] + matrix[2, 1]) / s
            else:
                s = 2.0 * np.sqrt(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1])
                w = (matrix[1, 0] - matrix[0, 1]) / s
                x = (matrix[0, 2] + matrix[2, 0]) / s
                y = (matrix[1, 2] + matrix[2, 1]) / s
                z = 0.25 * s
        
        return np.array([w, x, y, z])
    
    def export_to_colmap(self, cameras: List[CameraData], output_dir: str):
        """
        Export camera data to COLMAP format.
        Creates cameras.txt and images.txt files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write cameras.txt
        cameras_file = output_path / "cameras.txt"
        with open(cameras_file, 'w') as f:
            f.write("# Camera list with one line of data per camera:\n")
            f.write("#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
            
            # Assume single camera model for all frames
            if cameras and cameras[0].intrinsics:
                focal = cameras[0].intrinsics['focal_length']
                cx = cameras[0].intrinsics.get('cx', 320)
                cy = cameras[0].intrinsics.get('cy', 240)
            else:
                focal, cx, cy = 800, 320, 240
            
            f.write(f"1 PINHOLE 640 480 {focal} {focal} {cx} {cy}\n")
        
        # Write images.txt
        images_file = output_path / "images.txt"
        with open(images_file, 'w') as f:
            f.write("# Image list with two lines of data per image:\n")
            f.write("#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
            f.write("#   POINTS2D[] as (X, Y, POINT3D_ID)\n")
            
            for cam in cameras:
                quat = cam.orientation
                pos = cam.position
                f.write(f"{cam.frame_id} {quat[0]} {quat[1]} {quat[2]} {quat[3]} ")
                f.write(f"{pos[0]} {pos[1]} {pos[2]} 1 frame_{cam.frame_id:04d}.jpg\n")
                f.write("\n")  # Empty line for POINTS2D
        
        return {
            'cameras_file': str(cameras_file),
            'images_file': str(images_file)
        }


# Register parser
def get_camera_parser():
    """Get camera parser instance"""
    return CameraParser()
