#!/usr/bin/env python3
"""
Re-process a scene from scratch with the fixed pipeline
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from utils.config import settings
from datetime import datetime
import uuid

async def reprocess_scene(scene_id: str):
    """Re-trigger video pipeline for a scene"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    try:
        # Get scene
        scene = await db.scenes.find_one({'_id': scene_id})
        if not scene:
            print(f"❌ Scene {scene_id} not found")
            return
        
        print(f"\n{'='*80}")
        print(f"Scene: {scene.get('name')}")
        print(f"ID: {scene_id}")
        print(f"Current Status: {scene.get('status')}")
        print(f"{'='*80}\n")
        
        organization_id = scene.get('organization_id', 'default-org')
        
        # Delete all existing jobs for this scene
        result = await db.processing_jobs.delete_many({'scene_id': scene_id})
        print(f"Deleted {result.deleted_count} existing job(s)")
        
        # Delete existing data from MinIO
        print("\nCleaning up old data from MinIO...")
        from utils.minio_client import get_minio_client
        minio = get_minio_client()
        
        # Delete from scenes bucket
        try:
            objects = list(minio.client.list_objects("scenes", prefix=f"{scene_id}/", recursive=True))
            for obj in objects:
                minio.client.remove_object("scenes", obj.object_name)
            print(f"  Deleted {len(objects)} files from scenes bucket")
        except Exception as e:
            print(f"  Warning: {e}")
        
        # Delete from frames bucket
        try:
            objects = list(minio.client.list_objects("frames", prefix=f"{scene_id}/", recursive=True))
            for obj in objects:
                minio.client.remove_object("frames", obj.object_name)
            print(f"  Deleted {len(objects)} files from frames bucket")
        except Exception as e:
            print(f"  Warning: {e}")
        
        # Reset scene status
        await db.scenes.update_one(
            {'_id': scene_id},
            {
                '$set': {
                    'status': 'uploaded',
                    'status_message': 'Re-processing with fixed pipeline',
                    'error_message': None,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        print("\nReset scene status to 'uploaded'")
        
        # Create new video pipeline job
        print("\nCreating new video pipeline job...")
        from workers.video_pipeline import process_video_pipeline
        
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        job_doc = {
            "_id": job_id,
            "scene_id": scene_id,
            "organization_id": organization_id,
            "job_type": "full_pipeline",
            "priority": "normal",
            "parameters": {},
            "celery_task_id": None,
            "worker_id": None,
            "queue": "cpu",
            "status": "pending",
            "error_message": None,
            "retry_count": 0,
            "max_retries": 3,
            "progress_percent": 0.0,
            "current_step": None,
            "steps": [],
            "result": None,
            "output_paths": {},
            "created_at": now,
            "updated_at": now,
            "queued_at": None,
            "started_at": None,
            "completed_at": None,
            "wait_time_seconds": None,
            "run_time_seconds": None,
        }
        
        await db.processing_jobs.insert_one(job_doc)
        
        # Trigger Celery task
        result = process_video_pipeline.delay(scene_id, job_id)
        
        await db.processing_jobs.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "celery_task_id": result.id,
                    "status": "queued",
                    "queued_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        print(f"✅ Video pipeline job created: {job_id}")
        print(f"   Celery task ID: {result.id}")
        print(f"\n{'='*80}")
        print(f"✅ Scene re-processing started!")
        print(f"{'='*80}\n")
        print(f"The complete pipeline will run automatically:")
        print(f"  1. Video processing (frame extraction, COLMAP, depth)")
        print(f"  2. Gaussian Splatting reconstruction (auto-triggered)")
        print(f"  3. Tiling/optimization (auto-triggered)")
        print(f"\nTotal time: ~20-60 minutes")
        print(f"Check progress: python3 check_jobs.py {scene_id}")
        
    finally:
        client.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 reprocess_scene.py <scene_id>")
        print("\nThis will:")
        print("  - Delete all existing jobs for the scene")
        print("  - Clean up old data from MinIO")
        print("  - Re-run the complete pipeline with fixed settings")
        sys.exit(1)
    
    scene_id = sys.argv[1]
    asyncio.run(reprocess_scene(scene_id))
