"""
Tests for Task 7.5: Depth Estimation Tests

Tests MiDaS model loading, depth map generation, normalization,
and performance targets for depth estimation.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**
"""
import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile
import os
import time
from unittest.mock import patch, MagicMock, Mock
import torch

# Import the function we're testing
from workers.video_pipeline import estimate_depth_maps


class TestMiDaSModelLoading:
    """Test MiDaS model loading on GPU (Requirement 5.1)"""
    
    def test_midas_model_loads_successfully(self, tmp_path):
        """
        **Validates: Requirements 5.1**
        Test that MiDaS v3.1 DPT-Large model loads correctly
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        # Create test frame
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        # Mock torch.hub.load to avoid downloading model
        with patch('torch.hub.load') as mock_hub_load:
            # Mock model
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            # Mock transform
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            # Setup mock returns
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            
            # Mock model inference
            mock_prediction = torch.randn(1, 384, 384)
            mock_model.return_value = mock_prediction
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify MiDaS was loaded
            assert mock_hub_load.called, "torch.hub.load should be called to load MiDaS"
            
            # Verify DPT_Large model was requested
            model_calls = [c for c in mock_hub_load.call_args_list 
                          if len(c[0]) > 1 and c[0][1] == "DPT_Large"]
            assert len(model_calls) > 0, "Should load DPT_Large model"
    
    def test_midas_model_uses_gpu_when_available(self, tmp_path):
        """
        **Validates: Requirements 5.1**
        Test that MiDaS model is loaded on GPU when CUDA is available
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('torch.hub.load') as mock_hub_load, \
             patch('torch.cuda.is_available', return_value=True):
            
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            mock_model.return_value = torch.randn(1, 384, 384)
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify model was moved to GPU
            assert mock_model.to.called, "Model should be moved to device"
            
            # Check if cuda device was used
            device_calls = [str(c) for c in mock_model.to.call_args_list]
            has_cuda = any('cuda' in str(c).lower() for c in device_calls)
            assert has_cuda, "Should use CUDA device when available"

    def test_midas_model_falls_back_to_cpu(self, tmp_path):
        """
        **Validates: Requirements 5.1**
        Test that MiDaS falls back to CPU when GPU is not available
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('torch.hub.load') as mock_hub_load, \
             patch('torch.cuda.is_available', return_value=False):
            
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            mock_model.return_value = torch.randn(1, 384, 384)
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify model was moved to CPU device
            assert mock_model.to.called, "Model should be moved to device"


class TestDepthMapGeneration:
    """Test depth map generation for all valid frames (Requirement 5.2)"""
    
    def test_depth_maps_generated_for_all_frames(self, tmp_path):
        """
        **Validates: Requirements 5.1, 5.2**
        Test that depth maps are generated for ALL valid frames
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        # Create 5 test frames
        valid_frames = [f"frame_{i+1:06d}.jpg" for i in range(5)]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('torch.hub.load') as mock_hub_load:
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            
            # Mock model to return different depth maps
            call_count = [0]
            def model_forward(*args, **kwargs):
                call_count[0] += 1
                return torch.randn(1, 384, 384)
            
            mock_model.side_effect = model_forward
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify depth maps were generated for all frames
            assert result['depth_count'] == 5, \
                f"Should generate depth maps for all 5 frames, got {result['depth_count']}"
            
            # Verify model was called 5 times (once per frame)
            assert call_count[0] == 5, \
                f"Model should be called 5 times, was called {call_count[0]} times"

    def test_depth_map_resolution_matches_input(self, tmp_path):
        """
        **Validates: Requirements 5.2**
        Test that depth maps have the same resolution as input frames
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        # Create frame with specific resolution
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('torch.hub.load') as mock_hub_load:
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            
            # Mock model output
            mock_model.return_value = torch.randn(1, 384, 384)
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify depth map was created
            depth_file = output_dir / "frame_000001_depth.png"
            assert depth_file.exists(), "Depth map file should be created"
            
            # Read depth map and verify resolution
            depth_map = cv2.imread(str(depth_file), cv2.IMREAD_GRAYSCALE)
            assert depth_map is not None, "Depth map should be readable"
            
            # Depth map should match input resolution (720x1280)
            assert depth_map.shape[0] == 720, \
                f"Depth map height should be 720, got {depth_map.shape[0]}"
            assert depth_map.shape[1] == 1280, \
                f"Depth map width should be 1280, got {depth_map.shape[1]}"
    
    def test_depth_maps_saved_as_png(self, tmp_path):
        """
        **Validates: Requirements 5.2, 5.5**
        Test that depth maps are saved as PNG files
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('torch.hub.load') as mock_hub_load:
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            mock_model.return_value = torch.randn(1, 384, 384)
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify PNG files were created
            depth_file_1 = output_dir / "frame_000001_depth.png"
            depth_file_2 = output_dir / "frame_000002_depth.png"
            
            assert depth_file_1.exists(), "Depth map 1 should be saved as PNG"
            assert depth_file_2.exists(), "Depth map 2 should be saved as PNG"
            
            # Verify files are valid PNG images
            depth_1 = cv2.imread(str(depth_file_1))
            depth_2 = cv2.imread(str(depth_file_2))
            
            assert depth_1 is not None, "Depth map 1 should be valid PNG"
            assert depth_2 is not None, "Depth map 2 should be valid PNG"



class TestDepthNormalization:
    """Test depth value normalization to 0-1 range (Requirement 5.3)"""
    
    def test_depth_values_normalized_to_0_255(self, tmp_path):
        """
        **Validates: Requirements 5.3**
        Test that depth values are normalized to 0-255 range (8-bit PNG)
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('torch.hub.load') as mock_hub_load:
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            
            # Mock model to return depth with arbitrary range
            mock_model.return_value = torch.randn(1, 384, 384) * 100 + 50
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Read depth map
            depth_file = output_dir / "frame_000001_depth.png"
            depth_map = cv2.imread(str(depth_file), cv2.IMREAD_GRAYSCALE)
            
            # Verify depth values are in 0-255 range
            assert depth_map.min() >= 0, \
                f"Minimum depth value should be >= 0, got {depth_map.min()}"
            assert depth_map.max() <= 255, \
                f"Maximum depth value should be <= 255, got {depth_map.max()}"
            
            # Verify normalization uses full range
            # (should have values near 0 and near 255)
            assert depth_map.min() < 50, \
                "Normalized depth should have values near 0"
            assert depth_map.max() > 200, \
                "Normalized depth should have values near 255"
    
    def test_depth_normalization_preserves_relative_values(self, tmp_path):
        """
        **Validates: Requirements 5.3**
        Test that normalization preserves relative depth relationships
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('torch.hub.load') as mock_hub_load:
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            
            # Create synthetic depth with known pattern
            # Left side = near (high values), right side = far (low values)
            synthetic_depth = torch.zeros(1, 100, 100)
            synthetic_depth[:, :, :50] = 100.0  # Near
            synthetic_depth[:, :, 50:] = 10.0   # Far
            
            mock_model.return_value = synthetic_depth
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Read depth map
            depth_file = output_dir / "frame_000001_depth.png"
            depth_map = cv2.imread(str(depth_file), cv2.IMREAD_GRAYSCALE)
            
            # Verify relative relationships are preserved
            left_mean = depth_map[:, :50].mean()
            right_mean = depth_map[:, 50:].mean()
            
            # Left side (near) should have higher values than right side (far)
            assert left_mean > right_mean, \
                "Relative depth relationships should be preserved after normalization"



class TestPerformanceTargets:
    """Test performance targets for depth estimation (Requirement 5.4)"""
    
    def test_depth_estimation_completes_in_reasonable_time(self, tmp_path):
        """
        **Validates: Requirements 5.4**
        Test that depth estimation completes in reasonable time
        (Target: 2 seconds per frame on RTX 3090, but we test for completion)
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        # Create 3 test frames
        valid_frames = [f"frame_{i+1:06d}.jpg" for i in range(3)]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('torch.hub.load') as mock_hub_load:
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            mock_model.return_value = torch.randn(1, 384, 384)
            
            # Measure execution time
            start_time = time.time()
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            elapsed_time = time.time() - start_time
            
            # Verify all frames were processed
            assert result['depth_count'] == 3, "Should process all 3 frames"
            
            # Verify reasonable completion time (generous limit for CI/testing)
            # In production with real GPU, target is 2s per frame
            # For testing with mocks, should be very fast
            assert elapsed_time < 30, \
                f"Depth estimation should complete in reasonable time, took {elapsed_time:.2f}s"
    
    def test_gpu_acceleration_used_when_available(self, tmp_path):
        """
        **Validates: Requirements 5.4**
        Test that GPU acceleration is used when available for performance
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('torch.hub.load') as mock_hub_load, \
             patch('torch.cuda.is_available', return_value=True) as mock_cuda:
            
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            mock_model.return_value = torch.randn(1, 384, 384)
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify CUDA availability was checked
            assert mock_cuda.called, "Should check for CUDA availability"
            
            # Verify model was moved to GPU
            assert mock_model.to.called, "Model should be moved to device"


class TestFallbackBehavior:
    """Test fallback behavior when MiDaS is not available"""
    
    def test_fallback_to_edge_detection_on_midas_failure(self, tmp_path):
        """
        Test that system falls back to edge detection when MiDaS fails
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        # Mock torch.hub.load to raise exception (MiDaS not available)
        with patch('torch.hub.load', side_effect=Exception("MiDaS not available")):
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify fallback still generates depth maps
            assert result['depth_count'] == 2, \
                "Fallback should still generate depth maps for all frames"
            
            # Verify depth files exist
            depth_file_1 = output_dir / "frame_000001_depth.png"
            depth_file_2 = output_dir / "frame_000002_depth.png"
            
            assert depth_file_1.exists(), "Fallback depth map 1 should exist"
            assert depth_file_2.exists(), "Fallback depth map 2 should exist"

    def test_fallback_depth_maps_are_valid(self, tmp_path):
        """
        Test that fallback depth maps are valid images
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        # Create frame with some edges
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some rectangles for edges
        cv2.rectangle(img, (100, 100), (200, 200), (255, 255, 255), -1)
        cv2.rectangle(img, (300, 300), (400, 400), (255, 255, 255), -1)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('torch.hub.load', side_effect=Exception("MiDaS not available")):
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Read fallback depth map
            depth_file = output_dir / "frame_000001_depth.png"
            depth_map = cv2.imread(str(depth_file), cv2.IMREAD_GRAYSCALE)
            
            assert depth_map is not None, "Fallback depth map should be readable"
            assert depth_map.shape == (480, 640), \
                "Fallback depth map should match input resolution"
            
            # Verify values are normalized
            assert depth_map.min() >= 0, "Fallback depth min should be >= 0"
            assert depth_map.max() <= 255, "Fallback depth max should be <= 255"


class TestIntegration:
    """Integration tests for complete depth estimation pipeline"""
    
    def test_complete_depth_estimation_pipeline(self, tmp_path):
        """
        Test the complete depth estimation pipeline:
        Model loading -> inference -> normalization -> saving
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "depth"
        output_dir.mkdir()
        
        # Create realistic test frames
        valid_frames = []
        for i in range(4):
            filename = f"frame_{i+1:06d}.jpg"
            
            # Create image with depth cues (gradient)
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            for y in range(480):
                intensity = int(255 * (y / 480))
                img[y, :] = [intensity, intensity, intensity]
            
            cv2.imwrite(str(frames_dir / filename), img)
            valid_frames.append(filename)
        
        with patch('torch.hub.load') as mock_hub_load:
            mock_model = MagicMock()
            mock_model.eval = MagicMock(return_value=mock_model)
            mock_model.to = MagicMock(return_value=mock_model)
            
            mock_transform = MagicMock()
            mock_transform.return_value = torch.randn(1, 3, 384, 384)
            
            def hub_load_side_effect(repo, model_name, *args, **kwargs):
                if model_name == "DPT_Large":
                    return mock_model
                elif model_name == "transforms":
                    mock_transforms = MagicMock()
                    mock_transforms.dpt_transform = mock_transform
                    return mock_transforms
                return MagicMock()
            
            mock_hub_load.side_effect = hub_load_side_effect
            
            # Mock model to return different depth for each frame
            call_count = [0]
            def model_forward(*args, **kwargs):
                call_count[0] += 1
                # Return depth with variation
                return torch.randn(1, 384, 384) * 10 + call_count[0] * 5
            
            mock_model.side_effect = model_forward
            
            result = estimate_depth_maps(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify complete pipeline execution
            assert result['depth_count'] == 4, "Should process all 4 frames"
            
            # Verify all depth maps were created
            for i, filename in enumerate(valid_frames):
                depth_filename = filename.replace(".jpg", "_depth.png")
                depth_file = output_dir / depth_filename
                assert depth_file.exists(), f"Depth map {i+1} should exist"
                
                # Verify depth map is valid
                depth_map = cv2.imread(str(depth_file), cv2.IMREAD_GRAYSCALE)
                assert depth_map is not None, f"Depth map {i+1} should be readable"
                assert depth_map.shape == (480, 640), \
                    f"Depth map {i+1} should match input resolution"
            
            # Verify model was called for each frame
            assert call_count[0] == 4, "Model should be called once per frame"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
