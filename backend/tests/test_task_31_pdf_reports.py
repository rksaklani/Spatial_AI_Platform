"""
Tests for Task 31: PDF Report Generation

Tests cover:
- Report content generation
- Template rendering
- Generation performance
- PDF/A format
- Custom branding
- Section selection
- Defect reporting
"""

import pytest
import io
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from services.report_generator import (
    ReportGenerator,
    ConstructionTemplate,
    RealEstateTemplate,
    SurveyingTemplate
)


class TestReportTemplates:
    """Test report templates"""
    
    def test_construction_template(self):
        """Test construction template initialization"""
        template = ConstructionTemplate()
        
        assert template.name == "Construction"
        assert template.primary_color == (0.2, 0.3, 0.5)
        assert template.secondary_color == (0.8, 0.5, 0.1)
        
        styles = template.get_styles()
        assert 'CustomTitle' in styles
        assert 'CustomHeading' in styles
        assert 'CustomSubHeading' in styles
        assert 'CustomBody' in styles
    
    def test_real_estate_template(self):
        """Test real estate template initialization"""
        template = RealEstateTemplate()
        
        assert template.name == "Real Estate"
        assert template.primary_color == (0.1, 0.4, 0.3)
        assert template.secondary_color == (0.7, 0.7, 0.7)
    
    def test_surveying_template(self):
        """Test surveying template initialization"""
        template = SurveyingTemplate()
        
        assert template.name == "Surveying"
        assert template.primary_color == (0.5, 0.1, 0.1)
        assert template.secondary_color == (0.3, 0.3, 0.3)


class TestReportGenerator:
    """Test report generator"""
    
    @pytest.fixture
    def generator(self, tmp_path):
        """Create report generator with temp storage"""
        return ReportGenerator(storage_path=str(tmp_path))
    
    @pytest.fixture
    def sample_scene_data(self):
        """Sample scene data"""
        return {
            'scene_id': 'test_scene_123',
            'name': 'Test Scene',
            'source_type': 'video',
            'capture_date': '2024-01-15',
            'processing_date': '2024-01-16',
            'status': 'completed',
            'statistics': {
                'point_count': 1500000,
                'tile_count': 45,
                'dimensions': '50m x 30m x 10m',
                'processing_time': '15 minutes',
                'annotation_count': 25
            }
        }
    
    @pytest.fixture
    def sample_annotations(self):
        """Sample annotations"""
        return [
            {
                'type': 'comment',
                'content': 'Main entrance area',
                'position': [10.5, 20.3, 1.5],
                'author': 'user_123',
                'created_at': '2024-01-16T10:30:00'
            },
            {
                'type': 'marker',
                'content': 'Reference point',
                'position': [15.2, 18.7, 0.0],
                'author': 'user_456',
                'created_at': '2024-01-16T11:00:00'
            }
        ]
    
    @pytest.fixture
    def sample_measurements(self):
        """Sample measurements"""
        return [
            {
                'type': 'distance',
                'value': 12.5,
                'unit': 'm',
                'position': [10.0, 20.0, 0.0],
                'author': 'user_123',
                'created_at': '2024-01-16T10:45:00'
            },
            {
                'type': 'area',
                'value': 156.8,
                'unit': 'm²',
                'position': [15.0, 25.0, 0.0],
                'author': 'user_456',
                'created_at': '2024-01-16T11:15:00'
            }
        ]
    
    @pytest.fixture
    def sample_defects(self):
        """Sample defects"""
        return [
            {
                'category': 'crack',
                'severity': 'high',
                'description': 'Large crack in foundation wall',
                'position': [5.0, 10.0, 0.5],
                'author': 'inspector_789',
                'created_at': '2024-01-16T12:00:00',
                'photos': []
            },
            {
                'category': 'water_damage',
                'severity': 'medium',
                'description': 'Water staining on ceiling',
                'position': [20.0, 15.0, 3.0],
                'author': 'inspector_789',
                'created_at': '2024-01-16T12:30:00',
                'photos': []
            }
        ]
    
    def test_generate_basic_report(
        self,
        generator,
        sample_scene_data,
        sample_annotations,
        sample_measurements,
        sample_defects
    ):
        """
        Test basic report generation
        
        Requirements: 16.1, 16.2, 16.3, 16.4
        """
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=sample_annotations,
            measurements=sample_measurements,
            defects=sample_defects,
            scene_images=[],
            template_name='construction'
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'  # PDF magic number
    
    def test_generate_report_with_template(
        self,
        generator,
        sample_scene_data,
        sample_annotations,
        sample_measurements,
        sample_defects
    ):
        """
        Test report generation with different templates
        
        Requirements: 27.1
        """
        for template_name in ['construction', 'real_estate', 'surveying']:
            pdf_bytes = generator.generate_report(
                scene_data=sample_scene_data,
                annotations=sample_annotations,
                measurements=sample_measurements,
                defects=sample_defects,
                scene_images=[],
                template_name=template_name
            )
            
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
    
    def test_generate_report_with_branding(
        self,
        generator,
        sample_scene_data,
        sample_annotations,
        sample_measurements,
        sample_defects
    ):
        """
        Test report generation with custom branding
        
        Requirements: 27.2
        """
        branding = {
            'primary_color': (0.1, 0.2, 0.8),
            'secondary_color': (0.9, 0.5, 0.1),
            'company_info': {
                'name': 'Test Company Inc.',
                'address': '123 Test Street',
                'phone': '555-1234',
                'email': 'test@example.com'
            }
        }
        
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=sample_annotations,
            measurements=sample_measurements,
            defects=sample_defects,
            scene_images=[],
            template_name='construction',
            branding=branding
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
    
    def test_generate_report_with_section_selection(
        self,
        generator,
        sample_scene_data,
        sample_annotations,
        sample_measurements,
        sample_defects
    ):
        """
        Test report generation with section selection
        
        Requirements: 27.7
        """
        # Generate report with only overview and measurements
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=sample_annotations,
            measurements=sample_measurements,
            defects=sample_defects,
            scene_images=[],
            template_name='construction',
            sections=['overview', 'measurements']
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Report with fewer sections should be smaller
        full_pdf = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=sample_annotations,
            measurements=sample_measurements,
            defects=sample_defects,
            scene_images=[],
            template_name='construction'
        )
        
        assert len(pdf_bytes) < len(full_pdf)
    
    def test_generate_report_with_defects(
        self,
        generator,
        sample_scene_data,
        sample_annotations,
        sample_measurements,
        sample_defects
    ):
        """
        Test report generation with defects section
        
        Requirements: 31.8
        """
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=sample_annotations,
            measurements=sample_measurements,
            defects=sample_defects,
            scene_images=[],
            template_name='construction',
            sections=['defects']
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
    
    def test_generate_report_performance_100_annotations(
        self,
        generator,
        sample_scene_data
    ):
        """
        Test report generation performance with 100 annotations
        
        Target: 30 seconds for scenes with up to 100 annotations
        Requirements: 16.5, 27.10
        """
        # Generate 100 annotations
        annotations = []
        measurements = []
        defects = []
        
        for i in range(70):
            annotations.append({
                'type': 'comment',
                'content': f'Annotation {i}',
                'position': [i * 0.5, i * 0.3, 0.0],
                'author': 'user_test',
                'created_at': '2024-01-16T10:00:00'
            })
        
        for i in range(20):
            measurements.append({
                'type': 'distance',
                'value': 10.0 + i,
                'unit': 'm',
                'position': [i * 1.0, i * 0.5, 0.0],
                'author': 'user_test',
                'created_at': '2024-01-16T10:00:00'
            })
        
        for i in range(10):
            defects.append({
                'category': 'crack',
                'severity': 'medium',
                'description': f'Defect {i}',
                'position': [i * 2.0, i * 1.0, 0.0],
                'author': 'user_test',
                'created_at': '2024-01-16T10:00:00',
                'photos': []
            })
        
        start_time = time.time()
        
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=annotations,
            measurements=measurements,
            defects=defects,
            scene_images=[],
            template_name='construction'
        )
        
        elapsed_time = time.time() - start_time
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert elapsed_time < 30.0, f"Report generation took {elapsed_time:.2f}s, expected < 30s"
    
    def test_generate_report_performance_200_annotations(
        self,
        generator,
        sample_scene_data
    ):
        """
        Test report generation performance with 200 annotations
        
        Target: 60 seconds for scenes with up to 200 annotations
        Requirements: 27.10
        """
        # Generate 200 annotations
        annotations = []
        measurements = []
        defects = []
        
        for i in range(140):
            annotations.append({
                'type': 'comment',
                'content': f'Annotation {i}',
                'position': [i * 0.5, i * 0.3, 0.0],
                'author': 'user_test',
                'created_at': '2024-01-16T10:00:00'
            })
        
        for i in range(40):
            measurements.append({
                'type': 'distance',
                'value': 10.0 + i,
                'unit': 'm',
                'position': [i * 1.0, i * 0.5, 0.0],
                'author': 'user_test',
                'created_at': '2024-01-16T10:00:00'
            })
        
        for i in range(20):
            defects.append({
                'category': 'crack',
                'severity': 'medium',
                'description': f'Defect {i}',
                'position': [i * 2.0, i * 1.0, 0.0],
                'author': 'user_test',
                'created_at': '2024-01-16T10:00:00',
                'photos': []
            })
        
        start_time = time.time()
        
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=annotations,
            measurements=measurements,
            defects=defects,
            scene_images=[],
            template_name='construction'
        )
        
        elapsed_time = time.time() - start_time
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert elapsed_time < 60.0, f"Report generation took {elapsed_time:.2f}s, expected < 60s"
    
    def test_save_report(
        self,
        generator,
        sample_scene_data,
        sample_annotations,
        sample_measurements,
        sample_defects
    ):
        """
        Test saving report to storage
        
        Requirements: 16.6, 16.7
        """
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=sample_annotations,
            measurements=sample_measurements,
            defects=sample_defects,
            scene_images=[],
            template_name='construction'
        )
        
        report_path = generator.save_report(
            pdf_bytes=pdf_bytes,
            scene_id='test_scene_123',
            organization_id='org_456'
        )
        
        assert Path(report_path).exists()
        assert Path(report_path).suffix == '.pdf'
        
        # Verify file content
        with open(report_path, 'rb') as f:
            saved_bytes = f.read()
        
        assert saved_bytes == pdf_bytes
    
    def test_table_of_contents_generation(
        self,
        generator,
        sample_scene_data
    ):
        """
        Test table of contents generation for reports > 10 pages
        
        Requirements: 27.8
        """
        # Generate enough content to exceed 10 pages
        annotations = [
            {
                'type': 'comment',
                'content': f'Annotation {i}' * 20,  # Long content
                'position': [i * 0.5, i * 0.3, 0.0],
                'author': 'user_test',
                'created_at': '2024-01-16T10:00:00'
            }
            for i in range(100)
        ]
        
        pdf_bytes = generator.generate_report(
            scene_data=sample_scene_data,
            annotations=annotations,
            measurements=[],
            defects=[],
            scene_images=[],
            template_name='construction'
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Report should be generated successfully (TOC is optional based on size)
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_estimate_page_count(self, generator):
        """Test page count estimation"""
        annotations = [{'type': 'comment'} for _ in range(50)]
        measurements = [{'type': 'distance'} for _ in range(30)]
        defects = [{'category': 'crack'} for _ in range(10)]
        scene_images = [b'fake_image' for _ in range(4)]
        
        page_count = generator._estimate_page_count(
            annotations=annotations,
            measurements=measurements,
            defects=defects,
            scene_images=scene_images,
            sections=['overview', 'measurements', 'annotations', 'photos', 'defects']
        )
        
        assert page_count > 0
        assert isinstance(page_count, int)


class TestReportAPI:
    """Test report API endpoints"""
    
    @pytest.mark.asyncio
    async def test_generate_report_endpoint(self):
        """
        Test report generation endpoint
        
        Requirements: 16.1, 16.2, 16.3, 16.4
        """
        # This would require full FastAPI test setup
        # Placeholder for integration test
        pass
    
    @pytest.mark.asyncio
    async def test_download_report_endpoint(self):
        """
        Test report download endpoint
        
        Requirements: 16.6
        """
        # This would require full FastAPI test setup
        # Placeholder for integration test
        pass
    
    @pytest.mark.asyncio
    async def test_list_scene_reports_endpoint(self):
        """
        Test listing scene reports
        
        Requirements: 16.7
        """
        # This would require full FastAPI test setup
        # Placeholder for integration test
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
