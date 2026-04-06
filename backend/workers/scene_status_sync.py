"""
Scene Status Sync Worker

Automatically syncs scene status based on completed jobs.
Runs periodically to catch any scenes where the status update failed.
"""
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from celery import shared_task
from utils.config import settings
import structlog

logger = structlog.get_logger(__name__)


async def sync_scene_statuses():
    """
    Sync scene statuses based on job completion.
    
    Finds scenes with 'processing' status and checks if their jobs are completed.
    Updates scene status accordingly.
    """
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    try:
        # Find all scenes with processing status
        processing_scenes = await db.scenes.find({
            'status': 'processing'
        }).to_list(None)
        
        synced_count = 0
        failed_count = 0
        
        for scene in processing_scenes:
            scene_id = scene['_id']
            
            # Find the latest job for this scene
            job = await db.processing_jobs.find_one(
                {'scene_id': scene_id},
                sort=[('created_at', -1)]
            )
            
            if not job:
                continue
            
            job_status = job.get('status')
            
            # If job is completed, update scene to completed
            if job_status == 'completed':
                await db.scenes.update_one(
                    {'_id': scene_id},
                    {
                        '$set': {
                            'status': 'completed',
                            'updated_at': datetime.utcnow().isoformat()
                        }
                    }
                )
                logger.info(f"Synced scene {scene_id} to completed status")
                synced_count += 1
            
            # If job failed, update scene to failed
            elif job_status == 'failed':
                error_msg = job.get('error_message', 'Processing failed')
                await db.scenes.update_one(
                    {'_id': scene_id},
                    {
                        '$set': {
                            'status': 'failed',
                            'error_message': error_msg,
                            'updated_at': datetime.utcnow().isoformat()
                        }
                    }
                )
                logger.info(f"Synced scene {scene_id} to failed status")
                failed_count += 1
        
        if synced_count > 0 or failed_count > 0:
            logger.info(f"Scene status sync complete: {synced_count} completed, {failed_count} failed")
        
        return {
            'synced_completed': synced_count,
            'synced_failed': failed_count
        }
        
    except Exception as e:
        logger.error(f"Scene status sync failed: {e}")
        raise
    finally:
        client.close()


@shared_task(name='workers.scene_status_sync.sync_scene_statuses_task')
def sync_scene_statuses_task():
    """
    Celery task to sync scene statuses.
    
    This task should be scheduled to run periodically (e.g., every 5 minutes)
    to catch any scenes where the status update failed during processing.
    """
    try:
        result = asyncio.run(sync_scene_statuses())
        logger.info(f"Scene status sync task completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Scene status sync task failed: {e}")
        raise


async def sync_single_scene(scene_id: str):
    """
    Sync status for a single scene.
    
    Args:
        scene_id: The scene ID to sync
        
    Returns:
        dict: Sync result with status and message
    """
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    try:
        # Get scene
        scene = await db.scenes.find_one({'_id': scene_id})
        if not scene:
            return {'success': False, 'message': 'Scene not found'}
        
        # Get latest job
        job = await db.processing_jobs.find_one(
            {'scene_id': scene_id},
            sort=[('created_at', -1)]
        )
        
        if not job:
            return {'success': False, 'message': 'No job found for scene'}
        
        scene_status = scene.get('status')
        job_status = job.get('status')
        
        # Check if sync is needed
        if scene_status == 'processing' and job_status == 'completed':
            await db.scenes.update_one(
                {'_id': scene_id},
                {
                    '$set': {
                        'status': 'completed',
                        'updated_at': datetime.utcnow().isoformat()
                    }
                }
            )
            return {
                'success': True,
                'message': 'Scene status synced to completed',
                'old_status': scene_status,
                'new_status': 'completed'
            }
        
        elif scene_status == 'processing' and job_status == 'failed':
            error_msg = job.get('error_message', 'Processing failed')
            await db.scenes.update_one(
                {'_id': scene_id},
                {
                    '$set': {
                        'status': 'failed',
                        'error_message': error_msg,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                }
            )
            return {
                'success': True,
                'message': 'Scene status synced to failed',
                'old_status': scene_status,
                'new_status': 'failed'
            }
        
        else:
            return {
                'success': True,
                'message': 'Scene status already in sync',
                'scene_status': scene_status,
                'job_status': job_status
            }
        
    finally:
        client.close()
