"""
Semantic Scene Analysis Worker

Implements object detection and classification using:
- Segment Anything Model (SAM) for segmentation
- CLIP for zero-shot classification
- Scene graph construction for spatial relationships
"""

import os
import time
import tempfile
import shutil
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from celery.utils.log import get_task_logger
from workers.celery_app import celery_app
from workers.base_task import SpatialAIBaseTask

logger = get_task_logger(__name__)

# Category labels for CLIP classification
CATEGORY_LABELS = [
    "wall", "floor", "ceiling", "door", "window", "stairs",
    "chair", "table", "sofa", "bed", "desk", "cabinet", "shelf",
    "lamp", "plant", "artwork", "appliance", "electronics",
    "person", "animal", "vehicle", "tree", "building", "road",
    "object"
]


def update_job_progress(job_id: str, progress: float, step: str, message: str = None):
    """Update job progress in MongoDB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from utils.config import settings
    import asyncio
    
    async def _update():
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        await db.processing_jobs.update_one(
            {"_id": job_id},
            {"$set": {
                "progress_percent": progress,
                "current_step": step,
                "status_message": message or step,
                "updated_at": datetime.utcnow(),
            }}
        )
        client.close()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_update())
    finally:
        loop.close()


class SegmentAnythingWrapper:
    """Wrapper for Segment Anything Model (SAM)."""
    
    def __init__(self, model_type: str = "vit_b"):
        """
        Initialize SAM model.
        
        Args:
            model_type: Model variant (vit_b, vit_l, vit_h)
        """
        self.model = None
        self.predictor = None
        self.mask_generator = None  # Initialize to None for fallback mode
        self.model_type = model_type
        self.device = "cpu"
        
        try:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Try to load SAM
            try:
                from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator
                
                # Model checkpoints (would need to be downloaded)
                checkpoint_map = {
                    "vit_b": "sam_vit_b_01ec64.pth",
                    "vit_l": "sam_vit_l_0b3195.pth",
                    "vit_h": "sam_vit_h_4b8939.pth",
                }
                
                checkpoint = checkpoint_map.get(model_type)
                if checkpoint and os.path.exists(checkpoint):
                    self.model = sam_model_registry[model_type](checkpoint=checkpoint)
                    self.model.to(self.device)
                    self.predictor = SamPredictor(self.model)
                    self.mask_generator = SamAutomaticMaskGenerator(self.model)
                    logger.info(f"Loaded SAM {model_type} on {self.device}")
                else:
                    logger.warning(f"SAM checkpoint not found, using fallback segmentation")
            except ImportError:
                logger.warning("segment_anything not installed, using fallback")
                
        except ImportError:
            logger.warning("PyTorch not available")
    
    def generate_masks(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Generate all masks for an image using automatic mask generation.
        
        Args:
            image: RGB image array (H, W, 3)
            
        Returns:
            List of mask dictionaries with 'segmentation', 'bbox', 'area', etc.
        """
        if self.mask_generator is not None:
            return self.mask_generator.generate(image)
        
        # Fallback: simple grid-based segmentation
        return self._fallback_segment(image)
    
    def _fallback_segment(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Fallback segmentation using superpixels or grid."""
        try:
            from skimage.segmentation import slic
            from skimage.measure import regionprops
            
            # SLIC superpixel segmentation
            segments = slic(image, n_segments=50, compactness=10)
            
            masks = []
            for region_id in np.unique(segments):
                if region_id == 0:  # Skip background
                    continue
                    
                mask = segments == region_id
                coords = np.where(mask)
                
                if len(coords[0]) < 100:  # Skip tiny regions
                    continue
                
                y_min, y_max = coords[0].min(), coords[0].max()
                x_min, x_max = coords[1].min(), coords[1].max()
                
                masks.append({
                    "segmentation": mask,
                    "bbox": [x_min, y_min, x_max - x_min, y_max - y_min],
                    "area": np.sum(mask),
                    "predicted_iou": 0.8,
                    "stability_score": 0.8,
                })
            
            return masks
            
        except ImportError:
            # Even simpler fallback: grid
            h, w = image.shape[:2]
            grid_size = 4
            masks = []
            
            for i in range(grid_size):
                for j in range(grid_size):
                    y_start = i * h // grid_size
                    y_end = (i + 1) * h // grid_size
                    x_start = j * w // grid_size
                    x_end = (j + 1) * w // grid_size
                    
                    mask = np.zeros((h, w), dtype=bool)
                    mask[y_start:y_end, x_start:x_end] = True
                    
                    masks.append({
                        "segmentation": mask,
                        "bbox": [x_start, y_start, x_end - x_start, y_end - y_start],
                        "area": (y_end - y_start) * (x_end - x_start),
                        "predicted_iou": 0.5,
                        "stability_score": 0.5,
                    })
            
            return masks


class CLIPClassifier:
    """CLIP-based zero-shot classifier for objects."""
    
    def __init__(self):
        """Initialize CLIP model."""
        self.model = None
        self.preprocess = None
        self.device = "cpu"
        
        try:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            try:
                import clip
                
                self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
                
                # Pre-compute text embeddings for categories
                text_inputs = torch.cat([
                    clip.tokenize(f"a photo of a {label}") for label in CATEGORY_LABELS
                ]).to(self.device)
                
                with torch.no_grad():
                    self.text_features = self.model.encode_text(text_inputs)
                    self.text_features /= self.text_features.norm(dim=-1, keepdim=True)
                
                logger.info(f"Loaded CLIP on {self.device}")
                
            except ImportError:
                logger.warning("CLIP not installed, using fallback classification")
                
        except ImportError:
            logger.warning("PyTorch not available")
    
    def classify(self, image: np.ndarray, mask: np.ndarray = None) -> Tuple[str, float, List[Dict]]:
        """
        Classify an image or masked region.
        
        Args:
            image: RGB image array
            mask: Optional binary mask for region of interest
            
        Returns:
            Tuple of (category, confidence, alternatives)
        """
        if self.model is not None:
            return self._clip_classify(image, mask)
        else:
            return self._fallback_classify(image, mask)
    
    def _clip_classify(self, image: np.ndarray, mask: np.ndarray = None) -> Tuple[str, float, List[Dict]]:
        """Classify using CLIP."""
        import torch
        from PIL import Image
        
        # Apply mask if provided
        if mask is not None:
            # Crop to mask bounding box
            coords = np.where(mask)
            if len(coords[0]) == 0:
                return "unknown", 0.0, []
                
            y_min, y_max = coords[0].min(), coords[0].max()
            x_min, x_max = coords[1].min(), coords[1].max()
            
            # Add padding
            padding = 10
            y_min = max(0, y_min - padding)
            y_max = min(image.shape[0], y_max + padding)
            x_min = max(0, x_min - padding)
            x_max = min(image.shape[1], x_max + padding)
            
            image = image[y_min:y_max, x_min:x_max]
        
        # Convert to PIL and preprocess
        pil_image = Image.fromarray(image)
        image_input = self.preprocess(pil_image).unsqueeze(0).to(self.device)
        
        # Get image features
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            
            # Compute similarity
            similarity = (100.0 * image_features @ self.text_features.T).softmax(dim=-1)
            
        # Get top predictions
        values, indices = similarity[0].topk(5)
        
        top_category = CATEGORY_LABELS[indices[0].item()]
        top_confidence = values[0].item()
        
        alternatives = [
            {"label": CATEGORY_LABELS[idx.item()], "confidence": val.item()}
            for val, idx in zip(values[1:], indices[1:])
        ]
        
        return top_category, top_confidence, alternatives
    
    def _fallback_classify(self, image: np.ndarray, mask: np.ndarray = None) -> Tuple[str, float, List[Dict]]:
        """Fallback classification based on color/size heuristics."""
        if mask is not None:
            area = np.sum(mask)
            total_area = mask.shape[0] * mask.shape[1]
            area_ratio = area / total_area
        else:
            area_ratio = 1.0
        
        # Simple heuristics
        if area_ratio > 0.3:
            # Large regions are likely walls/floors/ceilings
            mean_color = np.mean(image, axis=(0, 1)) if mask is None else np.mean(image[mask], axis=0)
            
            if mean_color[1] > mean_color[0] and mean_color[1] > mean_color[2]:
                return "plant", 0.3, []
            elif np.std(mean_color) < 20:
                return "wall", 0.4, []
            else:
                return "floor", 0.3, []
        elif area_ratio > 0.05:
            return "furniture", 0.3, []
        else:
            return "object", 0.2, []


def compute_3d_bounding_box(
    masks: List[np.ndarray],
    depth_maps: List[np.ndarray],
    camera_params: List[Dict],
) -> Dict[str, float]:
    """
    Compute 3D bounding box from 2D masks and depth maps.
    
    Args:
        masks: List of 2D binary masks
        depth_maps: Corresponding depth maps
        camera_params: Camera intrinsics/extrinsics
        
    Returns:
        3D bounding box parameters
    """
    # Simplified: average 2D bbox and use median depth
    all_points = []
    
    for mask, depth in zip(masks, depth_maps):
        if mask is None or depth is None:
            continue
            
        coords = np.where(mask)
        if len(coords[0]) == 0:
            continue
        
        # Get depth values in masked region
        depths = depth[mask]
        median_depth = np.median(depths)
        
        # Simple projection (assuming normalized coords)
        y_center = np.mean(coords[0]) / mask.shape[0]
        x_center = np.mean(coords[1]) / mask.shape[1]
        
        # Approximate 3D position
        all_points.append([
            (x_center - 0.5) * median_depth * 2,
            (y_center - 0.5) * median_depth * 2,
            median_depth,
        ])
    
    if not all_points:
        return {
            "center_x": 0, "center_y": 0, "center_z": 0,
            "width": 1, "height": 1, "depth": 1,
        }
    
    points = np.array(all_points)
    
    return {
        "center_x": float(np.mean(points[:, 0])),
        "center_y": float(np.mean(points[:, 1])),
        "center_z": float(np.mean(points[:, 2])),
        "width": float(np.ptp(points[:, 0]) + 0.1),
        "height": float(np.ptp(points[:, 1]) + 0.1),
        "depth": float(np.ptp(points[:, 2]) + 0.1),
    }


def build_scene_graph(objects: List[Dict]) -> Dict[str, Any]:
    """
    Build hierarchical scene graph from detected objects.
    
    Args:
        objects: List of detected object dictionaries
        
    Returns:
        Scene graph structure
    """
    # Sort by size (volume) - larger objects are more likely containers
    sorted_objects = sorted(
        objects,
        key=lambda x: x.get("bounding_box", {}).get("width", 0) * 
                      x.get("bounding_box", {}).get("height", 0) *
                      x.get("bounding_box", {}).get("depth", 0),
        reverse=True
    )
    
    root_objects = []
    relationships = []
    
    # Simple containment/support relationships
    structural_categories = {"wall", "floor", "ceiling", "room"}
    furniture_categories = {"table", "desk", "shelf", "cabinet"}
    
    for i, obj in enumerate(sorted_objects):
        category = obj.get("category", "unknown")
        obj_id = obj.get("id")
        
        if category in structural_categories:
            root_objects.append(obj_id)
        else:
            # Find potential parent (larger object that contains this one)
            parent_found = False
            obj_center = (
                obj["bounding_box"]["center_x"],
                obj["bounding_box"]["center_y"],
                obj["bounding_box"]["center_z"],
            )
            
            for parent in sorted_objects[:i]:
                parent_bbox = parent.get("bounding_box", {})
                parent_center = (
                    parent_bbox.get("center_x", 0),
                    parent_bbox.get("center_y", 0),
                    parent_bbox.get("center_z", 0),
                )
                
                # Check if this object is near/inside parent
                distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(obj_center, parent_center)))
                parent_size = max(
                    parent_bbox.get("width", 1),
                    parent_bbox.get("height", 1),
                    parent_bbox.get("depth", 1),
                )
                
                if distance < parent_size * 0.5:
                    parent_category = parent.get("category", "")
                    
                    if parent_category in furniture_categories:
                        relationships.append({
                            "source": obj_id,
                            "target": parent["id"],
                            "relation": "on_top_of",
                        })
                        obj["parent_object_id"] = parent["id"]
                        parent_found = True
                        break
                    elif parent_category == "floor":
                        relationships.append({
                            "source": obj_id,
                            "target": parent["id"],
                            "relation": "standing_on",
                        })
                        obj["parent_object_id"] = parent["id"]
                        parent_found = True
                        break
            
            if not parent_found:
                root_objects.append(obj_id)
    
    # Count categories
    category_counts = {}
    for obj in objects:
        cat = obj.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    return {
        "root_objects": root_objects,
        "relationships": relationships,
        "category_counts": category_counts,
        "object_count": len(objects),
    }


def save_objects_to_db(scene_id: str, organization_id: str, objects: List[Dict]):
    """Save detected objects to MongoDB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from utils.config import settings
    import asyncio
    
    async def _save():
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Delete existing objects for this scene
        await db.scene_objects.delete_many({"scene_id": scene_id})
        
        if objects:
            # Add required fields
            for obj in objects:
                obj["scene_id"] = scene_id
                obj["organization_id"] = organization_id
                obj["created_at"] = datetime.utcnow()
                obj["updated_at"] = datetime.utcnow()
            
            await db.scene_objects.insert_many(objects)
        
        client.close()
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_save())
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    base=SpatialAIBaseTask,
    name="workers.semantic_analysis.analyze_scene",
    queue="gpu",
    max_retries=2,
    soft_time_limit=3600,
    time_limit=3900,
)
def analyze_scene(self, scene_id: str, job_id: str) -> Dict[str, Any]:
    """
    Perform semantic analysis on a reconstructed scene.
    
    Args:
        scene_id: Scene UUID
        job_id: Processing job UUID
        
    Returns:
        Analysis results
    """
    start_time = time.time()
    work_dir = None
    
    try:
        logger.info(f"Starting semantic analysis for scene {scene_id}")
        
        update_job_progress(job_id, 0, "initializing", "Starting semantic analysis")
        
        # Get scene data
        from motor.motor_asyncio import AsyncIOMotorClient
        from utils.config import settings
        import asyncio
        
        async def get_scene():
            client = AsyncIOMotorClient(settings.mongodb_url)
            db = client[settings.database_name]
            scene = await db.scenes.find_one({"_id": scene_id})
            client.close()
            return scene
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scene = loop.run_until_complete(get_scene())
        loop.close()
        
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        organization_id = scene["organization_id"]
        
        # Create working directory
        work_dir = tempfile.mkdtemp(prefix=f"sem_{scene_id}_")
        
        # Download frames
        update_job_progress(job_id, 10, "downloading", "Downloading frames")
        
        from utils.minio_client import get_minio_client
        minio = get_minio_client()
        
        frames_dir = os.path.join(work_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        frame_files = []
        try:
            objects = minio.client.list_objects("frames", prefix=f"{scene_id}/", recursive=True)
            for obj in objects:
                filename = os.path.basename(obj.object_name)
                local_path = os.path.join(frames_dir, filename)
                minio.download_file("frames", obj.object_name, local_path)
                frame_files.append(local_path)
        except Exception as e:
            logger.warning(f"Failed to download frames: {e}")
        
        frame_files.sort()
        
        if not frame_files:
            logger.warning("No frames found, creating dummy analysis")
            frame_files = []
        
        # Initialize models
        update_job_progress(job_id, 20, "loading_models", "Loading SAM and CLIP")
        
        sam = SegmentAnythingWrapper()
        clip_classifier = CLIPClassifier()
        
        # Process frames
        update_job_progress(job_id, 30, "segmenting", "Segmenting objects")
        
        all_detections = []
        
        # Sample frames (don't process all for efficiency)
        sample_indices = list(range(0, len(frame_files), max(1, len(frame_files) // 10)))
        
        for idx, frame_idx in enumerate(sample_indices):
            if frame_idx >= len(frame_files):
                continue
                
            frame_path = frame_files[frame_idx]
            
            try:
                import cv2
                image = cv2.imread(frame_path)
                if image is None:
                    continue
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            except Exception as e:
                logger.warning(f"Failed to read frame {frame_path}: {e}")
                continue
            
            # Generate masks
            masks = sam.generate_masks(image)
            
            # Classify each mask
            for mask_data in masks:
                mask = mask_data.get("segmentation")
                if mask is None:
                    continue
                
                # Classify
                category, confidence, alternatives = clip_classifier.classify(image, mask)
                
                if confidence < 0.2:
                    continue
                
                all_detections.append({
                    "frame_index": frame_idx,
                    "category": category,
                    "confidence": confidence,
                    "alternatives": alternatives,
                    "bbox": mask_data.get("bbox"),
                    "area": mask_data.get("area"),
                })
            
            progress = 30 + (40 * (idx + 1) / len(sample_indices))
            update_job_progress(job_id, progress, "segmenting", f"Processed {idx + 1}/{len(sample_indices)} frames")
        
        # Cluster detections into objects
        update_job_progress(job_id, 70, "clustering", "Clustering detections into objects")
        
        objects = cluster_detections(all_detections)
        
        # Build scene graph
        update_job_progress(job_id, 85, "building_graph", "Building scene graph")
        
        scene_graph = build_scene_graph(objects)
        
        # Save to database
        update_job_progress(job_id, 95, "saving", "Saving objects to database")
        
        save_objects_to_db(scene_id, organization_id, objects)
        
        # Results
        processing_time = time.time() - start_time
        
        result = {
            "scene_id": scene_id,
            "object_count": len(objects),
            "category_counts": scene_graph.get("category_counts", {}),
            "root_objects": len(scene_graph.get("root_objects", [])),
            "relationships": len(scene_graph.get("relationships", [])),
            "frames_processed": len(sample_indices),
            "processing_time_seconds": processing_time,
        }
        
        update_job_progress(job_id, 100, "completed", f"Detected {len(objects)} objects")
        
        logger.info(f"Semantic analysis complete for {scene_id}: {len(objects)} objects")
        
        return result
        
    except Exception as e:
        logger.error(f"Semantic analysis failed for {scene_id}: {e}")
        update_job_progress(job_id, 0, "failed", str(e))
        raise
        
    finally:
        if work_dir and os.path.exists(work_dir):
            try:
                shutil.rmtree(work_dir)
            except Exception:
                pass


def cluster_detections(detections: List[Dict]) -> List[Dict]:
    """
    Cluster frame-level detections into scene-level objects.
    
    Args:
        detections: List of per-frame detections
        
    Returns:
        List of clustered objects
    """
    if not detections:
        return []
    
    # Group by category
    by_category = {}
    for det in detections:
        cat = det.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(det)
    
    objects = []
    
    for category, cat_detections in by_category.items():
        # Simple clustering: merge nearby detections of same category
        # In production, would use more sophisticated spatial clustering
        
        # For now, create one object per category with aggregated stats
        avg_confidence = np.mean([d["confidence"] for d in cat_detections])
        
        # Estimate 3D bbox from 2D bboxes
        all_bboxes = [d["bbox"] for d in cat_detections if d.get("bbox")]
        if all_bboxes:
            avg_x = np.mean([b[0] + b[2]/2 for b in all_bboxes])
            avg_y = np.mean([b[1] + b[3]/2 for b in all_bboxes])
            avg_w = np.mean([b[2] for b in all_bboxes])
            avg_h = np.mean([b[3] for b in all_bboxes])
        else:
            avg_x, avg_y, avg_w, avg_h = 0.5, 0.5, 0.1, 0.1
        
        # If many detections, might be multiple instances
        num_instances = max(1, len(cat_detections) // 3)
        
        for instance in range(num_instances):
            obj_id = str(uuid.uuid4())
            
            objects.append({
                "_id": obj_id,
                "category": category,
                "label": category.replace("_", " ").title(),
                "confidence": float(avg_confidence),
                "alternative_labels": cat_detections[0].get("alternatives", [])[:3],
                "bounding_box": {
                    "center_x": float(avg_x + instance * 0.1),
                    "center_y": float(avg_y),
                    "center_z": 1.0,
                    "width": float(avg_w),
                    "height": float(avg_h),
                    "depth": 0.5,
                },
                "centroid": (float(avg_x + instance * 0.1), float(avg_y), 1.0),
                "masks": [],
                "parent_object_id": None,
                "child_object_ids": [],
                "relationships": [],
                "properties": {},
                "gaussian_indices": [],
                "gaussian_count": 0,
            })
    
    return objects
