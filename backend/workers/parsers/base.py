"""
Base classes and utilities for 3D file parsers.

Provides common data structures and conversion utilities.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class ParsedDataType(str, Enum):
    """Type of parsed 3D data."""
    POINT_CLOUD = "point_cloud"
    MESH = "mesh"
    GAUSSIAN = "gaussian"
    BIM = "bim"


@dataclass
class ParsedData:
    """
    Standard data structure for parsed 3D files.
    
    All parsers should return data in this format for consistent
    downstream processing.
    """
    # Core geometry (required)
    positions: np.ndarray  # (N, 3) float32 - point/vertex positions
    
    # Optional geometry attributes
    colors: Optional[np.ndarray] = None  # (N, 3) float32 - RGB colors [0-1]
    normals: Optional[np.ndarray] = None  # (N, 3) float32 - normal vectors
    
    # Mesh data (optional)
    faces: Optional[np.ndarray] = None  # (F, 3) int32 - triangle indices
    uvs: Optional[np.ndarray] = None  # (N, 2) float32 - texture coordinates
    
    # Gaussian-specific attributes (optional)
    scales: Optional[np.ndarray] = None  # (N, 3) float32 - Gaussian scales
    rotations: Optional[np.ndarray] = None  # (N, 4) float32 - quaternions (w,x,y,z)
    opacities: Optional[np.ndarray] = None  # (N, 1) float32 - opacity [0-1]
    sh_coeffs: Optional[np.ndarray] = None  # (N, K) float32 - spherical harmonics
    
    # Point cloud attributes
    intensities: Optional[np.ndarray] = None  # (N,) float32 - intensity values
    classifications: Optional[np.ndarray] = None  # (N,) int32 - point classifications
    
    # BIM attributes
    element_ids: Optional[np.ndarray] = None  # (N,) int32 - element IDs
    element_types: Optional[List[str]] = None  # List of element type names
    bim_properties: Optional[Dict[int, Dict]] = None  # element_id -> properties
    
    # Metadata
    data_type: ParsedDataType = ParsedDataType.POINT_CLOUD
    is_gaussian: bool = False
    point_count: int = 0
    face_count: int = 0
    
    def __post_init__(self):
        """Compute derived values after initialization."""
        if self.positions is not None:
            self.point_count = len(self.positions)
        if self.faces is not None:
            self.face_count = len(self.faces)


@dataclass
class MaterialInfo:
    """Material information for meshes."""
    name: str = "default"
    diffuse_color: Optional[np.ndarray] = None  # RGB [0-1]
    specular_color: Optional[np.ndarray] = None
    ambient_color: Optional[np.ndarray] = None
    emissive_color: Optional[np.ndarray] = None
    roughness: float = 0.5
    metallic: float = 0.0
    opacity: float = 1.0
    diffuse_texture: Optional[str] = None  # Path to texture
    normal_texture: Optional[str] = None
    roughness_texture: Optional[str] = None


@dataclass
class BIMElement:
    """BIM element information."""
    element_id: int
    global_id: str
    element_type: str  # IfcWall, IfcDoor, etc.
    name: Optional[str] = None
    description: Optional[str] = None
    object_type: Optional[str] = None
    storey: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    quantities: Dict[str, float] = field(default_factory=dict)  # area, volume, etc.
    material: Optional[str] = None
    bounding_box: Optional[np.ndarray] = None  # (2, 3) min/max corners


@dataclass
class ParserResult:
    """
    Complete result from a parser including data and metadata.
    """
    data: ParsedData
    format_name: str
    format_version: Optional[str] = None
    
    # Geometry statistics
    bounding_box_min: Optional[np.ndarray] = None
    bounding_box_max: Optional[np.ndarray] = None
    center: Optional[np.ndarray] = None
    
    # Materials
    materials: List[MaterialInfo] = field(default_factory=list)
    
    # BIM elements
    bim_elements: List[BIMElement] = field(default_factory=list)
    
    # Warnings during parsing
    warnings: List[str] = field(default_factory=list)
    
    # Original file metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Compute bounding box if not provided."""
        if self.data.positions is not None and len(self.data.positions) > 0:
            if self.bounding_box_min is None:
                self.bounding_box_min = self.data.positions.min(axis=0)
            if self.bounding_box_max is None:
                self.bounding_box_max = self.data.positions.max(axis=0)
            if self.center is None:
                self.center = (self.bounding_box_min + self.bounding_box_max) / 2


def normalize_colors(colors: np.ndarray) -> np.ndarray:
    """Normalize colors to [0, 1] range."""
    if colors is None:
        return None
    colors = colors.astype(np.float32)
    if colors.max() > 1.0:
        colors = colors / 255.0
    return np.clip(colors, 0, 1)


def normalize_normals(normals: np.ndarray) -> np.ndarray:
    """Normalize normal vectors to unit length."""
    if normals is None:
        return None
    normals = normals.astype(np.float32)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    return normals / norms


def sample_mesh_to_points(
    vertices: np.ndarray,
    faces: np.ndarray,
    n_samples: int = 100000,
    vertex_colors: Optional[np.ndarray] = None,
    vertex_normals: Optional[np.ndarray] = None,
) -> tuple:
    """
    Sample points from mesh surface using barycentric coordinates.
    
    Returns:
        Tuple of (points, colors, normals, face_indices)
    """
    # Calculate face areas for weighted sampling
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    
    cross = np.cross(v1 - v0, v2 - v0)
    areas = 0.5 * np.linalg.norm(cross, axis=1)
    
    # Normalize areas to probabilities
    total_area = areas.sum()
    if total_area == 0:
        # Degenerate mesh, sample vertices directly
        indices = np.random.choice(len(vertices), min(n_samples, len(vertices)), replace=False)
        points = vertices[indices].astype(np.float32)
        colors = vertex_colors[indices] if vertex_colors is not None else None
        normals = vertex_normals[indices] if vertex_normals is not None else None
        return points, colors, normals, None
    
    probs = areas / total_area
    
    # Sample faces based on area
    face_indices = np.random.choice(len(faces), n_samples, p=probs)
    
    # Generate random barycentric coordinates
    r1 = np.random.rand(n_samples, 1)
    r2 = np.random.rand(n_samples, 1)
    sqrt_r1 = np.sqrt(r1)
    
    # Barycentric coordinates
    w0 = 1 - sqrt_r1
    w1 = sqrt_r1 * (1 - r2)
    w2 = sqrt_r1 * r2
    
    # Interpolate positions
    v0 = vertices[faces[face_indices, 0]]
    v1 = vertices[faces[face_indices, 1]]
    v2 = vertices[faces[face_indices, 2]]
    
    points = (w0 * v0 + w1 * v1 + w2 * v2).astype(np.float32)
    
    # Interpolate colors if available
    colors = None
    if vertex_colors is not None:
        c0 = vertex_colors[faces[face_indices, 0]]
        c1 = vertex_colors[faces[face_indices, 1]]
        c2 = vertex_colors[faces[face_indices, 2]]
        colors = (w0 * c0 + w1 * c1 + w2 * c2).astype(np.float32)
    
    # Interpolate normals if available
    normals = None
    if vertex_normals is not None:
        n0 = vertex_normals[faces[face_indices, 0]]
        n1 = vertex_normals[faces[face_indices, 1]]
        n2 = vertex_normals[faces[face_indices, 2]]
        normals = normalize_normals(w0 * n0 + w1 * n1 + w2 * n2)
    
    return points, colors, normals, face_indices


def estimate_point_scales(positions: np.ndarray, k: int = 5) -> np.ndarray:
    """
    Estimate Gaussian scales from local point density.
    
    Uses k-nearest neighbors to estimate local scale.
    """
    from scipy.spatial import KDTree
    
    n = len(positions)
    if n <= k:
        # Too few points, use constant scale
        return np.ones((n, 3), dtype=np.float32) * 0.1
    
    tree = KDTree(positions)
    distances, _ = tree.query(positions, k=min(k + 1, n))
    
    # Average distance to k neighbors (exclude self at index 0)
    mean_distances = distances[:, 1:].mean(axis=1)
    
    # Use half the mean distance as scale
    scales = np.stack([mean_distances] * 3, axis=1).astype(np.float32) * 0.5
    
    return scales


def colors_to_sh_dc(colors: np.ndarray) -> np.ndarray:
    """
    Convert RGB colors to DC spherical harmonics coefficients.
    
    The DC (degree 0) SH coefficient encodes the base color.
    """
    if colors is None:
        return None
    
    SH_C0 = 0.28209479177387814  # sqrt(1 / (4 * pi))
    
    # Convert from [0,1] RGB to SH DC
    sh_dc = (colors - 0.5) / SH_C0
    
    return sh_dc.astype(np.float32)


def create_identity_rotations(n: int) -> np.ndarray:
    """Create identity quaternions for n Gaussians."""
    rotations = np.zeros((n, 4), dtype=np.float32)
    rotations[:, 0] = 1.0  # w component
    return rotations


def points_to_gaussians(
    positions: np.ndarray,
    colors: Optional[np.ndarray] = None,
    normals: Optional[np.ndarray] = None,
    scale_factor: float = 0.5,
) -> ParsedData:
    """
    Convert point cloud to Gaussian representation.
    
    Args:
        positions: (N, 3) point positions
        colors: Optional (N, 3) RGB colors
        normals: Optional (N, 3) normals (used for oriented Gaussians)
        scale_factor: Multiplier for estimated scales
        
    Returns:
        ParsedData with Gaussian attributes
    """
    n = len(positions)
    
    # Estimate scales from point density
    scales = estimate_point_scales(positions) * scale_factor
    
    # Create identity rotations (or orient by normals if available)
    if normals is not None:
        # TODO: Compute rotations from normals for oriented Gaussians
        rotations = create_identity_rotations(n)
    else:
        rotations = create_identity_rotations(n)
    
    # Initialize opacities
    opacities = np.ones((n, 1), dtype=np.float32) * 0.8
    
    # Convert colors to SH if available
    sh_coeffs = None
    if colors is not None:
        sh_dc = colors_to_sh_dc(colors)
        # Create full SH array with only DC populated
        sh_coeffs = np.zeros((n, 48), dtype=np.float32)
        sh_coeffs[:, :3] = sh_dc
    
    return ParsedData(
        positions=positions.astype(np.float32),
        colors=colors,
        normals=normals,
        scales=scales,
        rotations=rotations,
        opacities=opacities,
        sh_coeffs=sh_coeffs,
        data_type=ParsedDataType.GAUSSIAN,
        is_gaussian=True,
        point_count=n,
    )
