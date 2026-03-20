"""
LAS/LAZ Point Cloud Parser (Task 14.3)

Parses LAS and LAZ (compressed) point cloud formats.
Supports LAS 1.0-1.4 formats with various point record types.

Dependencies:
- laspy (required)
- lazrs (for LAZ decompression, optional)
"""

import numpy as np
from pathlib import Path
from typing import Optional
import logging

from workers.parsers.base import (
    ParsedData,
    ParserResult,
    ParsedDataType,
    normalize_colors,
)

logger = logging.getLogger(__name__)

# LAS classification codes
LAS_CLASSIFICATIONS = {
    0: "Created, never classified",
    1: "Unclassified",
    2: "Ground",
    3: "Low Vegetation",
    4: "Medium Vegetation",
    5: "High Vegetation",
    6: "Building",
    7: "Low Point (noise)",
    8: "Reserved",
    9: "Water",
    10: "Rail",
    11: "Road Surface",
    12: "Reserved",
    13: "Wire - Guard (Shield)",
    14: "Wire - Conductor (Phase)",
    15: "Transmission Tower",
    16: "Wire-structure Connector",
    17: "Bridge Deck",
    18: "High Noise",
}


def parse_las(file_path: str) -> ParserResult:
    """
    Parse a LAS or LAZ point cloud file.
    
    Extracts:
    - Point positions (XYZ)
    - Colors (RGB if available)
    - Intensities
    - Classifications
    - Return numbers (for multi-return lidar)
    
    Args:
        file_path: Path to LAS/LAZ file
        
    Returns:
        ParserResult with parsed data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"LAS file not found: {file_path}")
    
    logger.info(f"Parsing LAS file: {file_path}")
    
    try:
        return _parse_with_laspy(file_path)
    except ImportError:
        logger.warning("laspy not available, using fallback parser")
        return _parse_las_fallback(file_path)
    except Exception as e:
        logger.warning(f"laspy failed: {e}, trying fallback")
        return _parse_las_fallback(file_path)


def _parse_with_laspy(file_path: str) -> ParserResult:
    """Parse LAS/LAZ using laspy library."""
    import laspy
    
    # Open LAS file (laspy handles LAZ automatically if lazrs is installed)
    las = laspy.read(file_path)
    
    n = len(las.points)
    logger.info(f"LAS file has {n} points")
    
    # Extract scaled positions
    positions = np.stack([
        las.x,
        las.y,
        las.z,
    ], axis=1).astype(np.float32)
    
    # Extract colors if available (LAS format 2, 3, 5, 7, 8, 10)
    colors = None
    if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
        try:
            colors = np.stack([
                np.array(las.red),
                np.array(las.green),
                np.array(las.blue),
            ], axis=1).astype(np.float32)
            # LAS colors are 16-bit (0-65535)
            if colors.max() > 255:
                colors = colors / 65535.0
            else:
                colors = colors / 255.0
        except Exception as e:
            logger.warning(f"Failed to extract colors: {e}")
    
    # Extract intensity
    intensities = None
    if hasattr(las, 'intensity'):
        try:
            intensities = np.array(las.intensity).astype(np.float32)
            # Normalize to 0-1
            max_intensity = intensities.max()
            if max_intensity > 0:
                intensities = intensities / max_intensity
        except Exception as e:
            logger.warning(f"Failed to extract intensity: {e}")
    
    # Extract classification
    classifications = None
    if hasattr(las, 'classification'):
        try:
            classifications = np.array(las.classification).astype(np.int32)
        except Exception as e:
            logger.warning(f"Failed to extract classification: {e}")
    
    # Generate colors from intensity if no RGB colors
    if colors is None and intensities is not None:
        # Grayscale from intensity
        colors = np.stack([intensities, intensities, intensities], axis=1)
    
    # Generate colors from classification if still no colors
    if colors is None and classifications is not None:
        colors = _classification_to_colors(classifications, n)
    
    # Extract metadata from header
    header = las.header
    metadata = {
        "las_version": f"{header.version.major}.{header.version.minor}",
        "point_format": header.point_format.id if hasattr(header.point_format, 'id') else None,
        "point_count": n,
        "scale": [header.scales[0], header.scales[1], header.scales[2]],
        "offset": [header.offsets[0], header.offsets[1], header.offsets[2]],
        "has_colors": colors is not None,
        "has_intensity": intensities is not None,
        "has_classification": classifications is not None,
    }
    
    # Add CRS info if available
    if hasattr(las, 'vlrs'):
        for vlr in las.vlrs:
            if vlr.record_id == 2112:  # WKT
                try:
                    metadata["crs_wkt"] = vlr.record_data.decode('utf-8', errors='ignore')
                except:
                    pass
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        intensities=intensities,
        classifications=classifications,
        data_type=ParsedDataType.POINT_CLOUD,
        point_count=n,
    )
    
    # Compute bounds
    warnings = []
    
    return ParserResult(
        data=parsed_data,
        format_name="LAS",
        format_version=metadata.get("las_version"),
        metadata=metadata,
        warnings=warnings,
    )


def _classification_to_colors(classifications: np.ndarray, n: int) -> np.ndarray:
    """Generate colors from LAS classification codes."""
    # Color map for common classifications
    color_map = {
        0: [0.5, 0.5, 0.5],  # Unclassified - gray
        1: [0.5, 0.5, 0.5],  # Unclassified - gray
        2: [0.6, 0.4, 0.2],  # Ground - brown
        3: [0.4, 0.8, 0.4],  # Low vegetation - light green
        4: [0.2, 0.6, 0.2],  # Medium vegetation - medium green
        5: [0.0, 0.4, 0.0],  # High vegetation - dark green
        6: [0.8, 0.2, 0.2],  # Building - red
        7: [0.3, 0.3, 0.3],  # Low point - dark gray
        9: [0.2, 0.4, 0.8],  # Water - blue
        10: [0.4, 0.4, 0.4], # Rail - gray
        11: [0.3, 0.3, 0.3], # Road - dark gray
        17: [0.6, 0.6, 0.6], # Bridge - light gray
    }
    
    default_color = [0.5, 0.5, 0.5]
    colors = np.zeros((n, 3), dtype=np.float32)
    
    for class_id, color in color_map.items():
        mask = classifications == class_id
        colors[mask] = color
    
    # Handle unknown classifications
    unknown_mask = ~np.isin(classifications, list(color_map.keys()))
    colors[unknown_mask] = default_color
    
    return colors


def _parse_las_fallback(file_path: str) -> ParserResult:
    """
    Fallback LAS parser without laspy dependency.
    
    Supports basic LAS 1.2 format (most common).
    Does NOT support LAZ compression.
    """
    import struct
    
    path = Path(file_path)
    if path.suffix.lower() == '.laz':
        raise ImportError("LAZ decompression requires laspy with lazrs. Install with: pip install laspy[lazrs]")
    
    with open(file_path, 'rb') as f:
        # Read LAS header
        signature = f.read(4)
        if signature != b'LASF':
            raise ValueError("Invalid LAS file signature")
        
        # Skip to header size
        f.seek(94)
        header_size = struct.unpack('<H', f.read(2))[0]
        
        # Read point offset
        f.seek(96)
        point_offset = struct.unpack('<I', f.read(4))[0]
        
        # Skip VLRs count
        f.seek(100)
        num_vlrs = struct.unpack('<I', f.read(4))[0]
        
        # Point format
        point_format = struct.unpack('<B', f.read(1))[0]
        
        # Point record length
        point_record_length = struct.unpack('<H', f.read(2))[0]
        
        # Number of points (32-bit for LAS 1.2, may need 64-bit for 1.4)
        f.seek(107)
        point_count = struct.unpack('<I', f.read(4))[0]
        
        # Scale and offset
        f.seek(131)
        scale_x, scale_y, scale_z = struct.unpack('<ddd', f.read(24))
        offset_x, offset_y, offset_z = struct.unpack('<ddd', f.read(24))
        
        # Seek to point data
        f.seek(point_offset)
        
        # Read point records
        n = point_count
        positions = np.zeros((n, 3), dtype=np.float32)
        intensities = np.zeros(n, dtype=np.float32)
        classifications = np.zeros(n, dtype=np.int32)
        colors = None
        
        # Check if format has RGB (formats 2, 3, 5, 7, 8, 10)
        has_rgb = point_format in [2, 3, 5, 7, 8, 10]
        if has_rgb:
            colors = np.zeros((n, 3), dtype=np.float32)
        
        for i in range(n):
            record = f.read(point_record_length)
            
            # XYZ (always first 12 bytes as int32)
            x, y, z = struct.unpack_from('<iii', record, 0)
            positions[i, 0] = x * scale_x + offset_x
            positions[i, 1] = y * scale_y + offset_y
            positions[i, 2] = z * scale_z + offset_z
            
            # Intensity (bytes 12-13)
            intensity = struct.unpack_from('<H', record, 12)[0]
            intensities[i] = intensity / 65535.0
            
            # Classification (byte 15 for format 0-5, varies for 6+)
            if point_format <= 5:
                classifications[i] = record[15]
            
            # RGB (varies by format)
            if has_rgb:
                if point_format in [2, 3]:
                    rgb_offset = 20
                elif point_format == 5:
                    rgb_offset = 28
                else:
                    rgb_offset = 20  # Default
                
                if rgb_offset + 6 <= len(record):
                    r, g, b = struct.unpack_from('<HHH', record, rgb_offset)
                    colors[i, 0] = r / 65535.0
                    colors[i, 1] = g / 65535.0
                    colors[i, 2] = b / 65535.0
    
    # Generate colors from classification if no RGB
    if colors is None:
        colors = _classification_to_colors(classifications, n)
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        intensities=intensities,
        classifications=classifications,
        data_type=ParsedDataType.POINT_CLOUD,
        point_count=n,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="LAS",
        format_version="1.2",
        metadata={
            "parser": "fallback",
            "point_format": point_format,
            "point_count": n,
            "scale": [scale_x, scale_y, scale_z],
            "offset": [offset_x, offset_y, offset_z],
        },
        warnings=["Using fallback parser - some features may not be supported"]
    )
