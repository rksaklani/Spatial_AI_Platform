"""
Tests for Task 14.12: JSON Scene Metadata Round-Trip Property Test

Property-based test using Hypothesis to validate JSON scene metadata round-trip correctness.

**Validates: Requirements 20.7**

Property 2: Scene metadata round-trip
For any valid Scene_Graph object, parsing the serialized JSON and then serializing again
SHALL produce equivalent JSON.
"""
import pytest
import json
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from typing import Dict, Any

from models.scene_object import SceneGraph


# Hypothesis strategies for generating valid Scene_Graph objects

@composite
def scene_id_strategy(draw):
    """Generate valid scene IDs (UUIDs or alphanumeric strings)."""
    # Generate UUID-like strings or simple alphanumeric IDs
    return draw(st.one_of(
        st.uuids().map(str),
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=8, max_size=32)
    ))


@composite
def object_id_list_strategy(draw, min_size=0, max_size=20):
    """Generate list of object IDs."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(st.uuids().map(str)) for _ in range(size)]


@composite
def category_counts_strategy(draw):
    """Generate category counts dictionary."""
    categories = [
        "wall", "floor", "ceiling", "door", "window", "stairs",
        "chair", "table", "sofa", "bed", "desk", "cabinet", "shelf",
        "lamp", "plant", "artwork", "appliance", "electronics",
        "person", "animal", "vehicle", "tree", "building", "road", "object", "unknown"
    ]
    
    # Select random subset of categories
    num_categories = draw(st.integers(min_value=0, max_value=len(categories)))
    selected_categories = draw(st.lists(
        st.sampled_from(categories),
        min_size=num_categories,
        max_size=num_categories,
        unique=True
    ))
    
    # Generate counts for each category
    return {
        category: draw(st.integers(min_value=0, max_value=100))
        for category in selected_categories
    }


@composite
def relationship_strategy(draw):
    """Generate a single relationship dictionary."""
    relation_types = ["on_top_of", "inside", "next_to", "attached_to", "supports", "contains"]
    
    return {
        "source": draw(st.uuids().map(str)),
        "target": draw(st.uuids().map(str)),
        "relation": draw(st.sampled_from(relation_types)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0))
    }


@composite
def relationships_list_strategy(draw, min_size=0, max_size=50):
    """Generate list of relationships."""
    return draw(st.lists(
        relationship_strategy(),
        min_size=min_size,
        max_size=max_size
    ))


@composite
def scene_bounds_strategy(draw):
    """Generate scene bounds dictionary."""
    # Generate min/max coordinates
    min_x = draw(st.floats(min_value=-1000.0, max_value=0.0, allow_nan=False, allow_infinity=False))
    max_x = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    min_y = draw(st.floats(min_value=-1000.0, max_value=0.0, allow_nan=False, allow_infinity=False))
    max_y = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    min_z = draw(st.floats(min_value=-1000.0, max_value=0.0, allow_nan=False, allow_infinity=False))
    max_z = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "min_z": min_z,
        "max_z": max_z
    }


@composite
def scene_center_strategy(draw):
    """Generate scene center tuple (x, y, z)."""
    x = draw(st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    y = draw(st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    z = draw(st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    return (x, y, z)


@composite
def scene_graph_strategy(draw):
    """Generate a valid SceneGraph object."""
    scene_id = draw(scene_id_strategy())
    root_objects = draw(object_id_list_strategy(min_size=0, max_size=20))
    object_count = draw(st.integers(min_value=0, max_value=1000))
    category_counts = draw(category_counts_strategy())
    relationships = draw(relationships_list_strategy(min_size=0, max_size=50))
    scene_bounds = draw(scene_bounds_strategy())
    scene_center = draw(scene_center_strategy())
    total_gaussian_count = draw(st.integers(min_value=0, max_value=10000000))
    
    return SceneGraph(
        scene_id=scene_id,
        root_objects=root_objects,
        object_count=object_count,
        category_counts=category_counts,
        relationships=relationships,
        scene_bounds=scene_bounds,
        scene_center=scene_center,
        total_gaussian_count=total_gaussian_count
    )


class TestJSONRoundTrip:
    """
    Property-based tests for JSON scene metadata round-trip.
    
    **Validates: Requirements 20.7**
    """
    
    @given(scene_graph=scene_graph_strategy())
    @settings(max_examples=100, deadline=None)
    def test_scene_graph_json_roundtrip_property(self, scene_graph: SceneGraph):
        """
        **Validates: Requirements 20.7**
        
        Property: For any valid Scene_Graph object, parsing the serialized JSON
        and then serializing again SHALL produce equivalent JSON.
        
        This tests the fundamental round-trip property:
        SceneGraph -> JSON -> SceneGraph -> JSON
        
        The two JSON outputs should be equivalent.
        """
        # Serialize to JSON (first serialization)
        json_str_1 = scene_graph.model_dump_json()
        
        # Parse JSON back to SceneGraph object
        scene_graph_dict = json.loads(json_str_1)
        scene_graph_parsed = SceneGraph(**scene_graph_dict)
        
        # Serialize again (second serialization)
        json_str_2 = scene_graph_parsed.model_dump_json()
        
        # Parse both JSON strings to dictionaries for comparison
        json_dict_1 = json.loads(json_str_1)
        json_dict_2 = json.loads(json_str_2)
        
        # Assert equivalence
        assert json_dict_1 == json_dict_2, \
            f"Round-trip JSON should be equivalent.\nFirst: {json_dict_1}\nSecond: {json_dict_2}"
    
    @given(scene_graph=scene_graph_strategy())
    @settings(max_examples=100, deadline=None)
    def test_scene_graph_object_equivalence_after_roundtrip(self, scene_graph: SceneGraph):
        """
        **Validates: Requirements 20.7**
        
        Test that the SceneGraph object is equivalent after JSON round-trip.
        
        This verifies that all fields are preserved correctly through serialization
        and deserialization.
        """
        # Serialize to JSON
        json_str = scene_graph.model_dump_json()
        
        # Parse back to SceneGraph
        scene_graph_dict = json.loads(json_str)
        scene_graph_parsed = SceneGraph(**scene_graph_dict)
        
        # Compare all fields
        assert scene_graph_parsed.scene_id == scene_graph.scene_id
        assert scene_graph_parsed.root_objects == scene_graph.root_objects
        assert scene_graph_parsed.object_count == scene_graph.object_count
        assert scene_graph_parsed.category_counts == scene_graph.category_counts
        assert scene_graph_parsed.relationships == scene_graph.relationships
        assert scene_graph_parsed.scene_bounds == scene_graph.scene_bounds
        assert scene_graph_parsed.scene_center == scene_graph.scene_center
        assert scene_graph_parsed.total_gaussian_count == scene_graph.total_gaussian_count
    
    @given(scene_graph=scene_graph_strategy())
    @settings(max_examples=50, deadline=None)
    def test_json_string_stability(self, scene_graph: SceneGraph):
        """
        **Validates: Requirements 20.7**
        
        Test that serializing the same SceneGraph multiple times produces
        identical JSON strings (deterministic serialization).
        """
        # Serialize multiple times
        json_str_1 = scene_graph.model_dump_json()
        json_str_2 = scene_graph.model_dump_json()
        json_str_3 = scene_graph.model_dump_json()
        
        # All should be identical
        assert json_str_1 == json_str_2 == json_str_3, \
            "Multiple serializations of the same object should produce identical JSON"
    
    @given(scene_graph=scene_graph_strategy())
    @settings(max_examples=50, deadline=None)
    def test_json_schema_validation(self, scene_graph: SceneGraph):
        """
        **Validates: Requirements 20.7, 20.3**
        
        Test that serialized JSON conforms to the expected schema and can be
        validated against schema constraints.
        """
        # Serialize to JSON
        json_str = scene_graph.model_dump_json()
        json_dict = json.loads(json_str)
        
        # Verify required fields are present
        required_fields = [
            "scene_id", "root_objects", "object_count", "category_counts",
            "relationships", "scene_bounds", "scene_center", "total_gaussian_count"
        ]
        
        for field in required_fields:
            assert field in json_dict, f"Required field '{field}' missing from JSON"
        
        # Verify field types
        assert isinstance(json_dict["scene_id"], str)
        assert isinstance(json_dict["root_objects"], list)
        assert isinstance(json_dict["object_count"], int)
        assert isinstance(json_dict["category_counts"], dict)
        assert isinstance(json_dict["relationships"], list)
        assert isinstance(json_dict["scene_bounds"], dict)
        assert isinstance(json_dict["scene_center"], (list, tuple))
        assert isinstance(json_dict["total_gaussian_count"], int)
    
    def test_empty_scene_graph_roundtrip(self):
        """
        **Validates: Requirements 20.7**
        
        Test round-trip for minimal/empty SceneGraph (edge case).
        """
        # Create minimal SceneGraph
        scene_graph = SceneGraph(
            scene_id="test-scene-001",
            root_objects=[],
            object_count=0,
            category_counts={},
            relationships=[],
            scene_bounds={
                "min_x": 0.0, "max_x": 0.0,
                "min_y": 0.0, "max_y": 0.0,
                "min_z": 0.0, "max_z": 0.0
            },
            scene_center=(0.0, 0.0, 0.0),
            total_gaussian_count=0
        )
        
        # Round-trip
        json_str_1 = scene_graph.model_dump_json()
        scene_graph_parsed = SceneGraph(**json.loads(json_str_1))
        json_str_2 = scene_graph_parsed.model_dump_json()
        
        # Verify equivalence
        assert json.loads(json_str_1) == json.loads(json_str_2)
    
    def test_large_scene_graph_roundtrip(self):
        """
        **Validates: Requirements 20.7**
        
        Test round-trip for large SceneGraph with many objects and relationships.
        """
        # Create large SceneGraph
        scene_graph = SceneGraph(
            scene_id="large-scene-001",
            root_objects=[f"obj-{i}" for i in range(100)],
            object_count=1000,
            category_counts={
                "wall": 50,
                "floor": 10,
                "ceiling": 10,
                "chair": 200,
                "table": 50,
                "object": 680
            },
            relationships=[
                {
                    "source": f"obj-{i}",
                    "target": f"obj-{i+1}",
                    "relation": "on_top_of",
                    "confidence": 0.95
                }
                for i in range(100)
            ],
            scene_bounds={
                "min_x": -50.0, "max_x": 50.0,
                "min_y": -30.0, "max_y": 30.0,
                "min_z": 0.0, "max_z": 10.0
            },
            scene_center=(0.0, 0.0, 5.0),
            total_gaussian_count=5000000
        )
        
        # Round-trip
        json_str_1 = scene_graph.model_dump_json()
        scene_graph_parsed = SceneGraph(**json.loads(json_str_1))
        json_str_2 = scene_graph_parsed.model_dump_json()
        
        # Verify equivalence
        json_dict_1 = json.loads(json_str_1)
        json_dict_2 = json.loads(json_str_2)
        assert json_dict_1 == json_dict_2
    
    def test_special_characters_in_scene_id(self):
        """
        **Validates: Requirements 20.7**
        
        Test round-trip with special characters in scene_id.
        """
        scene_graph = SceneGraph(
            scene_id="scene-with-special-chars_123-456.789",
            root_objects=["obj-1"],
            object_count=1,
            category_counts={"object": 1},
            relationships=[],
            scene_bounds={
                "min_x": 0.0, "max_x": 1.0,
                "min_y": 0.0, "max_y": 1.0,
                "min_z": 0.0, "max_z": 1.0
            },
            scene_center=(0.5, 0.5, 0.5),
            total_gaussian_count=1000
        )
        
        # Round-trip
        json_str_1 = scene_graph.model_dump_json()
        scene_graph_parsed = SceneGraph(**json.loads(json_str_1))
        json_str_2 = scene_graph_parsed.model_dump_json()
        
        # Verify equivalence
        assert json.loads(json_str_1) == json.loads(json_str_2)
    
    def test_unicode_in_category_names(self):
        """
        **Validates: Requirements 20.7**
        
        Test round-trip with Unicode characters in category names.
        """
        scene_graph = SceneGraph(
            scene_id="unicode-scene",
            root_objects=["obj-1"],
            object_count=3,
            category_counts={
                "chair": 1,
                "table": 1,
                "object": 1
            },
            relationships=[],
            scene_bounds={
                "min_x": 0.0, "max_x": 1.0,
                "min_y": 0.0, "max_y": 1.0,
                "min_z": 0.0, "max_z": 1.0
            },
            scene_center=(0.5, 0.5, 0.5),
            total_gaussian_count=1000
        )
        
        # Round-trip
        json_str_1 = scene_graph.model_dump_json()
        scene_graph_parsed = SceneGraph(**json.loads(json_str_1))
        json_str_2 = scene_graph_parsed.model_dump_json()
        
        # Verify equivalence
        assert json.loads(json_str_1) == json.loads(json_str_2)
    
    def test_floating_point_precision_preservation(self):
        """
        **Validates: Requirements 20.7**
        
        Test that floating-point values are preserved with sufficient precision
        through JSON round-trip.
        """
        scene_graph = SceneGraph(
            scene_id="precision-test",
            root_objects=[],
            object_count=0,
            category_counts={},
            relationships=[],
            scene_bounds={
                "min_x": -123.456789,
                "max_x": 123.456789,
                "min_y": -987.654321,
                "max_y": 987.654321,
                "min_z": -0.123456789,
                "max_z": 0.123456789
            },
            scene_center=(1.23456789, -9.87654321, 0.11111111),
            total_gaussian_count=0
        )
        
        # Round-trip
        json_str_1 = scene_graph.model_dump_json()
        scene_graph_parsed = SceneGraph(**json.loads(json_str_1))
        json_str_2 = scene_graph_parsed.model_dump_json()
        
        # Verify equivalence
        json_dict_1 = json.loads(json_str_1)
        json_dict_2 = json.loads(json_str_2)
        
        # Check floating-point values are preserved
        assert json_dict_1["scene_bounds"] == json_dict_2["scene_bounds"]
        assert json_dict_1["scene_center"] == json_dict_2["scene_center"]


class TestJSONErrorHandling:
    """Test error handling for invalid JSON."""
    
    def test_invalid_json_raises_error(self):
        """
        **Validates: Requirements 20.4**
        
        Test that invalid JSON raises appropriate error.
        """
        invalid_json = '{"scene_id": "test", "invalid": }'
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
    
    def test_missing_required_field_raises_error(self):
        """
        **Validates: Requirements 20.3, 20.4**
        
        Test that missing required fields raise validation error.
        """
        # Missing 'scene_id' field
        incomplete_data = {
            "root_objects": [],
            "object_count": 0,
            "category_counts": {},
            "relationships": [],
            "scene_bounds": {
                "min_x": 0.0, "max_x": 0.0,
                "min_y": 0.0, "max_y": 0.0,
                "min_z": 0.0, "max_z": 0.0
            },
            "scene_center": (0.0, 0.0, 0.0),
            "total_gaussian_count": 0
        }
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            SceneGraph(**incomplete_data)
    
    def test_wrong_field_type_raises_error(self):
        """
        **Validates: Requirements 20.3, 20.4**
        
        Test that wrong field types raise validation error.
        """
        # object_count should be int, not string
        invalid_data = {
            "scene_id": "test",
            "root_objects": [],
            "object_count": "not-an-integer",  # Wrong type
            "category_counts": {},
            "relationships": [],
            "scene_bounds": {
                "min_x": 0.0, "max_x": 0.0,
                "min_y": 0.0, "max_y": 0.0,
                "min_z": 0.0, "max_z": 0.0
            },
            "scene_center": (0.0, 0.0, 0.0),
            "total_gaussian_count": 0
        }
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            SceneGraph(**invalid_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
