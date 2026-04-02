#!/usr/bin/env python3
"""Test script to verify the complete video-to-3D pipeline"""

import sys
import subprocess

def test_component(name, test_func):
    """Test a component and print result"""
    try:
        test_func()
        print(f"✅ {name}: OK")
        return True
    except Exception as e:
        print(f"❌ {name}: FAILED - {e}")
        return False

def test_colmap():
    """Test COLMAP installation"""
    result = subprocess.run(['colmap', '-h'], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("COLMAP not found")
    if 'COLMAP' not in result.stdout:
        raise Exception("COLMAP output unexpected")

def test_pytorch():
    """Test PyTorch with CUDA"""
    import torch
    if not torch.cuda.is_available():
        raise Exception("CUDA not available")
    if torch.version.cuda != '12.1':
        raise Exception(f"CUDA version mismatch: {torch.version.cuda}")
    # Test GPU access
    torch.cuda.get_device_name(0)

def test_gaussian_splatting():
    """Test Gaussian Splatting CUDA extensions"""
    from diff_gaussian_rasterization import GaussianRasterizationSettings
    from simple_knn._C import distCUDA2

def test_opencv():
    """Test OpenCV"""
    import cv2
    # Test basic functionality
    _ = cv2.__version__

def test_open3d():
    """Test Open3D"""
    import open3d as o3d
    # Test basic functionality
    _ = o3d.__version__

def test_midas():
    """Test MiDaS depth estimation"""
    import torch
    # Just verify torch hub can be accessed
    _ = torch.hub.list('intel-isl/MiDaS', force_reload=False)

def main():
    print("=" * 60)
    print("Video-to-3D Pipeline Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test each component
    results.append(test_component("COLMAP", test_colmap))
    results.append(test_component("PyTorch + CUDA 12.1", test_pytorch))
    results.append(test_component("Gaussian Splatting", test_gaussian_splatting))
    results.append(test_component("OpenCV", test_opencv))
    results.append(test_component("Open3D", test_open3d))
    
    print()
    print("=" * 60)
    
    if all(results):
        print("🎉 ALL COMPONENTS WORKING!")
        print()
        print("Video-to-3D pipeline is fully operational.")
        print("You can now upload videos and convert them to 3D models.")
        print()
        print("Next steps:")
        print("1. Access frontend: http://localhost:5173")
        print("2. Upload a video file")
        print("3. Wait for processing to complete")
        print("4. View your 3D model!")
        return 0
    else:
        print("⚠️  SOME COMPONENTS FAILED")
        print()
        print("Please check the errors above and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
