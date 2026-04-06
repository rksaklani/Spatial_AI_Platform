#!/usr/bin/env python3
"""
Clean up failed jobs and re-trigger reconstruction
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from utils.config import settings

async def cleanup_and_retrigger(scene_id: str):
    """Clean up failed jobs and re-trigger"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    try:
        # Delete failed reconstruction and tiling jobs
        result = await db.processing_jobs.delete_many({
            'scene_id': scene_id,
            'job_type': {'$in': ['reconstruction', 'optimization']},
            'status': 'queued',
            'current_step': 'failed'
        })
        
        print(f"Deleted {result.deleted_count} failed job(s)")
        
        # Now trigger new jobs
        print("\nTriggering new reconstruction job...")
        
        from workers.gaussian_splatting import reconstruct_scene
        from datetime import datetime
        import uuid
        
        # Get scene
        scene = await db.scenes.find_one({'_id': scene_id})
        if not scene:
            print(f"❌ Scene {scene_id} not found")
            return
        
        organization_id = scene.get('organization_id', 'default-org')
        
        # Create reconstruction job
        reconstruction_job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        job_doc = {
            "_id": reconstruction_job_id,
            "scene_id": scene_id,
            "organization_id": organization_id,
            "job_type": "reconstruction",
            "priority": "normal",
            "parameters": {},
            "celery_task_id": None,
            "worker_id": None,
            "queue": "gpu",
            "status": "pending",
            "error_message": None,
            "retry_count": 0,
            "max_retries": 2,
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
        result = reconstruct_scene.delay(scene_id, reconstruction_job_id)
        
        await db.processing_jobs.update_one(
            {"_id": reconstruction_job_id},
            {
                "$set": {
                    "celery_task_id": result.id,
                    "status": "queued",
                    "queued_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        print(f"✅ Reconstruction job created: {reconstruction_job_id}")
        print(f"   Celery task ID: {result.id}")
        print(f"\nThe job will automatically chain to tiling when complete.")
        print(f"Check progress with: python3 check_jobs.py {scene_id}")
        
    finally:
        client.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 cleanup_failed_jobs.py <scene_id>")
        sys.exit(1)
    
    scene_id = sys.argv[1]
    asyncio.run(cleanup_and_retrigger(scene_id))
