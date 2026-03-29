"""
Reports API endpoints

Provides endpoints for generating and downloading PDF reports.
"""

import io
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.report_generator import ReportGenerator
from utils.database import get_database
from models.scene import SceneInDB
from models.annotation import AnnotationInDB
from api.deps import get_current_user
from models.user import UserInDB


router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class BrandingConfig(BaseModel):
    """Branding configuration for reports"""
    logo_path: Optional[str] = None
    primary_color: Optional[tuple] = Field(None, description="RGB tuple (0-1 range)")
    secondary_color: Optional[tuple] = Field(None, description="RGB tuple (0-1 range)")
    company_info: Optional[Dict[str, str]] = Field(
        None,
        description="Company information (name, address, phone, email)"
    )


class ReportRequest(BaseModel):
    """Request model for report generation"""
    scene_id: str
    template: str = Field("construction", description="Template name: construction, real_estate, surveying")
    branding: Optional[BrandingConfig] = None
    sections: Optional[List[str]] = Field(
        None,
        description="Sections to include: overview, measurements, annotations, photos, statistics, defects"
    )
    pdf_a: bool = Field(False, description="Generate PDF/A format for archival")
    include_defects: bool = Field(True, description="Include defects section")


class ReportResponse(BaseModel):
    """Response model for report generation"""
    report_id: str
    scene_id: str
    generated_at: str
    download_url: str
    expires_at: str


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a PDF report for a scene
    
    - Includes scene metadata and statistics
    - Renders scene images from multiple viewpoints
    - Includes all annotations with details
    - Includes measurements with values and positions
    - Supports custom branding and templates
    - Supports section selection
    - Supports PDF/A format for archival
    
    Requirements: 16.1, 16.2, 16.3, 16.4, 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7, 27.9
    """
    db = await get_db()
    
    # Fetch scene
    scene = await db.scenes.find_one({
        "_id": request.scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Fetch annotations
    annotations_cursor = db.annotations.find({
        "scene_id": request.scene_id
    })
    annotations = await annotations_cursor.to_list(length=None)
    
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
    
    # TODO: Render scene images from multiple viewpoints
    # For now, use empty list - this would be implemented with server-side rendering
    scene_images = []
    
    # Convert branding to dict if provided
    branding_dict = None
    if request.branding:
        branding_dict = request.branding.dict(exclude_none=True)
    
    # Generate report
    generator = ReportGenerator()
    
    try:
        pdf_bytes = generator.generate_report(
            scene_data=scene_data,
            annotations=regular_annotations,
            measurements=measurements,
            defects=defects if request.include_defects else [],
            scene_images=scene_images,
            template_name=request.template,
            branding=branding_dict,
            sections=request.sections,
            pdf_a=request.pdf_a
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    # Save report
    report_path = generator.save_report(
        pdf_bytes=pdf_bytes,
        scene_id=request.scene_id,
        organization_id=current_user.organization_id
    )
    
    # Generate report ID and expiration
    report_id = f"{request.scene_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    expires_at = datetime.now() + timedelta(days=30)
    
    # Store report metadata in database
    await db.reports.insert_one({
        "_id": report_id,
        "scene_id": request.scene_id,
        "organization_id": current_user.organization_id,
        "user_id": current_user.id,
        "file_path": report_path,
        "template": request.template,
        "generated_at": datetime.now(),
        "expires_at": expires_at,
        "sections": request.sections,
        "pdf_a": request.pdf_a
    })
    
    return ReportResponse(
        report_id=report_id,
        scene_id=request.scene_id,
        generated_at=datetime.now().isoformat(),
        download_url=f"/api/v1/reports/{report_id}/download",
        expires_at=expires_at.isoformat()
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Download a generated report
    
    Requirements: 16.6
    """
    db = await get_db()
    
    # Fetch report metadata
    report = await db.reports.find_one({
        "_id": report_id,
        "organization_id": current_user.organization_id
    })
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check expiration
    if report['expires_at'] < datetime.now():
        raise HTTPException(status_code=410, detail="Report has expired")
    
    # Read report file
    try:
        with open(report['file_path'], 'rb') as f:
            pdf_bytes = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{report['scene_id']}.pdf"
        }
    )


@router.get("/scene/{scene_id}")
async def list_scene_reports(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    List all reports for a scene
    
    Requirements: 16.7
    """
    db = await get_db()
    
    # Verify scene access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Fetch reports
    reports_cursor = db.reports.find({
        "scene_id": scene_id,
        "organization_id": current_user.organization_id
    }).sort("generated_at", -1)
    
    reports = await reports_cursor.to_list(length=None)
    
    # Filter out expired reports
    active_reports = []
    for report in reports:
        if report['expires_at'] > datetime.now():
            active_reports.append({
                "report_id": report['_id'],
                "scene_id": report['scene_id'],
                "template": report['template'],
                "generated_at": report['generated_at'].isoformat(),
                "expires_at": report['expires_at'].isoformat(),
                "download_url": f"/api/v1/reports/{report['_id']}/download"
            })
    
    return {"reports": active_reports}


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Delete a report
    
    Requirements: 16.7
    """
    db = await get_db()
    
    # Fetch report
    report = await db.reports.find_one({
        "_id": report_id,
        "organization_id": current_user.organization_id
    })
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Delete file
    try:
        import os
        os.remove(report['file_path'])
    except FileNotFoundError:
        pass
    
    # Delete from database
    await db.reports.delete_one({"_id": report_id})
    
    return {"message": "Report deleted successfully"}
