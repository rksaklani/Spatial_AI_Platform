"""
3D File Parsers Module

Phase 4: Complete implementation of all 3D file format parsers

Supported formats:
- PLY (Task 14.2): Point clouds and meshes with Gaussian support
- LAS/LAZ (Task 14.3): Point cloud formats
- OBJ (Task 14.4): Wavefront mesh format
- GLTF/GLB (Task 14.5): glTF 2.0 format
- SPLAT (Task 14.6): Gaussian Splatting format
- STL (Task 15.2): Mesh format
- FBX (Task 15.1): Autodesk format
- DAE (Task 15.3): COLLADA format
- E57 (Task 15.4): Point cloud format
- IFC (Task 16.1): BIM format
"""

from workers.parsers.ply_parser import parse_ply
from workers.parsers.las_parser import parse_las
from workers.parsers.obj_parser import parse_obj
from workers.parsers.gltf_parser import parse_gltf
from workers.parsers.splat_parser import parse_splat
from workers.parsers.stl_parser import parse_stl
from workers.parsers.fbx_parser import parse_fbx
from workers.parsers.dae_parser import parse_dae
from workers.parsers.e57_parser import parse_e57
from workers.parsers.ifc_parser import parse_ifc
from workers.parsers.base import ParsedData, ParserResult

# Parser registry mapping format to parser function
PARSER_REGISTRY = {
    "ply": parse_ply,
    "las": parse_las,
    "obj": parse_obj,
    "gltf": parse_gltf,
    "splat": parse_splat,
    "stl": parse_stl,
    "fbx": parse_fbx,
    "dae": parse_dae,
    "e57": parse_e57,
    "ifc": parse_ifc,
}


def get_parser(parser_type: str):
    """Get parser function by type."""
    if parser_type not in PARSER_REGISTRY:
        raise ValueError(f"Unknown parser type: {parser_type}")
    return PARSER_REGISTRY[parser_type]


def parse_file(file_path: str, parser_type: str) -> ParserResult:
    """
    Parse a 3D file using the appropriate parser.
    
    Args:
        file_path: Path to the file
        parser_type: Parser type (ply, las, obj, etc.)
        
    Returns:
        ParserResult with parsed data
    """
    parser = get_parser(parser_type)
    return parser(file_path)


__all__ = [
    "parse_file",
    "get_parser",
    "PARSER_REGISTRY",
    "ParsedData",
    "ParserResult",
    "parse_ply",
    "parse_las",
    "parse_obj",
    "parse_gltf",
    "parse_splat",
    "parse_stl",
    "parse_fbx",
    "parse_dae",
    "parse_e57",
    "parse_ifc",
]
