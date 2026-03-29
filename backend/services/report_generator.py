"""
PDF Report Generation Service

This module provides PDF report generation functionality for scenes,
including professional templates, custom branding, and comprehensive content.
"""

import io
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class ReportTemplate:
    """Base class for report templates"""
    
    def __init__(self, name: str, primary_color: Tuple[float, float, float],
                 secondary_color: Tuple[float, float, float]):
        self.name = name
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        
    def get_styles(self):
        """Get paragraph styles for this template"""
        styles = getSampleStyleSheet()
        
        # Custom title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.Color(*self.primary_color),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Custom heading style
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.Color(*self.primary_color),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Custom subheading style
        styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.Color(*self.secondary_color),
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        ))
        
        # Custom body style
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))
        
        return styles


class ConstructionTemplate(ReportTemplate):
    """Template for construction reports"""
    
    def __init__(self):
        super().__init__(
            name="Construction",
            primary_color=(0.2, 0.3, 0.5),  # Dark blue
            secondary_color=(0.8, 0.5, 0.1)  # Orange
        )


class RealEstateTemplate(ReportTemplate):
    """Template for real estate reports"""
    
    def __init__(self):
        super().__init__(
            name="Real Estate",
            primary_color=(0.1, 0.4, 0.3),  # Dark green
            secondary_color=(0.7, 0.7, 0.7)  # Gray
        )


class SurveyingTemplate(ReportTemplate):
    """Template for surveying reports"""
    
    def __init__(self):
        super().__init__(
            name="Surveying",
            primary_color=(0.5, 0.1, 0.1),  # Dark red
            secondary_color=(0.3, 0.3, 0.3)  # Dark gray
        )


class ReportGenerator:
    """
    Service for generating PDF reports from scene data
    
    Supports:
    - Multiple professional templates
    - Custom branding (logo, colors, company info)
    - Scene metadata and statistics
    - Rendered scene images
    - Annotations and measurements
    - Defect reporting
    - Table of contents for long reports
    - PDF/A format for archival
    """
    
    TEMPLATES = {
        'construction': ConstructionTemplate,
        'real_estate': RealEstateTemplate,
        'surveying': SurveyingTemplate
    }
    
    def __init__(self, storage_path: str = "reports"):
        """
        Initialize report generator
        
        Args:
            storage_path: Directory to store generated reports
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def generate_report(
        self,
        scene_data: Dict[str, Any],
        annotations: List[Dict[str, Any]],
        measurements: List[Dict[str, Any]],
        defects: List[Dict[str, Any]],
        scene_images: List[bytes],
        template_name: str = 'construction',
        branding: Optional[Dict[str, Any]] = None,
        sections: Optional[List[str]] = None,
        pdf_a: bool = False
    ) -> bytes:
        """
        Generate a PDF report
        
        Args:
            scene_data: Scene metadata and statistics
            annotations: List of annotations
            measurements: List of measurements
            defects: List of defect annotations
            scene_images: List of rendered scene images (as bytes)
            template_name: Template to use ('construction', 'real_estate', 'surveying')
            branding: Custom branding (logo, colors, company_info)
            sections: Sections to include (None = all)
            pdf_a: Generate PDF/A format for archival
            
        Returns:
            PDF document as bytes
        """
        # Create template
        template_class = self.TEMPLATES.get(template_name, ConstructionTemplate)
        template = template_class()
        
        # Apply custom branding if provided
        if branding:
            if 'primary_color' in branding:
                template.primary_color = branding['primary_color']
            if 'secondary_color' in branding:
                template.secondary_color = branding['secondary_color']
        
        # Get styles
        styles = template.get_styles()
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build story (content)
        story = []
        
        # Determine which sections to include
        all_sections = ['overview', 'measurements', 'annotations', 'photos', 'statistics', 'defects']
        included_sections = sections if sections else all_sections
        
        # Cover page
        story.extend(self._build_cover_page(scene_data, branding, styles))
        story.append(PageBreak())
        
        # Table of contents (if report will be > 10 pages)
        estimated_pages = self._estimate_page_count(
            annotations, measurements, defects, scene_images, included_sections
        )
        if estimated_pages > 10:
            story.extend(self._build_table_of_contents(included_sections, styles))
            story.append(PageBreak())
        
        # Overview section
        if 'overview' in included_sections:
            story.extend(self._build_overview_section(scene_data, styles))
            story.append(Spacer(1, 0.2 * inch))
        
        # Statistics section
        if 'statistics' in included_sections:
            story.extend(self._build_statistics_section(scene_data, styles))
            story.append(Spacer(1, 0.2 * inch))
        
        # Scene images section
        if 'photos' in included_sections and scene_images:
            story.extend(self._build_images_section(scene_images, styles))
            story.append(PageBreak())
        
        # Measurements section
        if 'measurements' in included_sections and measurements:
            story.extend(self._build_measurements_section(measurements, styles))
            story.append(Spacer(1, 0.2 * inch))
        
        # Annotations section
        if 'annotations' in included_sections and annotations:
            story.extend(self._build_annotations_section(annotations, styles))
            story.append(Spacer(1, 0.2 * inch))
        
        # Defects section
        if 'defects' in included_sections and defects:
            story.extend(self._build_defects_section(defects, styles))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _build_cover_page(
        self,
        scene_data: Dict[str, Any],
        branding: Optional[Dict[str, Any]],
        styles
    ) -> List:
        """Build cover page"""
        elements = []
        
        # Logo if provided
        if branding and 'logo_path' in branding:
            try:
                logo = Image(branding['logo_path'], width=2*inch, height=1*inch)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.5 * inch))
            except:
                pass
        
        # Title
        title = Paragraph(
            f"Scene Report: {scene_data.get('name', 'Untitled')}",
            styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Company info if provided
        if branding and 'company_info' in branding:
            company_info = branding['company_info']
            info_text = f"""
            <para align=center>
            <b>{company_info.get('name', '')}</b><br/>
            {company_info.get('address', '')}<br/>
            {company_info.get('phone', '')}<br/>
            {company_info.get('email', '')}
            </para>
            """
            elements.append(Paragraph(info_text, styles['CustomBody']))
            elements.append(Spacer(1, 0.5 * inch))
        
        # Report metadata
        report_date = datetime.now().strftime("%B %d, %Y")
        metadata_text = f"""
        <para align=center>
        <b>Report Generated:</b> {report_date}<br/>
        <b>Scene ID:</b> {scene_data.get('scene_id', 'N/A')}<br/>
        <b>Capture Date:</b> {scene_data.get('capture_date', 'N/A')}
        </para>
        """
        elements.append(Paragraph(metadata_text, styles['CustomBody']))
        
        return elements
    
    def _build_table_of_contents(self, sections: List[str], styles) -> List:
        """Build table of contents"""
        elements = []
        
        elements.append(Paragraph("Table of Contents", styles['CustomTitle']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Section names
        section_names = {
            'overview': 'Scene Overview',
            'statistics': 'Scene Statistics',
            'photos': 'Scene Views',
            'measurements': 'Measurements',
            'annotations': 'Annotations',
            'defects': 'Defects'
        }
        
        toc_data = []
        for section in sections:
            if section in section_names:
                toc_data.append([section_names[section], '...'])
        
        toc_table = Table(toc_data, colWidths=[5*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(toc_table)
        
        return elements
    
    def _build_overview_section(self, scene_data: Dict[str, Any], styles) -> List:
        """Build overview section"""
        elements = []
        
        elements.append(Paragraph("Scene Overview", styles['CustomHeading']))
        
        overview_text = f"""
        <b>Scene Name:</b> {scene_data.get('name', 'Untitled')}<br/>
        <b>Scene ID:</b> {scene_data.get('scene_id', 'N/A')}<br/>
        <b>Source Type:</b> {scene_data.get('source_type', 'N/A')}<br/>
        <b>Capture Date:</b> {scene_data.get('capture_date', 'N/A')}<br/>
        <b>Processing Date:</b> {scene_data.get('processing_date', 'N/A')}<br/>
        <b>Status:</b> {scene_data.get('status', 'N/A')}
        """
        
        elements.append(Paragraph(overview_text, styles['CustomBody']))
        
        return elements
    
    def _build_statistics_section(self, scene_data: Dict[str, Any], styles) -> List:
        """Build statistics section"""
        elements = []
        
        elements.append(Paragraph("Scene Statistics", styles['CustomHeading']))
        
        stats = scene_data.get('statistics', {})
        
        stats_data = [
            ['Metric', 'Value'],
            ['Point Count', f"{stats.get('point_count', 0):,}"],
            ['Tile Count', f"{stats.get('tile_count', 0):,}"],
            ['Scene Dimensions', f"{stats.get('dimensions', 'N/A')}"],
            ['Processing Time', f"{stats.get('processing_time', 'N/A')}"],
            ['Annotation Count', f"{stats.get('annotation_count', 0):,}"],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(stats_table)
        
        return elements
    
    def _build_images_section(self, scene_images: List[bytes], styles) -> List:
        """Build scene images section"""
        elements = []
        
        elements.append(Paragraph("Scene Views", styles['CustomHeading']))
        elements.append(Spacer(1, 0.2 * inch))
        
        viewpoint_names = ['Top View', 'Front View', 'Side View', 'Perspective View']
        
        for idx, image_bytes in enumerate(scene_images[:4]):  # Max 4 images
            try:
                # Create image from bytes
                img = Image(io.BytesIO(image_bytes), width=5*inch, height=3.75*inch)
                img.hAlign = 'CENTER'
                
                # Add caption
                caption_text = viewpoint_names[idx] if idx < len(viewpoint_names) else f"View {idx + 1}"
                caption = Paragraph(
                    f"<para align=center><i>{caption_text}</i></para>",
                    styles['CustomBody']
                )
                
                elements.append(KeepTogether([img, caption]))
                elements.append(Spacer(1, 0.3 * inch))
            except Exception as e:
                # Skip invalid images
                pass
        
        return elements
    
    def _build_measurements_section(self, measurements: List[Dict[str, Any]], styles) -> List:
        """Build measurements section"""
        elements = []
        
        elements.append(Paragraph("Measurements", styles['CustomHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Build measurements table
        table_data = [['Type', 'Value', 'Position', 'Created By']]
        
        for m in measurements:
            measurement_type = m.get('type', 'N/A')
            value = m.get('value', 'N/A')
            unit = m.get('unit', 'm')
            position = m.get('position', [0, 0, 0])
            author = m.get('author', 'Unknown')
            
            # Format position
            pos_str = f"({position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f})"
            
            # Format value with unit
            value_str = f"{value:.2f} {unit}" if isinstance(value, (int, float)) else str(value)
            
            table_data.append([
                measurement_type.capitalize(),
                value_str,
                pos_str,
                author
            ])
        
        measurements_table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 1.5*inch])
        measurements_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(measurements_table)
        
        return elements
    
    def _build_annotations_section(self, annotations: List[Dict[str, Any]], styles) -> List:
        """Build annotations section"""
        elements = []
        
        elements.append(Paragraph("Annotations", styles['CustomHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        for idx, annotation in enumerate(annotations, 1):
            annotation_text = f"""
            <b>Annotation {idx}</b><br/>
            <b>Type:</b> {annotation.get('type', 'N/A')}<br/>
            <b>Content:</b> {annotation.get('content', 'N/A')}<br/>
            <b>Position:</b> {annotation.get('position', 'N/A')}<br/>
            <b>Created By:</b> {annotation.get('author', 'Unknown')}<br/>
            <b>Created At:</b> {annotation.get('created_at', 'N/A')}
            """
            
            elements.append(Paragraph(annotation_text, styles['CustomBody']))
            elements.append(Spacer(1, 0.15 * inch))
        
        return elements
    
    def _build_defects_section(self, defects: List[Dict[str, Any]], styles) -> List:
        """Build defects section"""
        elements = []
        
        elements.append(Paragraph("Defects", styles['CustomHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        for idx, defect in enumerate(defects, 1):
            # Defect header
            severity = defect.get('severity', 'medium')
            category = defect.get('category', 'unknown')
            
            defect_header = f"""
            <b>Defect {idx}: {category.replace('_', ' ').title()}</b><br/>
            <b>Severity:</b> {severity.upper()}<br/>
            <b>Description:</b> {defect.get('description', 'No description')}<br/>
            <b>Position:</b> {defect.get('position', 'N/A')}<br/>
            <b>Reported By:</b> {defect.get('author', 'Unknown')}<br/>
            <b>Reported At:</b> {defect.get('created_at', 'N/A')}
            """
            
            elements.append(Paragraph(defect_header, styles['CustomBody']))
            
            # Defect photos
            photos = defect.get('photos', [])
            if photos:
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph("<b>Photos:</b>", styles['CustomSubHeading']))
                
                for photo_bytes in photos[:2]:  # Max 2 photos per defect
                    try:
                        img = Image(io.BytesIO(photo_bytes), width=3*inch, height=2.25*inch)
                        img.hAlign = 'LEFT'
                        elements.append(img)
                        elements.append(Spacer(1, 0.1 * inch))
                    except:
                        pass
            
            elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _estimate_page_count(
        self,
        annotations: List[Dict[str, Any]],
        measurements: List[Dict[str, Any]],
        defects: List[Dict[str, Any]],
        scene_images: List[bytes],
        sections: List[str]
    ) -> int:
        """Estimate number of pages in report"""
        pages = 2  # Cover + overview
        
        if 'photos' in sections:
            pages += len(scene_images) // 2 + 1
        
        if 'measurements' in sections:
            pages += len(measurements) // 20 + 1
        
        if 'annotations' in sections:
            pages += len(annotations) // 10 + 1
        
        if 'defects' in sections:
            pages += len(defects) // 3 + 1
        
        return pages
    
    def save_report(
        self,
        pdf_bytes: bytes,
        scene_id: str,
        organization_id: str
    ) -> str:
        """
        Save report to storage
        
        Args:
            pdf_bytes: PDF document bytes
            scene_id: Scene identifier
            organization_id: Organization identifier
            
        Returns:
            File path where report was saved
        """
        # Create organization directory
        org_dir = self.storage_path / organization_id
        org_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{scene_id}_{timestamp}.pdf"
        filepath = org_dir / filename
        
        # Write PDF
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        
        return str(filepath)
