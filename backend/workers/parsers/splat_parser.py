"""
Gaussian Splatting (.splat) Parser (Task 14.6)

Parses custom Gaussian Splatting binary format used by various viewers.

The .splat format is a compact binary format storing:
- Position (3 floats)
- Scale (3 floats, log-scale)
- Rotation (4 floats, quaternion)
- Opacity (1 float, logit)
- Color/SH coefficients

Different implementations use slightly different layouts.
This parser supports common variants.
"""

import numpy as np
from pathlib import Path
import struct
import logging

from workers.parsers.base import (
    ParsedData,
    ParserResult,
    ParsedDataType,
)

logger = logging.getLogger(__name__)


# Common .splat file layouts (bytes per Gaussian)
SPLAT_LAYOUTS = {
    # Standard layout: pos(12) + scale(12) + rot(16) + opacity(4) + color(12) = 56 bytes
    56: {
        'pos': (0, 3, 'f'),
        'scale': (12, 3, 'f'),
        'rot': (24, 4, 'f'),
        'opacity': (40, 1, 'f'),
        'color': (44, 3, 'f'),
    },
    # Compact layout: pos(12) + scale(12) + rot(16) + opacity(4) = 44 bytes (no color)
    44: {
        'pos': (0, 3, 'f'),
        'scale': (12, 3, 'f'),
        'rot': (24, 4, 'f'),
        'opacity': (40, 1, 'f'),
    },
    # Extended layout with SH: pos(12) + scale(12) + rot(16) + opacity(4) + sh(48) = 92 bytes
    92: {
        'pos': (0, 3, 'f'),
        'scale': (12, 3, 'f'),
        'rot': (24, 4, 'f'),
        'opacity': (40, 1, 'f'),
        'sh': (44, 12, 'f'),  # 12 floats = 4 RGB * 3 SH bands
    },
    # Antimatter15 layout: pos(12) + rot(4, u8) + scale(4, u8) + rgba(4, u8) = 24 bytes
    24: {
        'pos': (0, 3, 'f'),
        'rot_u8': (12, 4, 'B'),
        'scale_u8': (16, 4, 'B'),  # 3 scale + 1 unused or opacity
        'rgba_u8': (20, 4, 'B'),
    },
    # Alternative compact: pos(12) + scale(6, f16) + rot(8, f16) + opacity(2, f16) + color(6, f16) = 34 bytes
    34: {
        'pos': (0, 3, 'f'),
        'scale_f16': (12, 3, 'e'),
        'rot_f16': (18, 4, 'e'),
        'opacity_f16': (26, 1, 'e'),
        'color_f16': (28, 3, 'e'),
    },
    # 32-byte compact layout (common web viewer format)
    32: {
        'pos': (0, 3, 'f'),
        'scale_exp': (12, 3, 'B'),  # Exponent only
        'rot_u8': (15, 4, 'B'),
        'opacity_u8': (19, 1, 'B'),
        'color_u8': (20, 3, 'B'),
        'padding': (23, 9, 'x'),
    },
}


def parse_splat(file_path: str) -> ParserResult:
    """
    Parse a .splat Gaussian Splatting file.
    
    Automatically detects the file layout based on file size and content.
    
    Args:
        file_path: Path to .splat file
        
    Returns:
        ParserResult with Gaussian data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SPLAT file not found: {file_path}")
    
    logger.info(f"Parsing SPLAT file: {file_path}")
    
    file_size = path.stat().st_size
    
    # Try to detect layout from file size
    layout, n_gaussians = _detect_layout(file_size)
    
    if layout is None:
        logger.warning(f"Unknown SPLAT layout for file size {file_size}, trying common formats")
        layout, n_gaussians = _try_parse_header(file_path)
    
    logger.info(f"Detected layout: {layout} bytes per Gaussian, {n_gaussians} Gaussians")
    
    # Parse based on detected layout
    with open(file_path, 'rb') as f:
        data = f.read()
    
    if layout == 24:
        return _parse_antimatter_layout(data, n_gaussians)
    elif layout == 32:
        return _parse_compact32_layout(data, n_gaussians)
    elif layout == 34:
        return _parse_f16_layout(data, n_gaussians)
    else:
        return _parse_standard_layout(data, layout, n_gaussians)


def _detect_layout(file_size: int) -> tuple:
    """Detect SPLAT file layout from file size."""
    for layout_size in sorted(SPLAT_LAYOUTS.keys(), reverse=True):
        if file_size % layout_size == 0:
            n_gaussians = file_size // layout_size
            if n_gaussians > 0:
                return layout_size, n_gaussians
    
    # Check for header (some formats have a header)
    for layout_size in SPLAT_LAYOUTS.keys():
        for header_size in [0, 4, 8, 12, 16]:
            adjusted_size = file_size - header_size
            if adjusted_size > 0 and adjusted_size % layout_size == 0:
                n_gaussians = adjusted_size // layout_size
                if 100 < n_gaussians < 100_000_000:  # Reasonable range
                    return layout_size, n_gaussians
    
    return None, 0


def _try_parse_header(file_path: str) -> tuple:
    """Try to parse file header for layout info."""
    with open(file_path, 'rb') as f:
        # Check for magic number or count at start
        header = f.read(16)
        
        # Some formats store count as first 4 bytes
        count = struct.unpack('<I', header[:4])[0]
        
        file_size = Path(file_path).stat().st_size
        remaining = file_size - 4
        
        for layout_size in SPLAT_LAYOUTS.keys():
            if remaining == count * layout_size:
                return layout_size, count
        
        # Try without header
        for layout_size in SPLAT_LAYOUTS.keys():
            if file_size % layout_size == 0:
                return layout_size, file_size // layout_size
    
    # Default to 56-byte layout
    return 56, file_size // 56


def _parse_standard_layout(data: bytes, layout_size: int, n: int) -> ParserResult:
    """Parse standard float-based SPLAT layouts (44, 56, 92 bytes)."""
    layout = SPLAT_LAYOUTS[layout_size]
    
    positions = np.zeros((n, 3), dtype=np.float32)
    scales = np.zeros((n, 3), dtype=np.float32)
    rotations = np.zeros((n, 4), dtype=np.float32)
    opacities = np.zeros((n, 1), dtype=np.float32)
    colors = None
    sh_coeffs = None
    
    for i in range(n):
        offset = i * layout_size
        
        # Position
        pos_offset, pos_count, pos_fmt = layout['pos']
        positions[i] = struct.unpack_from(f'<{pos_count}{pos_fmt}', data, offset + pos_offset)
        
        # Scale
        scale_offset, scale_count, scale_fmt = layout['scale']
        scales[i] = struct.unpack_from(f'<{scale_count}{scale_fmt}', data, offset + scale_offset)
        
        # Rotation
        rot_offset, rot_count, rot_fmt = layout['rot']
        rotations[i] = struct.unpack_from(f'<{rot_count}{rot_fmt}', data, offset + rot_offset)
        
        # Opacity
        op_offset, op_count, op_fmt = layout['opacity']
        opacities[i] = struct.unpack_from(f'<{op_count}{op_fmt}', data, offset + op_offset)
    
    # Colors (optional)
    if 'color' in layout:
        colors = np.zeros((n, 3), dtype=np.float32)
        for i in range(n):
            offset = i * layout_size
            col_offset, col_count, col_fmt = layout['color']
            colors[i] = struct.unpack_from(f'<{col_count}{col_fmt}', data, offset + col_offset)
    
    # SH coefficients (optional)
    if 'sh' in layout:
        sh_offset, sh_count, sh_fmt = layout['sh']
        sh_coeffs = np.zeros((n, sh_count), dtype=np.float32)
        for i in range(n):
            offset = i * layout_size
            sh_coeffs[i] = struct.unpack_from(f'<{sh_count}{sh_fmt}', data, offset + sh_offset)
    
    # Process Gaussian parameters
    # Check if scales are log-scaled (negative values indicate log-scale)
    if scales.min() < 0:
        scales = np.exp(scales)
    
    # Check if opacities are logit-scaled
    if opacities.min() < 0 or opacities.max() > 1.0:
        opacities = 1.0 / (1.0 + np.exp(-opacities))
    
    # Normalize rotations
    norms = np.linalg.norm(rotations, axis=1, keepdims=True)
    norms[norms == 0] = 1
    rotations = rotations / norms
    
    # Generate colors from SH if no direct colors
    if colors is None and sh_coeffs is not None:
        SH_C0 = 0.28209479177387814
        colors = sh_coeffs[:, :3] * SH_C0 + 0.5
        colors = np.clip(colors, 0, 1)
    elif colors is None:
        colors = np.ones((n, 3), dtype=np.float32) * 0.5
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        scales=scales,
        rotations=rotations,
        opacities=opacities,
        sh_coeffs=sh_coeffs,
        data_type=ParsedDataType.GAUSSIAN,
        is_gaussian=True,
        point_count=n,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="SPLAT",
        metadata={
            "layout_bytes": layout_size,
            "gaussian_count": n,
            "has_sh": sh_coeffs is not None,
        }
    )


def _parse_antimatter_layout(data: bytes, n: int) -> ParserResult:
    """Parse Antimatter15-style 24-byte compact layout."""
    layout_size = 24
    
    positions = np.zeros((n, 3), dtype=np.float32)
    scales = np.zeros((n, 3), dtype=np.float32)
    rotations = np.zeros((n, 4), dtype=np.float32)
    opacities = np.zeros((n, 1), dtype=np.float32)
    colors = np.zeros((n, 3), dtype=np.float32)
    
    for i in range(n):
        offset = i * layout_size
        
        # Position (3 floats)
        positions[i] = struct.unpack_from('<3f', data, offset)
        
        # Rotation (4 uint8 -> normalized quaternion)
        rot_u8 = struct.unpack_from('<4B', data, offset + 12)
        rotations[i] = (np.array(rot_u8, dtype=np.float32) - 128) / 128.0
        
        # Scale (3 uint8 -> log-scale)
        scale_u8 = struct.unpack_from('<4B', data, offset + 16)
        scales[i] = np.exp((np.array(scale_u8[:3], dtype=np.float32) - 128) / 16.0)
        
        # RGBA (4 uint8)
        rgba = struct.unpack_from('<4B', data, offset + 20)
        colors[i] = np.array(rgba[:3], dtype=np.float32) / 255.0
        opacities[i] = rgba[3] / 255.0
    
    # Normalize rotations
    norms = np.linalg.norm(rotations, axis=1, keepdims=True)
    norms[norms == 0] = 1
    rotations = rotations / norms
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        scales=scales,
        rotations=rotations,
        opacities=opacities,
        data_type=ParsedDataType.GAUSSIAN,
        is_gaussian=True,
        point_count=n,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="SPLAT",
        format_version="antimatter15",
        metadata={
            "layout_bytes": layout_size,
            "gaussian_count": n,
            "compact_format": True,
        }
    )


def _parse_compact32_layout(data: bytes, n: int) -> ParserResult:
    """Parse 32-byte compact web viewer layout."""
    layout_size = 32
    
    positions = np.zeros((n, 3), dtype=np.float32)
    scales = np.zeros((n, 3), dtype=np.float32)
    rotations = np.zeros((n, 4), dtype=np.float32)
    opacities = np.zeros((n, 1), dtype=np.float32)
    colors = np.zeros((n, 3), dtype=np.float32)
    
    for i in range(n):
        offset = i * layout_size
        
        # Position (3 floats)
        positions[i] = struct.unpack_from('<3f', data, offset)
        
        # Scale exponents (3 bytes)
        scale_exp = struct.unpack_from('<3B', data, offset + 12)
        scales[i] = np.exp((np.array(scale_exp, dtype=np.float32) - 128) / 32.0)
        
        # Rotation (4 bytes)
        rot_u8 = struct.unpack_from('<4B', data, offset + 15)
        rotations[i] = (np.array(rot_u8, dtype=np.float32) - 128) / 128.0
        
        # Opacity (1 byte)
        opacities[i] = struct.unpack_from('<B', data, offset + 19)[0] / 255.0
        
        # Color (3 bytes)
        color_u8 = struct.unpack_from('<3B', data, offset + 20)
        colors[i] = np.array(color_u8, dtype=np.float32) / 255.0
    
    # Normalize rotations
    norms = np.linalg.norm(rotations, axis=1, keepdims=True)
    norms[norms == 0] = 1
    rotations = rotations / norms
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        scales=scales,
        rotations=rotations,
        opacities=opacities,
        data_type=ParsedDataType.GAUSSIAN,
        is_gaussian=True,
        point_count=n,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="SPLAT",
        format_version="compact32",
        metadata={
            "layout_bytes": layout_size,
            "gaussian_count": n,
            "compact_format": True,
        }
    )


def _parse_f16_layout(data: bytes, n: int) -> ParserResult:
    """Parse float16-based compact layout."""
    layout_size = 34
    
    positions = np.zeros((n, 3), dtype=np.float32)
    scales = np.zeros((n, 3), dtype=np.float32)
    rotations = np.zeros((n, 4), dtype=np.float32)
    opacities = np.zeros((n, 1), dtype=np.float32)
    colors = np.zeros((n, 3), dtype=np.float32)
    
    for i in range(n):
        offset = i * layout_size
        
        # Position (3 float32)
        positions[i] = struct.unpack_from('<3f', data, offset)
        
        # Scale (3 float16)
        scale_bytes = data[offset + 12:offset + 18]
        scales[i] = np.frombuffer(scale_bytes, dtype=np.float16).astype(np.float32)
        
        # Rotation (4 float16)
        rot_bytes = data[offset + 18:offset + 26]
        rotations[i] = np.frombuffer(rot_bytes, dtype=np.float16).astype(np.float32)
        
        # Opacity (1 float16)
        op_bytes = data[offset + 26:offset + 28]
        opacities[i] = np.frombuffer(op_bytes, dtype=np.float16).astype(np.float32)
        
        # Color (3 float16)
        color_bytes = data[offset + 28:offset + 34]
        colors[i] = np.frombuffer(color_bytes, dtype=np.float16).astype(np.float32)
    
    # Process values
    if scales.min() < 0:
        scales = np.exp(scales)
    
    if opacities.min() < 0 or opacities.max() > 1.0:
        opacities = 1.0 / (1.0 + np.exp(-opacities))
    
    # Normalize rotations
    norms = np.linalg.norm(rotations, axis=1, keepdims=True)
    norms[norms == 0] = 1
    rotations = rotations / norms
    
    colors = np.clip(colors, 0, 1)
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        scales=scales,
        rotations=rotations,
        opacities=opacities,
        data_type=ParsedDataType.GAUSSIAN,
        is_gaussian=True,
        point_count=n,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="SPLAT",
        format_version="float16",
        metadata={
            "layout_bytes": layout_size,
            "gaussian_count": n,
            "compact_format": True,
        }
    )
