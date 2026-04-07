"""
Pipeline Configuration Models

Defines all configurable parameters for the video-to-3D pipeline.
Users can customize these before uploading to optimize for their use case.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class FrameExtractionConfig(BaseModel):
    """Frame extraction parameters."""
    
    frame_rate: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Frames per second to extract (1-10). Higher = more detail but slower. Recommended: 2-5"
    )
    
    max_frames: Optional[int] = Field(
        default=500,
        ge=100,
        le=1000,
        description="Maximum number of frames to extract. Recommended: 300-500"
    )
    
    resize_width: int = Field(
        default=1280,
        ge=640,
        le=1920,
        description="Resize frame width (maintains aspect ratio). Recommended: 1280"
    )
    
    quality: int = Field(
        default=2,
        ge=1,
        le=5,
        description="JPEG quality (1=best, 5=worst). Lower = better quality but larger files"
    )


class COLMAPConfig(BaseModel):
    """COLMAP camera pose estimation parameters."""
    
    feature_type: Literal["SIFT", "AKAZE"] = Field(
        default="SIFT",
        description="Feature detector type. SIFT is more accurate, AKAZE is faster"
    )
    
    max_num_features: int = Field(
        default=8000,
        ge=2000,
        le=16000,
        description="Maximum features per image. More = better but slower. Recommended: 8000"
    )
    
    matching_type: Literal["exhaustive", "sequential", "vocab_tree"] = Field(
        default="sequential",
        description=(
            "Feature matching strategy:\n"
            "- exhaustive: Best quality, very slow (< 300 frames)\n"
            "- sequential: Good for video sequences (recommended)\n"
            "- vocab_tree: Fast for large datasets (> 500 frames)"
        )
    )
    
    camera_model: Literal["SIMPLE_RADIAL", "PINHOLE", "SIMPLE_PINHOLE", "RADIAL"] = Field(
        default="SIMPLE_RADIAL",
        description=(
            "Camera model:\n"
            "- SIMPLE_RADIAL: Mobile/action cameras (recommended)\n"
            "- PINHOLE: DSLR/professional cameras\n"
            "- RADIAL: High distortion lenses"
        )
    )
    
    min_model_size: int = Field(
        default=10,
        ge=3,
        le=50,
        description="Minimum number of registered images for valid reconstruction"
    )


class DepthEstimationConfig(BaseModel):
    """Depth estimation parameters (optional, improves quality in sparse areas)."""
    
    enabled: bool = Field(
        default=False,
        description="Enable depth estimation (optional, adds processing time)"
    )
    
    model: Literal["midas", "dpt"] = Field(
        default="midas",
        description="Depth model: midas (faster) or dpt (more accurate)"
    )
    
    resolution: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Depth map resolution. Higher = better but slower"
    )
    
    batch_size: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Batch size for depth estimation. Higher = faster but more VRAM"
    )


class GaussianSplattingConfig(BaseModel):
    """Gaussian Splatting training parameters - MOST IMPORTANT."""
    
    iterations: int = Field(
        default=30000,
        ge=7000,
        le=50000,
        description=(
            "Training iterations:\n"
            "- 7000: Quick preview (5-10 min)\n"
            "- 30000: Good quality (20-40 min) [RECOMMENDED]\n"
            "- 50000: Best quality (40-80 min)"
        )
    )
    
    sh_degree: int = Field(
        default=3,
        ge=0,
        le=4,
        description=(
            "Spherical harmonics degree (lighting complexity):\n"
            "- 0: Flat colors (fastest)\n"
            "- 3: Realistic lighting [RECOMMENDED]\n"
            "- 4: Very detailed lighting (slower)"
        )
    )
    
    densify_from_iter: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Start densification at this iteration"
    )
    
    densify_until_iter: int = Field(
        default=15000,
        ge=3000,
        le=30000,
        description="Stop densification at this iteration (should be ~50% of total iterations)"
    )
    
    densify_grad_threshold: float = Field(
        default=0.0002,
        ge=0.0001,
        le=0.001,
        description=(
            "Gradient threshold for densification:\n"
            "- Lower = more points (denser, slower)\n"
            "- Higher = fewer points (sparser, faster)\n"
            "Recommended: 0.0002"
        )
    )
    
    opacity_reset_interval: int = Field(
        default=3000,
        ge=1000,
        le=5000,
        description="Reset opacity every N iterations to remove floaters"
    )
    
    position_lr_init: float = Field(
        default=0.00016,
        ge=0.00001,
        le=0.001,
        description="Initial learning rate for Gaussian positions"
    )
    
    position_lr_final: float = Field(
        default=0.0000016,
        ge=0.000001,
        le=0.0001,
        description="Final learning rate for Gaussian positions"
    )
    
    background: Literal["white", "black", "random"] = Field(
        default="white",
        description="Background color for training"
    )
    
    @field_validator("densify_until_iter")
    @classmethod
    def validate_densify_until(cls, v, info):
        """Ensure densify_until_iter is reasonable relative to total iterations."""
        if "iterations" in info.data:
            iterations = info.data["iterations"]
            if v > iterations * 0.7:
                raise ValueError(
                    f"densify_until_iter ({v}) should be <= 70% of iterations ({iterations}). "
                    f"Recommended: {int(iterations * 0.5)}"
                )
        return v


class TileGenerationConfig(BaseModel):
    """Tile generation parameters for streaming."""
    
    tile_size: int = Field(
        default=256,
        ge=128,
        le=512,
        description="Tile size in Gaussians. Smaller = more tiles, better streaming"
    )
    
    lod_levels: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of LOD (Level of Detail) levels. More = better streaming but more storage"
    )
    
    compression: Literal["none", "low", "medium", "high"] = Field(
        default="medium",
        description="Tile compression level. Higher = smaller files but slower loading"
    )
    
    max_gaussians_per_tile: int = Field(
        default=100000,
        ge=50000,
        le=500000,
        description="Maximum Gaussians per tile before splitting"
    )


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""
    
    frames: FrameExtractionConfig = Field(default_factory=FrameExtractionConfig)
    colmap: COLMAPConfig = Field(default_factory=COLMAPConfig)
    depth: DepthEstimationConfig = Field(default_factory=DepthEstimationConfig)
    training: GaussianSplattingConfig = Field(default_factory=GaussianSplattingConfig)
    tiles: TileGenerationConfig = Field(default_factory=TileGenerationConfig)
    
    # Global settings
    use_gpu: bool = Field(
        default=True,
        description="Use GPU acceleration (requires CUDA). Disable for CPU-only processing"
    )
    
    priority: Literal["low", "normal", "high"] = Field(
        default="normal",
        description="Processing priority in queue"
    )
    
    @classmethod
    def get_preset(cls, preset: Literal["fast", "balanced", "quality"]) -> "PipelineConfig":
        """Get a preset configuration."""
        
        if preset == "fast":
            # Fast preview: 5-15 minutes
            return cls(
                frames=FrameExtractionConfig(
                    frame_rate=2,
                    max_frames=300,
                    resize_width=1280,
                ),
                colmap=COLMAPConfig(
                    max_num_features=6000,
                    matching_type="sequential",
                ),
                depth=DepthEstimationConfig(enabled=False),
                training=GaussianSplattingConfig(
                    iterations=7000,
                    densify_until_iter=3500,
                ),
                tiles=TileGenerationConfig(
                    lod_levels=2,
                ),
            )
        
        elif preset == "balanced":
            # Balanced: 20-40 minutes (RECOMMENDED)
            return cls(
                frames=FrameExtractionConfig(
                    frame_rate=3,
                    max_frames=400,
                    resize_width=1280,
                ),
                colmap=COLMAPConfig(
                    max_num_features=8000,
                    matching_type="sequential",
                ),
                depth=DepthEstimationConfig(enabled=False),
                training=GaussianSplattingConfig(
                    iterations=30000,
                    densify_until_iter=15000,
                ),
                tiles=TileGenerationConfig(
                    lod_levels=3,
                ),
            )
        
        else:  # quality
            # High quality: 40-80 minutes
            return cls(
                frames=FrameExtractionConfig(
                    frame_rate=5,
                    max_frames=600,
                    resize_width=1920,
                ),
                colmap=COLMAPConfig(
                    max_num_features=12000,
                    matching_type="exhaustive",
                ),
                depth=DepthEstimationConfig(
                    enabled=True,
                    resolution="high",
                ),
                training=GaussianSplattingConfig(
                    iterations=50000,
                    densify_until_iter=25000,
                    sh_degree=4,
                ),
                tiles=TileGenerationConfig(
                    lod_levels=4,
                    compression="low",
                ),
            )
    
    def validate_for_hardware(self, has_gpu: bool, vram_gb: Optional[float] = None) -> list[str]:
        """
        Validate configuration against available hardware.
        
        Returns:
            List of warning messages (empty if all OK)
        """
        warnings = []
        
        if not has_gpu and self.use_gpu:
            warnings.append("GPU requested but not available. Will use CPU (much slower)")
        
        if has_gpu and vram_gb:
            # Estimate VRAM usage
            estimated_vram = (
                self.frames.resize_width * 0.001 +  # Frame size
                self.training.iterations * 0.00001 +  # Training
                self.colmap.max_num_features * 0.0001  # Features
            )
            
            if estimated_vram > vram_gb * 0.9:
                warnings.append(
                    f"Configuration may exceed available VRAM ({vram_gb}GB). "
                    f"Consider reducing frame size or feature count"
                )
        
        # Check for common mistakes
        if self.frames.frame_rate > 5 and self.frames.max_frames > 500:
            warnings.append(
                "High frame rate + high frame count = very slow processing. "
                "Consider reducing one of these"
            )
        
        if self.colmap.matching_type == "exhaustive" and self.frames.max_frames > 300:
            warnings.append(
                "Exhaustive matching with >300 frames will be VERY slow. "
                "Consider using 'sequential' matching"
            )
        
        if self.training.iterations < 10000:
            warnings.append(
                "Low iteration count may produce poor quality results. "
                "Recommended minimum: 10000"
            )
        
        return warnings


# Preset configurations for quick access
PRESET_FAST = PipelineConfig.get_preset("fast")
PRESET_BALANCED = PipelineConfig.get_preset("balanced")
PRESET_QUALITY = PipelineConfig.get_preset("quality")
