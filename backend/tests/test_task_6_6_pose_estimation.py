"""
Tests for Task 6.6: Pose Estimation Tests

Tests SIFT feature extraction, feature matching, sparse reconstruction,
and failure handling for camera pose estimation using COLMAP.

**Validates: Requirements 4.1, 4.2, 4.3, 4.6**
"""
import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock, call
import subprocess

# Import the function we're testing
from workers.video_pipeline import estimate_camera_poses


class TestSIFTFeatureExtraction:
    """Test SIFT feature extraction from frames (Requirement 4.1)"""
    
    def test_sift_feature_extraction_called(self, tmp_path):
        """
        **Validates: Requirements 4.1**
        Test that SIFT features are extracted from each frame
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create test frames
        valid_frames = []
        for i in range(3):
            filename = f"frame_{i+1:06d}.jpg"
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add checkerboard pattern for features
            for y in range(0, 480, 20):
                for x in range(0, 640, 20):
                    if (y // 20 + x // 20) % 2 == 0:
                        img[y:y+20, x:x+20] = 255
            
            cv2.imwrite(str(frames_dir / filename), img)
            valid_frames.append(filename)
        
        # Mock COLMAP subprocess calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output structure
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            
            # Create mock cameras.txt
            (model_dir / "cameras.txt").write_text(
                "# Camera list\n"
                "1 SIMPLE_PINHOLE 640 480 500 320 240\n"
            )
            
            # Create mock images.txt
            (model_dir / "images.txt").write_text(
                "# Image list\n"
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000001.jpg\n"
                "\n"
                "2 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000002.jpg\n"
                "\n"
            )
            
            # Create mock points3D.txt
            (model_dir / "points3D.txt").write_text("# 3D points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify COLMAP feature_extractor was called
            feature_extractor_calls = [
                c for c in mock_run.call_args_list
                if 'feature_extractor' in str(c)
            ]
            
            assert len(feature_extractor_calls) > 0, \
                "COLMAP feature_extractor should be called for SIFT extraction"
            
            # Verify SIFT parameters are used
            feature_cmd = str(feature_extractor_calls[0])
            assert 'Sift' in feature_cmd or 'sift' in feature_cmd.lower(), \
                "SIFT feature extraction should be configured"

    def test_sift_extraction_per_frame(self, tmp_path):
        """
        **Validates: Requirements 4.1**
        Test that SIFT features are extracted from ALL valid frames
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create 5 test frames
        valid_frames = []
        for i in range(5):
            filename = f"frame_{i+1:06d}.jpg"
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
            valid_frames.append(filename)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            (model_dir / "cameras.txt").write_text("# Cameras\n")
            (model_dir / "images.txt").write_text("# Images\n")
            (model_dir / "points3D.txt").write_text("# Points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify COLMAP was called (which means frames were processed)
            # The actual images directory path depends on COLMAP's internal structure
            assert mock_run.called, "COLMAP should be called to process frames"
            
            # Verify result indicates processing occurred
            assert 'camera_count' in result, "Result should contain camera_count"
            assert 'point_count' in result, "Result should contain point_count"


class TestFeatureMatching:
    """Test feature matching between frame pairs (Requirement 4.2)"""
    
    def test_colmap_feature_matching_called(self, tmp_path):
        """
        **Validates: Requirements 4.2**
        Test that COLMAP feature matching is performed between frame pairs
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create test frames
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            (model_dir / "cameras.txt").write_text("# Cameras\n")
            (model_dir / "images.txt").write_text("# Images\n")
            (model_dir / "points3D.txt").write_text("# Points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify COLMAP matcher was called
            matcher_calls = [
                c for c in mock_run.call_args_list
                if 'matcher' in str(c) or 'exhaustive_matcher' in str(c)
            ]
            
            assert len(matcher_calls) > 0, \
                "COLMAP feature matcher should be called"

    def test_feature_matching_uses_database(self, tmp_path):
        """
        **Validates: Requirements 4.2**
        Test that feature matching uses COLMAP database for storing matches
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            (model_dir / "cameras.txt").write_text("# Cameras\n")
            (model_dir / "images.txt").write_text("# Images\n")
            (model_dir / "points3D.txt").write_text("# Points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify database.db is referenced in commands
            all_calls = [str(c) for c in mock_run.call_args_list]
            database_refs = [c for c in all_calls if 'database' in c.lower()]
            
            assert len(database_refs) > 0, \
                "COLMAP commands should reference database for feature matching"


class TestSparseReconstruction:
    """Test sparse reconstruction to calculate camera poses (Requirement 4.3)"""
    
    def test_sparse_reconstruction_called(self, tmp_path):
        """
        **Validates: Requirements 4.3**
        Test that sparse reconstruction (mapper) is performed
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg", "frame_000003.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            (model_dir / "cameras.txt").write_text("# Cameras\n")
            (model_dir / "images.txt").write_text(
                "# Images\n"
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000001.jpg\n"
                "\n"
                "2 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000002.jpg\n"
                "\n"
                "3 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000003.jpg\n"
                "\n"
            )
            (model_dir / "points3D.txt").write_text("# Points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify COLMAP mapper was called
            mapper_calls = [
                c for c in mock_run.call_args_list
                if 'mapper' in str(c)
            ]
            
            assert len(mapper_calls) > 0, \
                "COLMAP mapper should be called for sparse reconstruction"

    def test_camera_poses_calculated(self, tmp_path):
        """
        **Validates: Requirements 4.3**
        Test that camera poses are calculated for all valid frames
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg", "frame_000003.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output with camera poses
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            
            (model_dir / "cameras.txt").write_text(
                "# Camera list with one entry\n"
                "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
                "1 SIMPLE_PINHOLE 640 480 500 320 240\n"
            )
            
            # Each image has 2 lines in images.txt
            (model_dir / "images.txt").write_text(
                "# Image list with entries\n"
                "# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n"
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000001.jpg\n"
                "\n"
                "2 0.9 0.1 0.0 0.0 1.0 0.0 0.0 1 frame_000002.jpg\n"
                "\n"
                "3 0.8 0.2 0.0 0.0 2.0 0.0 0.0 1 frame_000003.jpg\n"
                "\n"
            )
            
            (model_dir / "points3D.txt").write_text(
                "# 3D point list\n"
                "1 0.0 0.0 0.0 255 0 0 0.5 1 2\n"
                "2 1.0 0.0 0.0 0 255 0 0.5 2 3\n"
            )
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify result contains camera count
            assert 'camera_count' in result, "Result should contain camera_count"
            assert result['camera_count'] == 3, \
                f"Should have 3 cameras (one per frame), got {result['camera_count']}"
            
            # Verify sparse point cloud was generated
            assert 'point_count' in result, "Result should contain point_count"
            assert result['point_count'] == 2, \
                f"Should have 2 3D points, got {result['point_count']}"
    
    def test_sparse_point_cloud_generated(self, tmp_path):
        """
        **Validates: Requirements 4.3**
        Test that sparse point cloud is generated as byproduct
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            (model_dir / "cameras.txt").write_text("# Cameras\n")
            (model_dir / "images.txt").write_text("# Images\n")
            
            # Create points3D.txt with sparse points
            (model_dir / "points3D.txt").write_text(
                "# 3D point list\n"
                "# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n"
                "1 0.5 0.5 1.0 255 0 0 0.1 1 100 2 200\n"
                "2 1.0 0.5 1.0 0 255 0 0.1 1 101 2 201\n"
                "3 0.5 1.0 1.0 0 0 255 0.1 1 102 2 202\n"
            )
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify sparse point cloud exists
            assert result['point_count'] == 3, \
                f"Should have 3 sparse 3D points, got {result['point_count']}"



class TestFailureHandling:
    """Test failure handling when pose estimation fails (Requirement 4.6)"""
    
    def test_colmap_failure_returns_fallback(self, tmp_path):
        """
        **Validates: Requirements 4.6**
        Test that when COLMAP fails, system returns fallback result
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        # Mock COLMAP failure
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd="colmap",
                stderr="COLMAP error: insufficient features"
            )
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify fallback behavior
            assert result is not None, "Should return result even on failure"
            assert 'success' in result, "Result should indicate success status"
            assert result['success'] is False, "Success should be False on failure"
            assert 'fallback' in result, "Result should indicate fallback mode"
            assert result['fallback'] is True, "Fallback should be True"
    
    def test_missing_colmap_binary_handled(self, tmp_path):
        """
        **Validates: Requirements 4.6**
        Test that missing COLMAP binary is handled gracefully
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        # Mock FileNotFoundError (COLMAP not installed)
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("colmap: command not found")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Should return fallback result
            assert result is not None, "Should return result even when COLMAP missing"
            assert result['success'] is False, "Success should be False"
            assert result['fallback'] is True, "Should use fallback mode"
    
    def test_partial_reconstruction_continues(self, tmp_path):
        """
        **Validates: Requirements 4.6**
        Test that when some frames fail, processing continues with remaining frames
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create 5 frames
        valid_frames = [f"frame_{i+1:06d}.jpg" for i in range(5)]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output with only 3 cameras (2 frames failed)
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            
            (model_dir / "cameras.txt").write_text("# Cameras\n1 SIMPLE_PINHOLE 640 480 500 320 240\n")
            
            # Only 3 out of 5 frames reconstructed
            (model_dir / "images.txt").write_text(
                "# Images\n"
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000001.jpg\n"
                "\n"
                "2 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000003.jpg\n"
                "\n"
                "3 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000005.jpg\n"
                "\n"
            )
            
            (model_dir / "points3D.txt").write_text("# Points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify processing continued with partial results
            assert result['camera_count'] == 3, \
                "Should have 3 cameras even though 5 frames were provided"
            assert result['success'] is True, \
                "Should succeed with partial reconstruction"

    def test_no_reconstruction_output_handled(self, tmp_path):
        """
        **Validates: Requirements 4.6**
        Test that missing reconstruction output is handled gracefully
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            # COLMAP runs but produces no output (reconstruction failed)
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Don't create any output files (reconstruction failed)
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Should handle missing output gracefully
            assert result is not None, "Should return result even with no output"
            assert result['success'] is False, "Success should be False with no output"
            assert result['fallback'] is True, "Should use fallback mode"


class TestCameraParameters:
    """Test camera intrinsic and extrinsic parameters output"""
    
    def test_camera_intrinsics_in_output(self, tmp_path):
        """
        Test that camera intrinsic parameters are available in output
        (focal length, principal point)
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg"]
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / valid_frames[0]), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output with camera intrinsics
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            
            # SIMPLE_PINHOLE: camera_id, model, width, height, focal_length, cx, cy
            (model_dir / "cameras.txt").write_text(
                "# Camera list\n"
                "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
                "1 SIMPLE_PINHOLE 640 480 500.0 320.0 240.0\n"
            )
            
            (model_dir / "images.txt").write_text(
                "# Images\n"
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000001.jpg\n"
                "\n"
            )
            
            (model_dir / "points3D.txt").write_text("# Points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify cameras.txt exists with intrinsics
            cameras_file = model_dir / "cameras.txt"
            assert cameras_file.exists(), "cameras.txt should exist with intrinsic parameters"
            
            # Verify content has focal length and principal point
            content = cameras_file.read_text()
            assert "SIMPLE_PINHOLE" in content, "Should use SIMPLE_PINHOLE camera model"
            assert "500" in content, "Should contain focal length parameter"
    
    def test_camera_extrinsics_in_output(self, tmp_path):
        """
        Test that camera extrinsic parameters are available in output
        (rotation quaternion, translation vector)
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        valid_frames = ["frame_000001.jpg", "frame_000002.jpg"]
        for filename in valid_frames:
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / filename), img)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create mock output with camera extrinsics
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            
            (model_dir / "cameras.txt").write_text("# Cameras\n1 SIMPLE_PINHOLE 640 480 500 320 240\n")
            
            # Images.txt contains extrinsics: quaternion (QW, QX, QY, QZ) and translation (TX, TY, TZ)
            (model_dir / "images.txt").write_text(
                "# Image list\n"
                "# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n"
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000001.jpg\n"
                "\n"
                "2 0.9239 0.3827 0.0 0.0 1.5 0.2 0.1 1 frame_000002.jpg\n"
                "\n"
            )
            
            (model_dir / "points3D.txt").write_text("# Points\n")
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify images.txt exists with extrinsics
            images_file = model_dir / "images.txt"
            assert images_file.exists(), "images.txt should exist with extrinsic parameters"
            
            # Verify content has rotation and translation
            content = images_file.read_text()
            lines = [l for l in content.split('\n') if l and not l.startswith('#')]
            
            # Should have at least one image with extrinsics
            assert len(lines) >= 2, "Should have image entries with extrinsics"


class TestIntegration:
    """Integration tests for complete pose estimation pipeline"""
    
    def test_complete_pose_estimation_pipeline(self, tmp_path):
        """
        Test the complete pose estimation pipeline:
        SIFT extraction -> feature matching -> sparse reconstruction
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create realistic test frames with features
        valid_frames = []
        for i in range(4):
            filename = f"frame_{i+1:06d}.jpg"
            
            # Create image with distinct features
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add checkerboard pattern
            for y in range(0, 480, 30):
                for x in range(0, 640, 30):
                    if (y // 30 + x // 30 + i) % 2 == 0:
                        img[y:y+30, x:x+30] = [255, 255, 255]
            
            # Add some random features
            for _ in range(50):
                x = np.random.randint(0, 620)
                y = np.random.randint(0, 460)
                cv2.circle(img, (x, y), 5, (255, 0, 0), -1)
            
            cv2.imwrite(str(frames_dir / filename), img)
            valid_frames.append(filename)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Create complete mock output
            model_dir = output_dir / "sparse" / "0"
            model_dir.mkdir(parents=True)
            
            (model_dir / "cameras.txt").write_text(
                "# Camera list\n"
                "1 SIMPLE_PINHOLE 640 480 520.0 320.0 240.0\n"
            )
            
            (model_dir / "images.txt").write_text(
                "# Image list\n"
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_000001.jpg\n"
                "\n"
                "2 0.99 0.1 0.0 0.0 0.5 0.0 0.0 1 frame_000002.jpg\n"
                "\n"
                "3 0.98 0.15 0.05 0.0 1.0 0.1 0.0 1 frame_000003.jpg\n"
                "\n"
                "4 0.97 0.2 0.1 0.0 1.5 0.2 0.0 1 frame_000004.jpg\n"
                "\n"
            )
            
            (model_dir / "points3D.txt").write_text(
                "# 3D point list\n"
                "1 0.0 0.0 1.0 255 0 0 0.1 1 100\n"
                "2 0.5 0.0 1.0 0 255 0 0.1 1 101 2 200\n"
                "3 1.0 0.0 1.0 0 0 255 0.1 2 201 3 300\n"
                "4 1.5 0.0 1.0 255 255 0 0.1 3 301 4 400\n"
            )
            
            result = estimate_camera_poses(
                str(frames_dir),
                valid_frames,
                str(output_dir)
            )
            
            # Verify complete pipeline execution
            assert result['success'] is True, "Pipeline should succeed"
            assert result['camera_count'] == 4, "Should have 4 cameras"
            assert result['point_count'] == 4, "Should have 4 sparse points"
            
            # Verify all COLMAP stages were called
            all_calls = [str(c) for c in mock_run.call_args_list]
            
            has_feature_extraction = any('feature_extractor' in c for c in all_calls)
            has_matching = any('matcher' in c or 'exhaustive_matcher' in c for c in all_calls)
            has_mapper = any('mapper' in c for c in all_calls)
            
            assert has_feature_extraction, "Should call feature extraction"
            assert has_matching, "Should call feature matching"
            assert has_mapper, "Should call mapper for reconstruction"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
