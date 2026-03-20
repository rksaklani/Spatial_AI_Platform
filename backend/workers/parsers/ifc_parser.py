"""
IFC BIM Parser (Task 16.1)

Parses IFC (Industry Foundation Classes) BIM format.
Supports IFC 2x3 and IFC 4.

Features:
- Building element extraction
- BIM properties and metadata
- Geometric representation
- Element hierarchy
- Quantity takeoff data

Dependencies:
- ifcopenshell (recommended)
- trimesh with ifcopenshell backend
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from workers.parsers.base import (
    ParsedData,
    ParserResult,
    ParsedDataType,
    BIMElement,
    MaterialInfo,
    normalize_normals,
    sample_mesh_to_points,
)

logger = logging.getLogger(__name__)

# IFC element type categories
IFC_BUILDING_ELEMENTS = {
    'IfcWall', 'IfcWallStandardCase', 'IfcCurtainWall',
    'IfcSlab', 'IfcRoof', 'IfcCovering',
    'IfcDoor', 'IfcWindow',
    'IfcStair', 'IfcStairFlight', 'IfcRamp', 'IfcRampFlight',
    'IfcColumn', 'IfcBeam', 'IfcMember',
    'IfcPlate', 'IfcFooting', 'IfcPile',
    'IfcBuildingElementProxy',
}

IFC_SPATIAL_ELEMENTS = {
    'IfcSite', 'IfcBuilding', 'IfcBuildingStorey', 'IfcSpace',
}

IFC_ELEMENT_COLORS = {
    'IfcWall': [0.9, 0.9, 0.85],
    'IfcWallStandardCase': [0.9, 0.9, 0.85],
    'IfcSlab': [0.7, 0.7, 0.7],
    'IfcRoof': [0.6, 0.3, 0.2],
    'IfcDoor': [0.5, 0.3, 0.1],
    'IfcWindow': [0.6, 0.8, 0.95],
    'IfcColumn': [0.5, 0.5, 0.5],
    'IfcBeam': [0.5, 0.5, 0.5],
    'IfcStair': [0.7, 0.6, 0.5],
    'default': [0.6, 0.6, 0.6],
}


def parse_ifc(file_path: str) -> ParserResult:
    """
    Parse an IFC BIM file.
    
    Extracts:
    - Geometric representations
    - Building elements
    - Properties and quantities
    - Spatial hierarchy
    
    Args:
        file_path: Path to IFC file
        
    Returns:
        ParserResult with BIM data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"IFC file not found: {file_path}")
    
    logger.info(f"Parsing IFC file: {file_path}")
    
    try:
        return _parse_with_ifcopenshell(file_path)
    except ImportError:
        logger.warning("ifcopenshell not available")
    except Exception as e:
        logger.warning(f"ifcopenshell failed: {e}")
    
    # Try trimesh with IFC support
    try:
        return _parse_with_trimesh(file_path)
    except Exception as e:
        logger.warning(f"trimesh IFC failed: {e}")
    
    # Fallback - basic parsing
    return _parse_ifc_fallback(file_path)


def _parse_with_ifcopenshell(file_path: str) -> ParserResult:
    """Parse IFC using ifcopenshell."""
    import ifcopenshell
    import ifcopenshell.geom
    
    # Open IFC file
    ifc_file = ifcopenshell.open(file_path)
    
    # Get schema version
    schema = ifc_file.schema
    logger.info(f"IFC schema: {schema}")
    
    # Setup geometry settings
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.WELD_VERTICES, True)
    
    all_vertices = []
    all_faces = []
    all_colors = []
    all_element_ids = []
    bim_elements = []
    materials = []
    
    vertex_offset = 0
    element_counter = 0
    
    # Process building elements
    building_elements = list(ifc_file.by_type('IfcProduct'))
    logger.info(f"Found {len(building_elements)} IFC products")
    
    for element in building_elements:
        try:
            # Get element type
            element_type = element.is_a()
            
            # Skip spatial elements for geometry (but extract hierarchy)
            if element_type in IFC_SPATIAL_ELEMENTS:
                continue
            
            # Create geometry
            shape = ifcopenshell.geom.create_shape(settings, element)
            
            if shape is None:
                continue
            
            # Extract geometry
            geometry = shape.geometry
            vertices = np.array(geometry.verts, dtype=np.float32).reshape(-1, 3)
            faces = np.array(geometry.faces, dtype=np.int32).reshape(-1, 3)
            
            if len(vertices) == 0:
                continue
            
            n_verts = len(vertices)
            
            # Offset faces
            faces = faces + vertex_offset
            
            all_vertices.append(vertices)
            all_faces.append(faces)
            
            # Get color based on element type
            color = IFC_ELEMENT_COLORS.get(element_type, IFC_ELEMENT_COLORS['default'])
            colors = np.tile(color, (n_verts, 1)).astype(np.float32)
            all_colors.append(colors)
            
            # Track element IDs
            element_ids = np.full(n_verts, element_counter, dtype=np.int32)
            all_element_ids.append(element_ids)
            
            # Extract BIM element info
            bim_elem = _extract_bim_element(element, element_counter, vertices)
            bim_elements.append(bim_elem)
            
            vertex_offset += n_verts
            element_counter += 1
            
        except Exception as e:
            logger.debug(f"Failed to process element {element.id()}: {e}")
            continue
    
    if not all_vertices:
        raise ValueError("No geometry found in IFC file")
    
    # Concatenate all data
    vertices = np.concatenate(all_vertices, axis=0)
    faces = np.concatenate(all_faces, axis=0)
    colors = np.concatenate(all_colors, axis=0)
    element_ids = np.concatenate(all_element_ids, axis=0)
    
    n = len(vertices)
    f = len(faces)
    
    logger.info(f"IFC geometry: {n} vertices, {f} faces, {len(bim_elements)} elements")
    
    # Sample points
    n_samples = min(100000, n * 3)
    sampled_points, sampled_colors, sampled_normals, face_indices = sample_mesh_to_points(
        vertices, faces, n_samples, vertex_colors=colors
    )
    
    # Map element IDs to sampled points
    if face_indices is not None:
        sampled_element_ids = element_ids[faces[face_indices, 0]]
    else:
        sampled_element_ids = element_ids[:len(sampled_points)]
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=sampled_colors,
        normals=sampled_normals,
        faces=faces,
        element_ids=sampled_element_ids,
        element_types=[e.element_type for e in bim_elements],
        data_type=ParsedDataType.BIM,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    # Extract spatial hierarchy
    metadata = _extract_ifc_metadata(ifc_file)
    metadata.update({
        "element_count": len(bim_elements),
        "original_vertices": n,
        "original_faces": f,
    })
    
    return ParserResult(
        data=parsed_data,
        format_name="IFC",
        format_version=schema,
        bim_elements=bim_elements,
        metadata=metadata,
    )


def _extract_bim_element(element, element_id: int, vertices: np.ndarray) -> BIMElement:
    """Extract BIM element information from IFC element."""
    element_type = element.is_a()
    
    # Basic properties
    bim_elem = BIMElement(
        element_id=element_id,
        global_id=element.GlobalId,
        element_type=element_type,
        name=getattr(element, 'Name', None),
        description=getattr(element, 'Description', None),
        object_type=getattr(element, 'ObjectType', None),
    )
    
    # Bounding box
    if len(vertices) > 0:
        bim_elem.bounding_box = np.array([
            vertices.min(axis=0),
            vertices.max(axis=0)
        ], dtype=np.float32)
    
    # Extract properties
    try:
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                prop_set = definition.RelatingPropertyDefinition
                if prop_set.is_a('IfcPropertySet'):
                    for prop in prop_set.HasProperties:
                        if prop.is_a('IfcPropertySingleValue'):
                            value = prop.NominalValue.wrappedValue if prop.NominalValue else None
                            bim_elem.properties[prop.Name] = value
    except Exception:
        pass
    
    # Extract quantities
    try:
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                prop_set = definition.RelatingPropertyDefinition
                if prop_set.is_a('IfcElementQuantity'):
                    for quantity in prop_set.Quantities:
                        if hasattr(quantity, 'AreaValue'):
                            bim_elem.quantities[quantity.Name] = quantity.AreaValue
                        elif hasattr(quantity, 'VolumeValue'):
                            bim_elem.quantities[quantity.Name] = quantity.VolumeValue
                        elif hasattr(quantity, 'LengthValue'):
                            bim_elem.quantities[quantity.Name] = quantity.LengthValue
    except Exception:
        pass
    
    # Get storey
    try:
        if hasattr(element, 'ContainedInStructure'):
            for rel in element.ContainedInStructure:
                structure = rel.RelatingStructure
                if structure.is_a('IfcBuildingStorey'):
                    bim_elem.storey = structure.Name
                    break
    except Exception:
        pass
    
    return bim_elem


def _extract_ifc_metadata(ifc_file) -> Dict[str, Any]:
    """Extract IFC file metadata."""
    metadata = {}
    
    # File header info
    try:
        header = ifc_file.header
        if hasattr(header, 'file_name'):
            fn = header.file_name
            metadata['author'] = getattr(fn, 'author', None)
            metadata['organization'] = getattr(fn, 'organization', None)
    except Exception:
        pass
    
    # Count elements by type
    element_counts = {}
    for elem_type in IFC_BUILDING_ELEMENTS:
        try:
            count = len(list(ifc_file.by_type(elem_type)))
            if count > 0:
                element_counts[elem_type] = count
        except Exception:
            pass
    metadata['element_counts'] = element_counts
    
    # Spatial hierarchy
    try:
        sites = list(ifc_file.by_type('IfcSite'))
        buildings = list(ifc_file.by_type('IfcBuilding'))
        storeys = list(ifc_file.by_type('IfcBuildingStorey'))
        spaces = list(ifc_file.by_type('IfcSpace'))
        
        metadata['site_count'] = len(sites)
        metadata['building_count'] = len(buildings)
        metadata['storey_count'] = len(storeys)
        metadata['space_count'] = len(spaces)
        
        if buildings:
            metadata['building_name'] = buildings[0].Name
    except Exception:
        pass
    
    return metadata


def _parse_with_trimesh(file_path: str) -> ParserResult:
    """Parse IFC using trimesh (requires ifcopenshell backend)."""
    import trimesh
    
    scene = trimesh.load(file_path)
    
    if isinstance(scene, trimesh.Scene):
        meshes = [g for g in scene.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("IFC file contains no valid meshes")
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = scene
    
    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)
    
    n = len(vertices)
    f = len(faces)
    logger.info(f"IFC (trimesh) has {n} vertices, {f} faces")
    
    normals = None
    if mesh.vertex_normals is not None:
        normals = normalize_normals(mesh.vertex_normals.astype(np.float32))
    
    colors = None
    if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
        colors = mesh.visual.vertex_colors[:, :3].astype(np.float32) / 255.0
    else:
        colors = np.ones((n, 3), dtype=np.float32) * 0.7
    
    n_samples = min(100000, n * 3)
    sampled_points, sampled_colors, sampled_normals, _ = sample_mesh_to_points(
        vertices, faces, n_samples, vertex_colors=colors, vertex_normals=normals
    )
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=sampled_colors,
        normals=sampled_normals,
        faces=faces,
        data_type=ParsedDataType.BIM,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="IFC",
        metadata={
            "parser": "trimesh",
            "original_vertices": n,
            "original_faces": f,
        },
        warnings=["BIM properties not extracted - install ifcopenshell for full support"]
    )


def _parse_ifc_fallback(file_path: str) -> ParserResult:
    """Fallback IFC parser - basic text parsing."""
    # IFC is a STEP file format - extract basic info
    entity_counts = {}
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') and '=' in line:
                # Extract entity type
                parts = line.split('=', 1)
                if len(parts) == 2:
                    entity_part = parts[1].strip()
                    paren_idx = entity_part.find('(')
                    if paren_idx > 0:
                        entity_type = entity_part[:paren_idx].strip()
                        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    logger.warning("IFC fallback parser - geometry not extracted")
    logger.info(f"Found entities: {len(entity_counts)} types")
    
    # Generate placeholder geometry
    n = 1000
    positions = np.random.randn(n, 3).astype(np.float32) * 10
    colors = np.ones((n, 3), dtype=np.float32) * 0.7
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        data_type=ParsedDataType.BIM,
        point_count=n,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="IFC",
        metadata={
            "parser": "fallback",
            "entity_counts": entity_counts,
            "warning": "Geometry not extracted - install ifcopenshell for full support",
        },
        warnings=["IFC geometry not extracted - install ifcopenshell"]
    )
