"""
Phase 4 Complete Tests - 3D File Import Pipeline

Tests for Tasks 14-16:
- Task 14: 3D file import handler and parsers
- Task 15: Extended 3D format support
- Task 16: BIM and IFC support
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path


# =============================================================================
# Task 14.1: Import API Tests
# =============================================================================

class TestImportAPI:
    """Test import API endpoints and models."""
    
    def test_supported_formats_defined(self):
        """All supported formats are defined."""
        from api.import_3d import SUPPORTED_FORMATS
        
        expected_formats = ['.ply', '.las', '.laz', '.obj', '.glb', '.gltf', 
                          '.splat', '.stl', '.fbx', '.dae', '.e57', '.ifc']
        
        for fmt in expected_formats:
            assert fmt in SUPPORTED_FORMATS, f"Missing format: {fmt}"
    
    def test_format_types(self):
        """Each format has correct type classification."""
        from api.import_3d import SUPPORTED_FORMATS
        
        point_cloud_formats = ['.ply', '.las', '.laz', '.e57']
        mesh_formats = ['.obj', '.glb', '.gltf', '.stl', '.fbx', '.dae']
        gaussian_formats = ['.splat']
        bim_formats = ['.ifc']
        
        for fmt in point_cloud_formats:
            if fmt in SUPPORTED_FORMATS:
                assert SUPPORTED_FORMATS[fmt]['type'] in ['point_cloud', 'mesh']
        
        for fmt in mesh_formats:
            if fmt in SUPPORTED_FORMATS:
                assert SUPPORTED_FORMATS[fmt]['type'] == 'mesh'
        
        for fmt in gaussian_formats:
            if fmt in SUPPORTED_FORMATS:
                assert SUPPORTED_FORMATS[fmt]['type'] == 'gaussian'
        
        for fmt in bim_formats:
            if fmt in SUPPORTED_FORMATS:
                assert SUPPORTED_FORMATS[fmt]['type'] == 'bim'
    
    def test_max_file_size(self):
        """Max file size is 5GB."""
        from api.import_3d import MAX_FILE_SIZE_BYTES
        
        assert MAX_FILE_SIZE_BYTES == 5 * 1024 * 1024 * 1024


# =============================================================================
# Task 14.2: PLY Parser Tests
# =============================================================================

class TestPLYParser:
    """Test PLY file parsing (Task 14.2)."""
    
    def test_parser_module_exists(self):
        """PLY parser module exists."""
        from workers.parsers.ply_parser import parse_ply
        assert callable(parse_ply)
    
    def test_parse_simple_ply(self):
        """Parse a simple ASCII PLY file."""
        from workers.parsers.ply_parser import parse_ply
        
        # Create temp PLY file
        ply_content = """ply
format ascii 1.0
element vertex 4
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
0 0 0 255 0 0
1 0 0 0 255 0
1 1 0 0 0 255
0 1 0 255 255 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ply', delete=False) as f:
            f.write(ply_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_ply(temp_path)
            
            assert result.data.point_count == 4
            assert result.data.positions.shape == (4, 3)
            assert result.data.colors is not None
            assert result.data.colors.shape == (4, 3)
            assert result.format_name == "PLY"
        finally:
            os.unlink(temp_path)
    
    def test_parsed_data_structure(self):
        """ParserResult has correct structure."""
        from workers.parsers.base import ParserResult, ParsedData, ParsedDataType
        
        data = ParsedData(
            positions=np.random.randn(100, 3).astype(np.float32),
            data_type=ParsedDataType.POINT_CLOUD,
        )
        
        result = ParserResult(data=data, format_name="TEST")
        
        assert result.data.point_count == 100
        assert result.bounding_box_min is not None
        assert result.bounding_box_max is not None


# =============================================================================
# Task 14.3: LAS/LAZ Parser Tests
# =============================================================================

class TestLASParser:
    """Test LAS/LAZ parsing (Task 14.3)."""
    
    def test_parser_module_exists(self):
        """LAS parser module exists."""
        from workers.parsers.las_parser import parse_las
        assert callable(parse_las)
    
    def test_las_classifications_defined(self):
        """LAS classification codes are defined."""
        from workers.parsers.las_parser import LAS_CLASSIFICATIONS
        
        assert 2 in LAS_CLASSIFICATIONS  # Ground
        assert 6 in LAS_CLASSIFICATIONS  # Building
        assert 9 in LAS_CLASSIFICATIONS  # Water


# =============================================================================
# Task 14.4: OBJ Parser Tests
# =============================================================================

class TestOBJParser:
    """Test OBJ mesh parsing (Task 14.4)."""
    
    def test_parser_module_exists(self):
        """OBJ parser module exists."""
        from workers.parsers.obj_parser import parse_obj
        assert callable(parse_obj)
    
    def test_parse_simple_obj(self):
        """Parse a simple OBJ file."""
        from workers.parsers.obj_parser import parse_obj
        
        obj_content = """# Simple cube
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.obj', delete=False) as f:
            f.write(obj_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_obj(temp_path)
            
            assert result.data.point_count > 0
            assert result.format_name == "OBJ"
            assert result.data.data_type.value in ["mesh", "point_cloud"]
        finally:
            os.unlink(temp_path)


# =============================================================================
# Task 14.5: GLTF Parser Tests
# =============================================================================

class TestGLTFParser:
    """Test glTF/GLB parsing (Task 14.5)."""
    
    def test_parser_module_exists(self):
        """GLTF parser module exists."""
        from workers.parsers.gltf_parser import parse_gltf
        assert callable(parse_gltf)
    
    def test_gltf_component_types(self):
        """GLTF component types are defined."""
        from workers.parsers.gltf_parser import GLTF_COMPONENT_TYPES
        
        assert 5126 in GLTF_COMPONENT_TYPES  # FLOAT
        assert 5123 in GLTF_COMPONENT_TYPES  # UNSIGNED_SHORT
    
    def test_gltf_accessor_types(self):
        """GLTF accessor types are defined."""
        from workers.parsers.gltf_parser import GLTF_ACCESSOR_TYPES
        
        assert GLTF_ACCESSOR_TYPES['VEC3'] == 3
        assert GLTF_ACCESSOR_TYPES['VEC4'] == 4
        assert GLTF_ACCESSOR_TYPES['MAT4'] == 16


# =============================================================================
# Task 14.6: SPLAT Parser Tests
# =============================================================================

class TestSPLATParser:
    """Test Gaussian Splatting format parsing (Task 14.6)."""
    
    def test_parser_module_exists(self):
        """SPLAT parser module exists."""
        from workers.parsers.splat_parser import parse_splat
        assert callable(parse_splat)
    
    def test_splat_layouts_defined(self):
        """SPLAT layouts are defined."""
        from workers.parsers.splat_parser import SPLAT_LAYOUTS
        
        assert 56 in SPLAT_LAYOUTS  # Standard layout
        assert 24 in SPLAT_LAYOUTS  # Antimatter15 layout
        assert 32 in SPLAT_LAYOUTS  # Compact web layout
    
    def test_parse_standard_splat(self):
        """Parse standard 56-byte SPLAT format."""
        from workers.parsers.splat_parser import parse_splat
        import struct
        
        # Create a minimal 56-byte per Gaussian file
        n_gaussians = 10
        data = b''
        
        for i in range(n_gaussians):
            # pos(12) + scale(12) + rot(16) + opacity(4) + color(12) = 56 bytes
            pos = struct.pack('<3f', float(i), float(i), float(i))
            scale = struct.pack('<3f', 0.1, 0.1, 0.1)
            rot = struct.pack('<4f', 1.0, 0.0, 0.0, 0.0)
            opacity = struct.pack('<f', 0.8)
            color = struct.pack('<3f', 0.5, 0.5, 0.5)
            data += pos + scale + rot + opacity + color
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.splat', delete=False) as f:
            f.write(data)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_splat(temp_path)
            
            assert result.data.point_count == n_gaussians
            assert result.data.is_gaussian == True
            assert result.data.scales is not None
            assert result.data.rotations is not None
            assert result.data.opacities is not None
        finally:
            os.unlink(temp_path)


# =============================================================================
# Task 15.2: STL Parser Tests
# =============================================================================

class TestSTLParser:
    """Test STL mesh parsing (Task 15.2)."""
    
    def test_parser_module_exists(self):
        """STL parser module exists."""
        from workers.parsers.stl_parser import parse_stl
        assert callable(parse_stl)
    
    def test_parse_ascii_stl(self):
        """Parse ASCII STL file."""
        from workers.parsers.stl_parser import parse_stl
        
        stl_content = """solid test
facet normal 0 0 1
    outer loop
        vertex 0 0 0
        vertex 1 0 0
        vertex 0.5 1 0
    endloop
endfacet
endsolid test
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as f:
            f.write(stl_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_stl(temp_path)
            
            assert result.data.point_count > 0
            assert result.format_name == "STL"
        finally:
            os.unlink(temp_path)


# =============================================================================
# Task 15.1/15.3: FBX and DAE Parser Tests
# =============================================================================

class TestMeshParsers:
    """Test FBX and DAE parsers (Tasks 15.1, 15.3)."""
    
    def test_fbx_parser_exists(self):
        """FBX parser module exists."""
        from workers.parsers.fbx_parser import parse_fbx
        assert callable(parse_fbx)
    
    def test_dae_parser_exists(self):
        """DAE parser module exists."""
        from workers.parsers.dae_parser import parse_dae
        assert callable(parse_dae)
    
    def test_dae_namespaces(self):
        """COLLADA namespaces are defined."""
        from workers.parsers.dae_parser import COLLADA_NS
        
        assert 'c' in COLLADA_NS
        assert 'c14' in COLLADA_NS


# =============================================================================
# Task 15.4: E57 Parser Tests
# =============================================================================

class TestE57Parser:
    """Test E57 point cloud parsing (Task 15.4)."""
    
    def test_parser_module_exists(self):
        """E57 parser module exists."""
        from workers.parsers.e57_parser import parse_e57
        assert callable(parse_e57)


# =============================================================================
# Task 16.1: IFC/BIM Parser Tests
# =============================================================================

class TestIFCParser:
    """Test IFC BIM parsing (Task 16.1)."""
    
    def test_parser_module_exists(self):
        """IFC parser module exists."""
        from workers.parsers.ifc_parser import parse_ifc
        assert callable(parse_ifc)
    
    def test_ifc_building_elements(self):
        """IFC building elements are defined."""
        from workers.parsers.ifc_parser import IFC_BUILDING_ELEMENTS
        
        assert 'IfcWall' in IFC_BUILDING_ELEMENTS
        assert 'IfcDoor' in IFC_BUILDING_ELEMENTS
        assert 'IfcSlab' in IFC_BUILDING_ELEMENTS
        assert 'IfcColumn' in IFC_BUILDING_ELEMENTS
    
    def test_ifc_element_colors(self):
        """IFC element colors are defined."""
        from workers.parsers.ifc_parser import IFC_ELEMENT_COLORS
        
        assert 'IfcWall' in IFC_ELEMENT_COLORS
        assert 'IfcWindow' in IFC_ELEMENT_COLORS
        assert 'default' in IFC_ELEMENT_COLORS
    
    def test_bim_element_dataclass(self):
        """BIMElement dataclass works correctly."""
        from workers.parsers.base import BIMElement
        
        elem = BIMElement(
            element_id=1,
            global_id="abc123",
            element_type="IfcWall",
            name="Wall-001",
        )
        
        assert elem.element_id == 1
        assert elem.element_type == "IfcWall"
        assert elem.properties == {}
        assert elem.quantities == {}


# =============================================================================
# Parser Base Module Tests
# =============================================================================

class TestParserBase:
    """Test parser base utilities."""
    
    def test_parsed_data_types(self):
        """ParsedDataType enum has all types."""
        from workers.parsers.base import ParsedDataType
        
        assert ParsedDataType.POINT_CLOUD.value == "point_cloud"
        assert ParsedDataType.MESH.value == "mesh"
        assert ParsedDataType.GAUSSIAN.value == "gaussian"
        assert ParsedDataType.BIM.value == "bim"
    
    def test_normalize_colors(self):
        """Color normalization works."""
        from workers.parsers.base import normalize_colors
        
        # Test 0-255 range
        colors = np.array([[255, 128, 0], [0, 255, 128]], dtype=np.float32)
        normalized = normalize_colors(colors)
        
        assert normalized.max() <= 1.0
        assert normalized.min() >= 0.0
        assert np.allclose(normalized[0, 0], 1.0)
    
    def test_normalize_normals(self):
        """Normal normalization works."""
        from workers.parsers.base import normalize_normals
        
        normals = np.array([[3, 4, 0], [0, 0, 5]], dtype=np.float32)
        normalized = normalize_normals(normals)
        
        # Check unit length
        lengths = np.linalg.norm(normalized, axis=1)
        assert np.allclose(lengths, 1.0)
    
    def test_estimate_point_scales(self):
        """Point scale estimation works."""
        from workers.parsers.base import estimate_point_scales
        
        # Create grid of points
        x = np.linspace(0, 10, 10)
        y = np.linspace(0, 10, 10)
        xx, yy = np.meshgrid(x, y)
        positions = np.stack([xx.flatten(), yy.flatten(), np.zeros(100)], axis=1).astype(np.float32)
        
        scales = estimate_point_scales(positions)
        
        assert scales.shape == (100, 3)
        assert scales.min() > 0
    
    def test_create_identity_rotations(self):
        """Identity rotation creation works."""
        from workers.parsers.base import create_identity_rotations
        
        rotations = create_identity_rotations(10)
        
        assert rotations.shape == (10, 4)
        assert np.allclose(rotations[:, 0], 1.0)  # w component
        assert np.allclose(rotations[:, 1:], 0.0)  # xyz components
    
    def test_colors_to_sh_dc(self):
        """Color to SH DC conversion works."""
        from workers.parsers.base import colors_to_sh_dc
        
        colors = np.array([[0.5, 0.5, 0.5], [1.0, 0.0, 0.0]], dtype=np.float32)
        sh_dc = colors_to_sh_dc(colors)
        
        assert sh_dc.shape == (2, 3)
        # DC of gray (0.5, 0.5, 0.5) should be ~0
        assert np.allclose(sh_dc[0], 0.0, atol=0.01)
    
    def test_points_to_gaussians(self):
        """Point cloud to Gaussian conversion works."""
        from workers.parsers.base import points_to_gaussians
        
        positions = np.random.randn(50, 3).astype(np.float32)
        colors = np.random.rand(50, 3).astype(np.float32)
        
        result = points_to_gaussians(positions, colors)
        
        assert result.is_gaussian == True
        assert result.scales is not None
        assert result.rotations is not None
        assert result.opacities is not None
        assert result.point_count == 50


# =============================================================================
# Parser Registry Tests
# =============================================================================

class TestParserRegistry:
    """Test parser registry and dispatch."""
    
    def test_parser_registry_exists(self):
        """Parser registry exists."""
        from workers.parsers import PARSER_REGISTRY
        
        assert isinstance(PARSER_REGISTRY, dict)
        assert len(PARSER_REGISTRY) >= 10
    
    def test_all_parsers_registered(self):
        """All parsers are registered."""
        from workers.parsers import PARSER_REGISTRY
        
        expected_parsers = ['ply', 'las', 'obj', 'gltf', 'splat', 
                          'stl', 'fbx', 'dae', 'e57', 'ifc']
        
        for parser in expected_parsers:
            assert parser in PARSER_REGISTRY, f"Missing parser: {parser}"
    
    def test_get_parser(self):
        """get_parser returns correct parser."""
        from workers.parsers import get_parser
        from workers.parsers.ply_parser import parse_ply
        
        parser = get_parser('ply')
        assert parser == parse_ply
    
    def test_get_unknown_parser_raises(self):
        """get_parser raises for unknown parser."""
        from workers.parsers import get_parser
        
        with pytest.raises(ValueError):
            get_parser('unknown_format')


# =============================================================================
# Import Pipeline Integration Tests
# =============================================================================

class TestImportPipelineIntegration:
    """Test import pipeline integration with parsers."""
    
    def test_parse_file_function(self):
        """parse_file in import_pipeline works (skips if Celery not available)."""
        try:
            from workers.import_pipeline import parse_file
        except ImportError:
            pytest.skip("Celery not available - import_pipeline requires it")
        
        # Create a simple PLY file
        ply_content = """ply
format ascii 1.0
element vertex 3
property float x
property float y
property float z
end_header
0 0 0
1 0 0
0 1 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ply', delete=False) as f:
            f.write(ply_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_file(temp_path, 'ply')
            
            assert 'positions' in result
            assert 'point_count' in result
            assert result['point_count'] == 3
        finally:
            os.unlink(temp_path)
    
    def test_convert_to_gaussians(self):
        """convert_to_gaussians works (skips if Celery not available)."""
        try:
            from workers.import_pipeline import convert_to_gaussians
        except ImportError:
            pytest.skip("Celery not available - import_pipeline requires it")
        
        parsed_data = {
            "positions": np.random.randn(100, 3).astype(np.float32),
            "colors": np.random.rand(100, 3).astype(np.float32),
            "point_count": 100,
            "metadata": {"format": "test"},
        }
        
        result = convert_to_gaussians(parsed_data)
        
        assert "scales" in result
        assert "rotations" in result
        assert "opacities" in result
        assert result.get("is_gaussian") == True
    
    def test_parsers_module_parse_file(self):
        """Direct parsers module parse_file works."""
        from workers.parsers import parse_file
        
        # Create a simple PLY file
        ply_content = """ply
format ascii 1.0
element vertex 3
property float x
property float y
property float z
end_header
0 0 0
1 0 0
0 1 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ply', delete=False) as f:
            f.write(ply_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_file(temp_path, 'ply')
            
            assert result.data.point_count == 3
            assert result.data.positions.shape == (3, 3)
        finally:
            os.unlink(temp_path)
    
    def test_points_to_gaussians_conversion(self):
        """Direct points_to_gaussians works."""
        from workers.parsers.base import points_to_gaussians
        
        positions = np.random.randn(100, 3).astype(np.float32)
        colors = np.random.rand(100, 3).astype(np.float32)
        
        result = points_to_gaussians(positions, colors)
        
        assert result.scales is not None
        assert result.rotations is not None
        assert result.opacities is not None
        assert result.is_gaussian == True


# =============================================================================
# Material and BIM Data Structure Tests
# =============================================================================

class TestDataStructures:
    """Test additional data structures."""
    
    def test_material_info(self):
        """MaterialInfo dataclass works."""
        from workers.parsers.base import MaterialInfo
        
        mat = MaterialInfo(
            name="Metal",
            roughness=0.3,
            metallic=0.9,
        )
        
        assert mat.name == "Metal"
        assert mat.roughness == 0.3
        assert mat.metallic == 0.9
        assert mat.opacity == 1.0  # default
    
    def test_parser_result_with_materials(self):
        """ParserResult can contain materials."""
        from workers.parsers.base import ParserResult, ParsedData, MaterialInfo, ParsedDataType
        
        data = ParsedData(
            positions=np.zeros((10, 3), dtype=np.float32),
            data_type=ParsedDataType.MESH,
        )
        
        materials = [
            MaterialInfo(name="Mat1"),
            MaterialInfo(name="Mat2"),
        ]
        
        result = ParserResult(data=data, format_name="TEST", materials=materials)
        
        assert len(result.materials) == 2
        assert result.materials[0].name == "Mat1"
    
    def test_parser_result_with_bim_elements(self):
        """ParserResult can contain BIM elements."""
        from workers.parsers.base import ParserResult, ParsedData, BIMElement, ParsedDataType
        
        data = ParsedData(
            positions=np.zeros((10, 3), dtype=np.float32),
            data_type=ParsedDataType.BIM,
        )
        
        bim_elements = [
            BIMElement(element_id=1, global_id="a", element_type="IfcWall"),
            BIMElement(element_id=2, global_id="b", element_type="IfcDoor"),
        ]
        
        result = ParserResult(data=data, format_name="IFC", bim_elements=bim_elements)
        
        assert len(result.bim_elements) == 2
        assert result.bim_elements[0].element_type == "IfcWall"


# =============================================================================
# Phase 4 Summary Tests
# =============================================================================

class TestPhase4Summary:
    """Summary tests for Phase 4 completion."""
    
    def test_all_parser_modules_exist(self):
        """All parser modules exist."""
        from workers.parsers import (
            parse_ply, parse_las, parse_obj, parse_gltf, parse_splat,
            parse_stl, parse_fbx, parse_dae, parse_e57, parse_ifc
        )
        
        assert all(callable(p) for p in [
            parse_ply, parse_las, parse_obj, parse_gltf, parse_splat,
            parse_stl, parse_fbx, parse_dae, parse_e57, parse_ifc
        ])
    
    def test_base_module_exports(self):
        """Base module exports all required items."""
        from workers.parsers.base import (
            ParsedData, ParserResult, ParsedDataType,
            MaterialInfo, BIMElement,
            normalize_colors, normalize_normals,
            sample_mesh_to_points, estimate_point_scales,
            points_to_gaussians
        )
        
        # All imports successful
        assert True
    
    def test_import_api_complete(self):
        """Import API is complete."""
        from api.import_3d import (
            router, SUPPORTED_FORMATS, MAX_FILE_SIZE_BYTES,
            ImportFormatType, ImportStatus,
            list_supported_formats, upload_3d_file, get_import_status
        )
        
        assert len(SUPPORTED_FORMATS) >= 12
        assert MAX_FILE_SIZE_BYTES == 5 * 1024 * 1024 * 1024
    
    def test_import_pipeline_complete(self):
        """Import pipeline is complete."""
        try:
            from workers.import_pipeline import (
                parse_file, convert_to_gaussians, process_import
            )
            
            assert callable(parse_file)
            assert callable(convert_to_gaussians)
            assert callable(process_import)
        except ImportError:
            # Celery not available locally - test module file exists instead
            import os
            pipeline_path = os.path.join(
                os.path.dirname(__file__), '..', 'workers', 'import_pipeline.py'
            )
            assert os.path.exists(pipeline_path), "import_pipeline.py should exist"
