#!/usr/bin/env python3
"""
Manually trigger Gaussian Splatting reconstruction and tiling for a scene
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from utils.config import settings
from datetime import datetime
import uuid

async def trigger_reconstruction(scene_id: str):
    """Trigger Gaussian Splatting reconstruction and tiling"""
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
        print(f"Status: {scene.get('status')}")
        print(f"{'='*80}\n")
        
        organization_id = scene.get('organization_id', 'default-org')
        
        # Check if Gaussian model already exists
        existing_job = await db.processing_jobs.find_one(
            {'scene_id': scene_id, 'job_type': 'reconstruction'},
            sort=[('created_at', -1)]
        )
        
        if existing_job:
            print(f"⚠️  Reconstruction job already exists:")
            print(f"   Status: {existing_job.get('status')}")
            print(f"   Progress: {existing_job.get('progress_percent')}%")
            print(f"   Created: {existing_job.get('created_at')}")
            
            if existing_job.get('status') in ['completed', 'running']:
                print(f"\n   Skipping reconstruction, moving to tiling...")
                reconstruction_job_id = existing_job['_id']
            else:
                print(f"\n   Re-triggering reconstruction...")
                reconstruction_job_id = await create_reconstruction_job(db, scene_id, organization_id)
        else:
            print(f"Creating Gaussian Splatting reconstruction job...")
            reconstruction_job_id = await create_reconstruction_job(db, scene_id, organization_id)
        
        # Check if tiling job exists
        tiling_job = await db.processing_jobs.find_one(
            {'scene_id': scene_id, 'job_type': 'optimization'},
            sort=[('created_at', -1)]
        )
        
        if tiling_job and tiling_job.get('status') == 'completed':
            print(f"\n✅ Tiling already completed!")
            print(f"   Tiles: {tiling_job.get('result', {}).get('total_tiles', 0)}")
        else:
            print(f"\nCreating tiling/optimization job...")
            tiling_job_id = await create_tiling_job(db, scene_id, organization_id)
        
        print(f"\n{'='*80}")
        print(f"✅ Jobs created successfully!")
        print(f"{'='*80}\n")
        print(f"The workers will process these jobs automatically.")
        print(f"Check progress with: python3 check_scene_tiles.py")
        print(f"\nNote: Gaussian Splatting training can take 10-30 minutes.")
        print(f"      Tiling will start automatically after training completes.")
        
    finally:
        client.close()


async def create_reconstruction_job(db, scene_id: str, organization_id: str) -> str:
    """Create a Gaussian Splatting reconstruction job"""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    job_doc = {
        "_id": job_id,
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
    try:
        from workers.gaussian_splatting import reconstruct_scene
        result = reconstruct_scene.delay(scene_id, job_id)
        
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
        
        print(f"   ✅ Reconstruction job queued: {job_id}")
        print(f"   Celery task ID: {result.id}")
        
    except Exception as e:
        print(f"   ⚠️  Failed to queue Celery task: {e}")
        print(f"   Job created but not queued. Check if workers are running.")
    
    return job_id


async def create_tiling_job(db, scene_id: str, organization_id: str) -> str:
    """Create a tiling/optimization job"""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    job_doc = {
        "_id": job_id,
        "scene_id": scene_id,
        "organization_id": organization_id,
        "job_type": "optimization",
        "priority": "normal",
        "parameters": {},
        "celery_task_id": None,
        "worker_id": None,
        "queue": "cpu",
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
    try:
        from workers.scene_optimization import optimize_and_tile
        result = optimize_and_tile.delay(scene_id, job_id)
        
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
        
        print(f"   ✅ Tiling job queued: {job_id}")
        print(f"   Celery task ID: {result.id}")
        
    except Exception as e:
        print(f"   ⚠️  Failed to queue Celery task: {e}")
        print(f"   Job created but not queued. Check if workers are running.")
    
    return job_id


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 trigger_reconstruction.py <scene_id>")
        print("\nExample:")
        print("  python3 trigger_reconstruction.py dca8ded7-2054-4270-bc7c-f1f2862db32c")
        sys.exit(1)
    
    scene_id = sys.argv[1]
    asyncio.run(trigger_reconstruction(scene_id))
