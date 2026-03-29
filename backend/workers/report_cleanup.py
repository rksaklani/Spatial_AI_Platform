"""
Report Cleanup Worker

Celery task for cleaning up expired reports (older than 30 days).
"""

import os
from datetime import datetime
from pathlib import Path

from celery import Task
from backend.workers.celery_app import celery_app
from backend.utils.database import get_database_sync


@celery_app.task(bind=True, name="cleanup_expired_reports")
def cleanup_expired_reports(self: Task):
    """
    Clean up expired reports
    
    - Deletes report files older than 30 days
    - Removes expired report records from database
    
    Requirements: 16.7, 27.10
    """
    db = get_database_sync()
    
    # Find expired reports
    expired_reports = db.reports.find({
        "expires_at": {"$lt": datetime.now()}
    })
    
    deleted_count = 0
    error_count = 0
    
    for report in expired_reports:
        try:
            # Delete file if exists
            if os.path.exists(report['file_path']):
                os.remove(report['file_path'])
            
            # Delete from database
            db.reports.delete_one({"_id": report['_id']})
            
            deleted_count += 1
        except Exception as e:
            error_count += 1
            print(f"Error deleting report {report['_id']}: {e}")
    
    return {
        "deleted_count": deleted_count,
        "error_count": error_count,
        "timestamp": datetime.now().isoformat()
    }


@celery_app.task(bind=True, name="generate_report_async")
def generate_report_async(
    self: Task,
    scene_id: str,
    organization_id: str,
    user_id: str,
    template: str = "construction",
    branding: dict = None,
    sections: list = None,
    pdf_a: bool = False
):
    """
    Generate a report asynchronously
    
    This allows for background report generation for large scenes
    with many annotations, ensuring the API remains responsive.
    
    Requirements: 16.5, 27.10
    """
    from backend.services.report_generator import ReportGenerator
    
    db = get_database_sync()
    
    try:
        # Fetch scene
        scene = db.scenes.find_one({
            "_id": scene_id,
            "organization_id": organization_id
        })
        
        if not scene:
            raise ValueError("Scene not found")
        
        # Fetch annotations
        annotations = list(db.annotations.find({"scene_id": scene_id}))
        
        # Separate measurements, defects, and regular annotations
        measurements = []
        defects = []
        regular_annotations = []
        
        for ann in annotations:
            if ann.get('annotation_type') == 'measurement':
                measurements.append({
                    'type': ann.get('metadata', {}).get('measurement_type', 'distance'),
                    'value': ann.get('metadata', {}).get('value', 0),
                    'unit': ann.get('metadata', {}).get('unit', 'm'),
                    'position': ann.get('position', {}),
                    'author': ann.get('user_id', 'Unknown'),
                    'created_at': ann.get('created_at', datetime.now()).isoformat()
                })
            elif ann.get('annotation_type') == 'defect':
                defects.append({
                    'category': ann.get('metadata', {}).get('category', 'unknown'),
                    'severity': ann.get('metadata', {}).get('severity', 'medium'),
                    'description': ann.get('content', ''),
                    'position': ann.get('position', {}),
                    'author': ann.get('user_id', 'Unknown'),
                    'created_at': ann.get('created_at', datetime.now()).isoformat(),
                    'photos': ann.get('metadata', {}).get('photos', [])
                })
            else:
                regular_annotations.append({
                    'type': ann.get('annotation_type', 'comment'),
                    'content': ann.get('content', ''),
                    'position': ann.get('position', {}),
                    'author': ann.get('user_id', 'Unknown'),
                    'created_at': ann.get('created_at', datetime.now()).isoformat()
                })
        
        # Prepare scene data
        scene_data = {
            'scene_id': scene['_id'],
            'name': scene.get('name', 'Untitled Scene'),
            'source_type': scene.get('source_type', 'unknown'),
            'capture_date': scene.get('created_at', datetime.now()).strftime("%Y-%m-%d"),
            'processing_date': scene.get('updated_at', datetime.now()).strftime("%Y-%m-%d"),
            'status': scene.get('status', 'unknown'),
            'statistics': {
                'point_count': scene.get('metadata', {}).get('gaussian_count', 0),
                'tile_count': scene.get('metadata', {}).get('tile_count', 0),
                'dimensions': scene.get('metadata', {}).get('dimensions', 'N/A'),
                'processing_time': scene.get('metadata', {}).get('processing_time', 'N/A'),
                'annotation_count': len(annotations)
            }
        }
        
        # Generate report
        scene_images = []  # TODO: Implement server-side rendering
        
        generator = ReportGenerator()
        pdf_bytes = generator.generate_report(
            scene_data=scene_data,
            annotations=regular_annotations,
            measurements=measurements,
            defects=defects,
            scene_images=scene_images,
            template_name=template,
            branding=branding,
            sections=sections,
            pdf_a=pdf_a
        )
        
        # Save report
        report_path = generator.save_report(
            pdf_bytes=pdf_bytes,
            scene_id=scene_id,
            organization_id=organization_id
        )
        
        # Store report metadata
        from datetime import timedelta
        report_id = f"{scene_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        expires_at = datetime.now() + timedelta(days=30)
        
        db.reports.insert_one({
            "_id": report_id,
            "scene_id": scene_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "file_path": report_path,
            "template": template,
            "generated_at": datetime.now(),
            "expires_at": expires_at,
            "sections": sections,
            "pdf_a": pdf_a,
            "status": "completed"
        })
        
        return {
            "status": "completed",
            "report_id": report_id,
            "report_path": report_path
        }
        
    except Exception as e:
        # Update status to failed
        db.reports.update_one(
            {"scene_id": scene_id, "status": "generating"},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        raise
