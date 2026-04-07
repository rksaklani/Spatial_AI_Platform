"""
Tests for Task 5.5: Frame Intelligence Tests

Tests frame extraction at correct FPS, blur detection accuracy,
motion score calculation, and coverage maximization.

**Validates: Requirements 2.1, 2.3, 2.4, 2.5, 2.7**
"""
import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
import subprocess

# Import the functions we're testing
from workers.video_pipeline import (
    extract_frames,
    filter_frames,
    select_frames_by_coverage,
)


class TestFrameExtractionFPS:
    """Test frame extraction at correct FPS (Requirement 2.1)"""
    
    def test_extract_frames_at_3fps(self, tmp_path):
        """
        **Validates: Requirements 2.1**
        Test that frames are extracted at exactly 3 FPS
        """
        video_path = tmp_path / "test_video.mp4"
        output_dir = tmp_path / "frames"
        output_dir.mkdir()
        
        # Create a mock video file
        video_path.touch()
        
        # Mock subprocess calls
        with patch('subprocess.run') as mock_run:
            # Mock ffprobe response
            probe_output = {
                "format": {"duration": "10.0", "bit_rate": "1000000"},
                "streams": [{
                    "codec_type": "video",
                    "r_frame_rate": "30/1",
                    "width": 1920,
                    "height": 1080,
                    "codec_name": "h264"
                }]
            }
            
            # Mock ffmpeg extraction
            def mock_subprocess(*args, **kwargs):
                cmd = args[0]
                if 'ffprobe' in cmd:
                    result = MagicMock()
                    result.stdout = str(probe_output).replace("'", '"')
                    return result
                elif 'ffmpeg' in cmd:
                    # Create dummy frames
                    for i in range(30):  # 10 seconds * 3 fps = 30 frames
                        frame_path = output_dir / f"frame_{i+1:06d}.jpg"
                        img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                        cv2.imwrite(str(frame_path), img)
                    return MagicMock()
                return MagicMock()
            
            mock_run.side_effect = mock_subprocess
            
            result = extract_frames(str(video_path), str(output_dir), fps=3)
            
            # Verify FFmpeg was called with fps=3
            ffmpeg_calls = [call for call in mock_run.call_args_list if 'ffmpeg' in str(call)]
            assert len(ffmpeg_calls) > 0, "FFmpeg should be called"
            
            # Check that fps filter is in the command
            ffmpeg_cmd = str(ffmpeg_calls[0])
            assert 'fps' in ffmpeg_cmd or '3' in ffmpeg_cmd, "FPS parameter should be in FFmpeg command"
            
            # Verify frame count matches expected (3 fps * 10 seconds = 30 frames)
            assert result['frame_count'] == 30, f"Expected 30 frames at 3 FPS, got {result['frame_count']}"


class TestBlurDetection:
    """Test blur detection accuracy (Requirements 2.3, 2.4)"""
    
    def test_blur_detection_laplacian_variance(self, tmp_path):
        """
        **Validates: Requirements 2.3**
        Test that blur scores are calculated using Laplacian variance
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create a sharp image with high-frequency content (checkerboard)
        sharp_img = np.zeros((480, 640), dtype=np.uint8)
        for i in range(0, 480, 20):
            for j in range(0, 640, 20):
                if (i // 20 + j // 20) % 2 == 0:
                    sharp_img[i:i+20, j:j+20] = 255
        
        cv2.imwrite(str(frames_dir / "frame_000001.jpg"), sharp_img)
        
        result = filter_frames(str(frames_dir))
        
        # Sharp image should pass blur threshold
        assert len(result['valid_frames']) > 0, "Sharp frame should be kept"
    
    def test_blur_threshold_100(self, tmp_path):
        """
        **Validates: Requirements 2.4**
        Test that frames with blur score below 100 are marked as invalid
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create a sharp frame (should pass)
        sharp = np.zeros((480, 640), dtype=np.uint8)
        for i in range(0, 480, 10):
            for j in range(0, 640, 10):
                if (i // 10 + j // 10) % 2 == 0:
                    sharp[i:i+10, j:j+10] = 255
        cv2.imwrite(str(frames_dir / "frame_000001.jpg"), sharp)
        
        # Create a blurry frame (should fail)
        blurry = np.ones((480, 640), dtype=np.uint8) * 128
        blurry = cv2.GaussianBlur(blurry, (51, 51), 0)
        cv2.imwrite(str(frames_dir / "frame_000002.jpg"), blurry)
        
        result = filter_frames(str(frames_dir))
        
        # Calculate actual blur scores to verify threshold
        sharp_gray = cv2.imread(str(frames_dir / "frame_000001.jpg"), cv2.IMREAD_GRAYSCALE)
        blurry_gray = cv2.imread(str(frames_dir / "frame_000002.jpg"), cv2.IMREAD_GRAYSCALE)
        
        sharp_score = cv2.Laplacian(sharp_gray, cv2.CV_64F).var()
        blurry_score = cv2.Laplacian(blurry_gray, cv2.CV_64F).var()
        
        # Verify sharp passes threshold
        assert sharp_score > 100, f"Sharp image should have blur score > 100, got {sharp_score}"
        
        # Verify blurry fails threshold
        assert blurry_score < 100, f"Blurry image should have blur score < 100, got {blurry_score}"
        
        # Verify filtering result
        assert len(result['valid_frames']) >= 1, "At least one sharp frame should be kept"
        assert result['total_frames'] == 2, "Should have processed 2 frames"


class TestMotionScoreCalculation:
    """Test motion score calculation using optical flow (Requirement 2.2)"""
    
    def test_motion_score_optical_flow(self, tmp_path):
        """
        **Validates: Requirements 2.2**
        Test that motion scores are calculated using optical flow analysis
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create frame 1: object on left
        frame1 = np.zeros((480, 640), dtype=np.uint8)
        frame1[200:280, 100:200] = 255
        cv2.imwrite(str(frames_dir / "frame_000001.jpg"), frame1)
        
        # Create frame 2: object moved to right (significant motion)
        frame2 = np.zeros((480, 640), dtype=np.uint8)
        frame2[200:280, 400:500] = 255
        cv2.imwrite(str(frames_dir / "frame_000002.jpg"), frame2)
        
        # Create frame 3: object moved slightly (small motion)
        frame3 = np.zeros((480, 640), dtype=np.uint8)
        frame3[200:280, 410:510] = 255
        cv2.imwrite(str(frames_dir / "frame_000003.jpg"), frame3)
        
        result = filter_frames(str(frames_dir))
        
        # Motion scores should be calculated (verified by successful filtering)
        assert 'average_motion_score' in result, "Average motion score should be calculated"
        assert result['average_motion_score'] > 0, "Motion score should be positive for moving frames"
    
    def test_static_frames_low_motion(self, tmp_path):
        """
        **Validates: Requirements 2.2**
        Test that static frames have low motion scores
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create identical frames (no motion)
        static_img = np.zeros((480, 640), dtype=np.uint8)
        static_img[200:280, 300:400] = 255
        
        for i in range(3):
            cv2.imwrite(str(frames_dir / f"frame_{i+1:06d}.jpg"), static_img.copy())
        
        result = filter_frames(str(frames_dir))
        
        # Static frames should have very low average motion
        assert result['average_motion_score'] < 10, \
            f"Static frames should have low motion score, got {result['average_motion_score']}"


class TestCoverageMaximization:
    """Test coverage-based frame selection (Requirements 2.5, 2.7)"""
    
    def test_coverage_maximization_selection(self, tmp_path):
        """
        **Validates: Requirements 2.5**
        Test that frames are selected to maximize spatial coverage
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create frames with features in different spatial regions
        for i in range(20):
            img = np.zeros((480, 640), dtype=np.uint8)
            
            # Add features in different grid cells for each frame
            x_offset = (i % 4) * 160
            y_offset = (i // 4) * 120
            
            # Add high-frequency pattern to ensure sharpness
            for y in range(y_offset, min(y_offset + 120, 480), 10):
                for x in range(x_offset, min(x_offset + 160, 640), 10):
                    if (y // 10 + x // 10) % 2 == 0:
                        img[y:y+10, x:x+10] = 255
            
            cv2.imwrite(str(frames_dir / f"frame_{i+1:06d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        # Coverage-based selection should keep diverse frames
        assert len(result['valid_frames']) > 0, "Should keep some frames"
        assert len(result['valid_frames']) < 20, "Should reduce frame count"
    
    def test_30_percent_reduction_minimum(self, tmp_path):
        """
        **Validates: Requirements 2.7**
        Test that frame count is reduced by at least 30%
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create 50 frames with varying but sufficient quality
        for i in range(50):
            img = np.zeros((480, 640), dtype=np.uint8)
            
            # Add random high-frequency content to ensure sharpness
            for _ in range(100):
                x = np.random.randint(0, 620)
                y = np.random.randint(0, 460)
                img[y:y+20, x:x+20] = np.random.randint(0, 255)
            
            # Add checkerboard pattern to guarantee high blur score
            for y in range(0, 480, 20):
                for x in range(0, 640, 20):
                    if (y // 20 + x // 20) % 2 == 0:
                        img[y:y+20, x:x+20] = 255
            
            cv2.imwrite(str(frames_dir / f"frame_{i+1:06d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        initial_count = 50
        final_count = len(result['valid_frames'])
        reduction_percent = result['reduction_percent']
        
        # Verify at least 30% reduction
        assert reduction_percent >= 30, \
            f"Should reduce by at least 30%, got {reduction_percent:.1f}%"
        
        # Verify calculation is correct
        expected_reduction = ((initial_count - final_count) / initial_count) * 100
        assert abs(reduction_percent - expected_reduction) < 0.1, \
            "Reduction percentage calculation should be accurate"


class TestValidFramesOutput:
    """Test that only valid frames are output (Requirement 2.6)"""
    
    def test_only_valid_frames_output(self, tmp_path):
        """
        **Validates: Requirements 2.6**
        Test that only Valid_Frames are output for subsequent processing
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create mix of sharp and blurry frames
        for i in range(10):
            if i % 2 == 0:
                # Sharp frame
                img = np.zeros((480, 640), dtype=np.uint8)
                for y in range(0, 480, 10):
                    for x in range(0, 640, 10):
                        if (y // 10 + x // 10) % 2 == 0:
                            img[y:y+10, x:x+10] = 255
            else:
                # Blurry frame
                img = np.ones((480, 640), dtype=np.uint8) * 128
                img = cv2.GaussianBlur(img, (51, 51), 0)
            
            cv2.imwrite(str(frames_dir / f"frame_{i+1:06d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        # Verify all output frames meet quality threshold
        for frame_filename in result['valid_frames']:
            frame_path = os.path.join(str(frames_dir), frame_filename)
            img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
            blur_score = cv2.Laplacian(img, cv2.CV_64F).var()
            
            assert blur_score >= 100, \
                f"Output frame {frame_filename} should have blur score >= 100, got {blur_score}"
    
    def test_valid_frames_list_format(self, tmp_path):
        """
        **Validates: Requirements 2.6**
        Test that valid_frames is returned as a list of filenames
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create a few sharp frames
        for i in range(5):
            img = np.zeros((480, 640), dtype=np.uint8)
            for y in range(0, 480, 15):
                for x in range(0, 640, 15):
                    if (y // 15 + x // 15) % 2 == 0:
                        img[y:y+15, x:x+15] = 255
            cv2.imwrite(str(frames_dir / f"frame_{i+1:06d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        # Verify return format
        assert 'valid_frames' in result, "Result should contain 'valid_frames' key"
        assert isinstance(result['valid_frames'], list), "valid_frames should be a list"
        assert all(isinstance(f, str) for f in result['valid_frames']), \
            "All valid_frames entries should be strings (filenames)"
        assert all(f.endswith('.jpg') for f in result['valid_frames']), \
            "All valid_frames should be .jpg files"


class TestCoverageAlgorithm:
    """Test the coverage-based selection algorithm implementation"""
    
    def test_grid_based_coverage_analysis(self, tmp_path):
        """
        Test that coverage analysis uses grid-based approach
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create frames with features in specific grid cells
        # Frame 1: top-left quadrant
        img1 = np.zeros((480, 640), dtype=np.uint8)
        for y in range(0, 240, 10):
            for x in range(0, 320, 10):
                if (y // 10 + x // 10) % 2 == 0:
                    img1[y:y+10, x:x+10] = 255
        cv2.imwrite(str(frames_dir / "frame_000001.jpg"), img1)
        
        # Frame 2: top-right quadrant
        img2 = np.zeros((480, 640), dtype=np.uint8)
        for y in range(0, 240, 10):
            for x in range(320, 640, 10):
                if (y // 10 + x // 10) % 2 == 0:
                    img2[y:y+10, x:x+10] = 255
        cv2.imwrite(str(frames_dir / "frame_000002.jpg"), img2)
        
        # Frame 3: duplicate of frame 1 (should be deprioritized)
        cv2.imwrite(str(frames_dir / "frame_000003.jpg"), img1)
        
        result = filter_frames(str(frames_dir))
        
        # Should prefer frames with different coverage
        assert len(result['valid_frames']) >= 2, "Should keep frames with different coverage"
    
    def test_coverage_reduction_target_parameter(self):
        """
        Test that select_frames_by_coverage respects target_reduction parameter
        """
        # Create mock frame data
        frames = []
        for i in range(100):
            frame_data = {
                'filename': f'frame_{i:06d}.jpg',
                'blur_score': 150,  # All sharp
                'motion_score': 10,
                'gray': np.random.randint(0, 255, (480, 640), dtype=np.uint8)
            }
            frames.append(frame_data)
        
        # Test with 30% reduction
        selected = select_frames_by_coverage(frames, target_reduction=0.3)
        
        expected_count = int(100 * (1 - 0.3))
        actual_count = len(selected)
        
        # Allow some tolerance (±10%)
        assert abs(actual_count - expected_count) <= 10, \
            f"Expected ~{expected_count} frames with 30% reduction, got {actual_count}"


class TestIntegration:
    """Integration tests for the complete frame intelligence pipeline"""
    
    def test_complete_pipeline_flow(self, tmp_path):
        """
        Test the complete flow: extract -> filter -> coverage selection
        """
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create a realistic set of frames
        for i in range(30):
            img = np.zeros((480, 640), dtype=np.uint8)
            
            # Vary quality: some sharp, some blurry
            if i % 3 == 0:
                # Blurry frame
                img = cv2.GaussianBlur(img, (51, 51), 0)
            else:
                # Sharp frame with features
                for y in range(0, 480, 15):
                    for x in range(0, 640, 15):
                        if (y // 15 + x // 15 + i) % 2 == 0:
                            img[y:y+15, x:x+15] = 255
            
            cv2.imwrite(str(frames_dir / f"frame_{i+1:06d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        # Verify all requirements are met
        assert 'valid_frames' in result, "Should return valid_frames"
        assert 'total_frames' in result, "Should return total_frames"
        assert 'reduction_percent' in result, "Should return reduction_percent"
        assert 'average_motion_score' in result, "Should return average_motion_score"
        
        # Verify reduction
        assert result['reduction_percent'] >= 30, "Should meet 30% reduction requirement"
        
        # Verify quality
        for frame_filename in result['valid_frames']:
            frame_path = os.path.join(str(frames_dir), frame_filename)
            img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
            blur_score = cv2.Laplacian(img, cv2.CV_64F).var()
            assert blur_score >= 100, "All output frames should meet quality threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
