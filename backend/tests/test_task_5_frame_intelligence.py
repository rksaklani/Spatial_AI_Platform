"""
Tests for Task 5: Frame Extraction and Intelligence
Tests frame extraction, blur detection, motion analysis, and coverage-based selection.
"""
import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Import the functions we're testing
from workers.video_pipeline import (
    extract_frames,
    filter_frames,
    calculate_blur_score,
    calculate_motion_score,
)


class TestFrameExtraction:
    """Test frame extraction at correct FPS"""
    
    def test_extract_frames_basic(self, tmp_path):
        """Test basic frame extraction"""
        # Create a mock video file path
        video_path = tmp_path / "test_video.mp4"
        output_dir = tmp_path / "frames"
        output_dir.mkdir()
        
        # Mock FFmpeg extraction
        with patch('workers.video_pipeline.ffmpeg') as mock_ffmpeg:
            mock_stream = MagicMock()
            mock_ffmpeg.input.return_value = mock_stream
            mock_stream.filter.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.run.return_value = None
            
            # Create some dummy frame files
            for i in range(10):
                frame_path = output_dir / f"frame_{i:04d}.jpg"
                # Create a simple test image
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.imwrite(str(frame_path), img)
            
            result = extract_frames(str(video_path), str(output_dir), fps=3)
            
            assert result['frame_count'] == 10
            assert result['output_dir'] == str(output_dir)
    
    def test_extract_frames_fps_setting(self, tmp_path):
        """Test that FPS setting is respected"""
        video_path = tmp_path / "test_video.mp4"
        output_dir = tmp_path / "frames"
        output_dir.mkdir()
        
        with patch('workers.video_pipeline.ffmpeg') as mock_ffmpeg:
            mock_stream = MagicMock()
            mock_ffmpeg.input.return_value = mock_stream
            mock_stream.filter.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            
            extract_frames(str(video_path), str(output_dir), fps=5)
            
            # Verify fps filter was called
            mock_stream.filter.assert_called()
            call_args = str(mock_stream.filter.call_args)
            assert 'fps' in call_args or '5' in call_args


class TestBlurDetection:
    """Test blur detection accuracy"""
    
    def test_calculate_blur_score_sharp_image(self):
        """Test blur score for sharp image"""
        # Create a sharp image with high-frequency content
        img = np.zeros((480, 640), dtype=np.uint8)
        # Add checkerboard pattern (high frequency)
        for i in range(0, 480, 20):
            for j in range(0, 640, 20):
                if (i // 20 + j // 20) % 2 == 0:
                    img[i:i+20, j:j+20] = 255
        
        blur_score = calculate_blur_score(img)
        
        # Sharp images should have high blur scores (> 100)
        assert blur_score > 100, f"Sharp image should have blur score > 100, got {blur_score}"
    
    def test_calculate_blur_score_blurry_image(self):
        """Test blur score for blurry image"""
        # Create a blurry image (low frequency)
        img = np.zeros((480, 640), dtype=np.uint8)
        # Add smooth gradient
        for i in range(480):
            img[i, :] = int(255 * i / 480)
        
        # Apply Gaussian blur
        img = cv2.GaussianBlur(img, (51, 51), 0)
        
        blur_score = calculate_blur_score(img)
        
        # Blurry images should have low blur scores (< 100)
        assert blur_score < 100, f"Blurry image should have blur score < 100, got {blur_score}"
    
    def test_blur_detection_threshold(self):
        """Test that blur threshold of 100 is applied correctly"""
        # Create frames with varying blur
        frames = []
        
        # Sharp frame
        sharp = np.zeros((480, 640), dtype=np.uint8)
        for i in range(0, 480, 10):
            for j in range(0, 640, 10):
                if (i // 10 + j // 10) % 2 == 0:
                    sharp[i:i+10, j:j+10] = 255
        frames.append(sharp)
        
        # Blurry frame
        blurry = cv2.GaussianBlur(sharp.copy(), (51, 51), 0)
        frames.append(blurry)
        
        # Calculate scores
        scores = [calculate_blur_score(f) for f in frames]
        
        # Sharp should pass, blurry should fail
        assert scores[0] > 100, "Sharp frame should pass threshold"
        assert scores[1] < 100, "Blurry frame should fail threshold"


class TestMotionAnalysis:
    """Test motion score calculation"""
    
    def test_calculate_motion_score_static(self):
        """Test motion score for static frames"""
        # Two identical frames
        frame1 = np.zeros((480, 640), dtype=np.uint8)
        frame2 = frame1.copy()
        
        motion_score = calculate_motion_score(frame1, frame2)
        
        # Static frames should have low motion score
        assert motion_score < 10, f"Static frames should have low motion, got {motion_score}"
    
    def test_calculate_motion_score_moving(self):
        """Test motion score for frames with motion"""
        # Frame 1: object on left
        frame1 = np.zeros((480, 640), dtype=np.uint8)
        frame1[200:280, 100:200] = 255
        
        # Frame 2: object moved to right
        frame2 = np.zeros((480, 640), dtype=np.uint8)
        frame2[200:280, 400:500] = 255
        
        motion_score = calculate_motion_score(frame1, frame2)
        
        # Moving frames should have high motion score
        assert motion_score > 50, f"Moving frames should have high motion, got {motion_score}"
    
    def test_motion_score_gradual_change(self):
        """Test motion score for gradual changes"""
        # Frame 1
        frame1 = np.zeros((480, 640), dtype=np.uint8)
        frame1[200:280, 100:200] = 255
        
        # Frame 2: slight movement
        frame2 = np.zeros((480, 640), dtype=np.uint8)
        frame2[200:280, 110:210] = 255
        
        motion_score = calculate_motion_score(frame1, frame2)
        
        # Should have moderate motion score
        assert 10 < motion_score < 100, f"Gradual motion should be moderate, got {motion_score}"


class TestCoverageSelection:
    """Test coverage maximization"""
    
    def test_filter_frames_removes_blurry(self, tmp_path):
        """Test that blurry frames are filtered out"""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create sharp frame
        sharp = np.zeros((480, 640), dtype=np.uint8)
        for i in range(0, 480, 10):
            for j in range(0, 640, 10):
                if (i // 10 + j // 10) % 2 == 0:
                    sharp[i:i+10, j:j+10] = 255
        cv2.imwrite(str(frames_dir / "frame_0000.jpg"), sharp)
        
        # Create blurry frame
        blurry = cv2.GaussianBlur(sharp.copy(), (51, 51), 0)
        cv2.imwrite(str(frames_dir / "frame_0001.jpg"), blurry)
        
        result = filter_frames(str(frames_dir))
        
        # Should keep sharp, remove blurry
        assert len(result['valid_frames']) >= 1
        assert result['blur_filtered'] >= 1
    
    def test_coverage_reduction_target(self, tmp_path):
        """Test that frame count is reduced by at least 30%"""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create 100 sharp frames with varying content
        for i in range(100):
            img = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
            # Add high-frequency pattern to ensure sharpness
            for y in range(0, 480, 20):
                for x in range(0, 640, 20):
                    if (y // 20 + x // 20) % 2 == 0:
                        img[y:y+20, x:x+20] = 255
            cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        initial_count = 100
        final_count = len(result['valid_frames'])
        reduction_percent = ((initial_count - final_count) / initial_count) * 100
        
        # Should reduce by at least 30%
        assert reduction_percent >= 30, f"Should reduce by >=30%, got {reduction_percent:.1f}%"
    
    def test_valid_frames_output(self, tmp_path):
        """Test that only valid frames are output"""
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
                img = np.zeros((480, 640), dtype=np.uint8)
                img = cv2.GaussianBlur(img, (51, 51), 0)
            
            cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        # All returned frames should be valid (sharp)
        for frame_path in result['valid_frames']:
            img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
            blur_score = calculate_blur_score(img)
            assert blur_score >= 100, f"Output frame should be sharp, got blur score {blur_score}"


class TestFrameMetadata:
    """Test frame metadata storage"""
    
    def test_blur_scores_stored(self, tmp_path):
        """Test that blur scores are stored in metadata"""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create test frame
        img = np.zeros((480, 640), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / "frame_0000.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        assert 'frame_metadata' in result
        assert len(result['frame_metadata']) > 0
        
        # Check metadata structure
        metadata = result['frame_metadata'][0]
        assert 'blur_score' in metadata
        assert 'motion_score' in metadata
        assert 'frame_path' in metadata
    
    def test_motion_scores_stored(self, tmp_path):
        """Test that motion scores are stored in metadata"""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create two frames
        for i in range(2):
            img = np.zeros((480, 640), dtype=np.uint8)
            img[200:280, 100+i*50:200+i*50] = 255
            cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), img)
        
        result = filter_frames(str(frames_dir))
        
        # Motion scores should be calculated between consecutive frames
        assert 'frame_metadata' in result
        if len(result['frame_metadata']) > 1:
            assert 'motion_score' in result['frame_metadata'][1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
