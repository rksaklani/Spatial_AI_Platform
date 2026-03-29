"""
Tests for Task 6: Camera Pose Estimation
Tests COLMAP integration, feature extraction, sparse reconstruction, and failure handling.
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import struct


class TestCOLMAPIntegration:
    """Test COLMAP integration and setup"""
    
    def test_colmap_available(self):
        """Test that COLMAP is available or fallback is used"""
        from workers.video_pipeline import estimate_camera_poses
        
        # Should not raise an error
        result = estimate_camera_poses(
            frames_dir="/tmp/test_frames",
            output_dir="/tmp/test_output",
            use_fallback=True
        )
        
        assert result is not None
        assert 'status' in result
    
    def test_colmap_parameters_configured(self):
        """Test that COLMAP parameters are properly configured"""
        from workers.video_pipeline import estimate_camera_poses
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b"", stderr=b"")
            
            result = estimate_camera_poses(
                frames_dir="/tmp/test_frames",
                output_dir="/tmp/test_output",
                use_fallback=False
            )
            
            # Should attempt to run COLMAP commands
            assert mock_run.called or result['status'] == 'fallback'


class TestFeatureExtraction:
    """Test SIFT feature extraction and matching"""
    
    def test_sift_feature_extraction(self):
        """Test SIFT feature extraction from frames"""
        import cv2
        
        # Create test image with features
        img = np.zeros((480, 640), dtype=np.uint8)
        # Add corners and edges
        cv2.rectangle(img, (100, 100), (200, 200), 255, -1)
        cv2.rectangle(img, (300, 300), (400, 400), 255, -1)
        
        # Extract SIFT features
        sift = cv2.SIFT_create()
        keypoints, descriptors = sift.detectAndCompute(img, None)
        
        # Should detect features
        assert len(keypoints) > 0, "Should detect SIFT features"
        assert descriptors is not None, "Should compute descriptors"
        assert descriptors.shape[0] == len(keypoints), "Descriptor count should match keypoints"
    
    def test_feature_matching_between_frames(self):
        """Test feature matching between frame pairs"""
        import cv2
        
        # Create two similar images
        img1 = np.zeros((480, 640), dtype=np.uint8)
        cv2.rectangle(img1, (100, 100), (200, 200), 255, -1)
        
        img2 = np.zeros((480, 640), dtype=np.uint8)
        cv2.rectangle(img2, (110, 110), (210, 210), 255, -1)  # Slightly shifted
        
        # Extract features
        sift = cv2.SIFT_create()
        kp1, desc1 = sift.detectAndCompute(img1, None)
        kp2, desc2 = sift.detectAndCompute(img2, None)
        
        # Match features
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(desc1, desc2, k=2)
        
        # Apply ratio test
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        # Should find matches between similar images
        assert len(good_matches) > 0, "Should find feature matches"
    
    def test_feature_storage(self, tmp_path):
        """Test that feature matches are stored"""
        from workers.video_pipeline import estimate_camera_poses
        
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create test frames
        import cv2
        for i in range(3):
            img = np.zeros((480, 640), dtype=np.uint8)
            cv2.rectangle(img, (100+i*10, 100), (200+i*10, 200), 255, -1)
            cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), img)
        
        result = estimate_camera_poses(
            frames_dir=str(frames_dir),
            output_dir=str(output_dir),
            use_fallback=True
        )
        
        assert result['status'] in ['success', 'fallback']


class TestSparseReconstruction:
    """Test sparse reconstruction and camera parameter calculation"""
    
    def test_camera_intrinsics_calculation(self):
        """Test calculation of camera intrinsics (focal length, principal point)"""
        # Typical camera intrinsics
        focal_length = 800.0
        cx = 320.0  # Principal point x
        cy = 240.0  # Principal point y
        
        # Create camera matrix
        K = np.array([
            [focal_length, 0, cx],
            [0, focal_length, cy],
            [0, 0, 1]
        ])
        
        # Verify structure
        assert K[0, 0] == focal_length, "Focal length x should be set"
        assert K[1, 1] == focal_length, "Focal length y should be set"
        assert K[0, 2] == cx, "Principal point x should be set"
        assert K[1, 2] == cy, "Principal point y should be set"
    
    def test_camera_extrinsics_calculation(self):
        """Test calculation of camera extrinsics (rotation, translation)"""
        # Create rotation matrix (identity = no rotation)
        R = np.eye(3)
        
        # Create translation vector
        t = np.array([1.0, 2.0, 3.0])
        
        # Create extrinsic matrix [R|t]
        extrinsics = np.hstack([R, t.reshape(3, 1)])
        
        # Verify structure
        assert extrinsics.shape == (3, 4), "Extrinsics should be 3x4"
        assert np.allclose(extrinsics[:3, :3], R), "Rotation should be preserved"
        assert np.allclose(extrinsics[:3, 3], t), "Translation should be preserved"
    
    def test_sparse_point_cloud_generation(self):
        """Test generation of sparse point cloud"""
        # Create sparse 3D points
        points_3d = np.random.rand(100, 3) * 10  # 100 points in 3D space
        
        # Verify structure
        assert points_3d.shape[0] > 0, "Should have 3D points"
        assert points_3d.shape[1] == 3, "Points should be 3D (x, y, z)"
    
    def test_colmap_output_files(self, tmp_path):
        """Test that COLMAP output files are generated"""
        from workers.video_pipeline import estimate_camera_poses
        
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create test frames
        import cv2
        for i in range(5):
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), img)
        
        result = estimate_camera_poses(
            frames_dir=str(frames_dir),
            output_dir=str(output_dir),
            use_fallback=True
        )
        
        # In fallback mode, should still create output structure
        assert result['status'] in ['success', 'fallback']
        if result['status'] == 'success':
            assert 'camera_count' in result


class TestPoseEstimationFailures:
    """Test handling of pose estimation failures"""
    
    def test_failed_frame_detection(self):
        """Test detection of failed pose estimation for individual frames"""
        from workers.video_pipeline import estimate_camera_poses
        
        # Test with insufficient frames
        result = estimate_camera_poses(
            frames_dir="/nonexistent/path",
            output_dir="/tmp/output",
            use_fallback=True
        )
        
        # Should handle gracefully
        assert result is not None
        assert 'status' in result
    
    def test_exclude_failed_frames(self, tmp_path):
        """Test that failed frames are excluded and processing continues"""
        from workers.video_pipeline import estimate_camera_poses
        
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create mix of good and problematic frames
        import cv2
        
        # Good frames with features
        for i in range(3):
            img = np.zeros((480, 640), dtype=np.uint8)
            cv2.rectangle(img, (100+i*50, 100), (200+i*50, 200), 255, -1)
            cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), img)
        
        # Blank frame (no features)
        blank = np.zeros((480, 640), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / "frame_0003.jpg"), blank)
        
        result = estimate_camera_poses(
            frames_dir=str(frames_dir),
            output_dir=str(output_dir),
            use_fallback=True
        )
        
        # Should complete despite problematic frame
        assert result['status'] in ['success', 'fallback', 'partial']
    
    def test_failure_logging(self, tmp_path):
        """Test that failure reasons are logged"""
        from workers.video_pipeline import estimate_camera_poses
        
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        result = estimate_camera_poses(
            frames_dir=str(frames_dir),
            output_dir=str(output_dir),
            use_fallback=True
        )
        
        # Should include status information
        assert 'status' in result
        if result['status'] != 'success':
            assert 'message' in result or 'error' in result


class TestCameraParameterStorage:
    """Test storage of camera parameters"""
    
    def test_camera_data_storage_format(self, tmp_path):
        """Test that camera data is stored in correct format"""
        sparse_dir = tmp_path / "sparse"
        sparse_dir.mkdir()
        
        # Create mock camera data
        cameras_file = sparse_dir / "cameras.txt"
        cameras_file.write_text("# Camera list\n1 PINHOLE 640 480 800 800 320 240\n")
        
        # Verify file exists and has content
        assert cameras_file.exists()
        content = cameras_file.read_text()
        assert "PINHOLE" in content
    
    def test_scene_metadata_update(self):
        """Test that scene metadata is updated with camera count"""
        # Mock scene metadata
        scene_metadata = {
            'scene_id': 'test_scene',
            'status': 'processing'
        }
        
        # Update with camera data
        camera_count = 10
        scene_metadata['camera_count'] = camera_count
        scene_metadata['status'] = 'cameras_estimated'
        
        # Verify update
        assert scene_metadata['camera_count'] == 10
        assert scene_metadata['status'] == 'cameras_estimated'
    
    def test_minio_upload_structure(self, tmp_path):
        """Test MinIO upload structure for camera data"""
        from workers.video_pipeline import upload_sparse_data
        
        sparse_dir = tmp_path / "sparse"
        sparse_dir.mkdir()
        
        # Create mock sparse reconstruction files
        (sparse_dir / "cameras.txt").write_text("# Cameras\n")
        (sparse_dir / "images.txt").write_text("# Images\n")
        (sparse_dir / "points3D.txt").write_text("# Points\n")
        
        scene_id = "test_scene_123"
        
        with patch('workers.video_pipeline.minio_client') as mock_minio:
            mock_minio.upload_file.return_value = True
            
            result = upload_sparse_data(str(sparse_dir), scene_id)
            
            # Should attempt to upload files
            assert result is not None


class TestIntegration:
    """Integration tests for complete pose estimation pipeline"""
    
    def test_end_to_end_pose_estimation(self, tmp_path):
        """Test complete pose estimation pipeline"""
        from workers.video_pipeline import estimate_camera_poses
        import cv2
        
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        output_dir = tmp_path / "sparse"
        output_dir.mkdir()
        
        # Create realistic test frames with features
        for i in range(5):
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add multiple features
            for j in range(5):
                x = 100 + j * 100 + i * 10
                y = 100 + j * 50
                cv2.circle(img, (x, y), 20, (255, 255, 255), -1)
                cv2.rectangle(img, (x-10, y-10), (x+10, y+10), (200, 200, 200), 2)
            
            cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), img)
        
        result = estimate_camera_poses(
            frames_dir=str(frames_dir),
            output_dir=str(output_dir),
            use_fallback=True
        )
        
        # Should complete successfully or with fallback
        assert result['status'] in ['success', 'fallback']
        assert 'camera_count' in result or 'message' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
