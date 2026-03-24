/**
 * ReportDialog Component
 * 
 * Select report template and generate PDF reports
 * Requirements: F4
 */

import { useState } from 'react';
import { Button, Modal } from '../common';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  sections: string[];
}

interface ReportDialogProps {
  sceneId: string;
  sceneName: string;
  isOpen: boolean;
  onClose: () => void;
  onGenerate?: (templateId: string, sections: string[]) => Promise<void>;
}

const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: 'standard',
    name: 'Standard Report',
    description: 'Comprehensive report with all scene details',
    sections: ['overview', 'metadata', 'annotations', 'measurements', 'photos'],
  },
  {
    id: 'inspection',
    name: 'Inspection Report',
    description: 'Focused on annotations and findings',
    sections: ['overview', 'annotations', 'photos', 'recommendations'],
  },
  {
    id: 'progress',
    name: 'Progress Report',
    description: 'Track changes over time',
    sections: ['overview', 'comparison', 'timeline', 'photos'],
  },
  {
    id: 'custom',
    name: 'Custom Report',
    description: 'Select specific sections to include',
    sections: [],
  },
];

const AVAILABLE_SECTIONS = [
  { id: 'overview', name: 'Scene Overview' },
  { id: 'metadata', name: 'Scene Metadata' },
  { id: 'annotations', name: 'Annotations' },
  { id: 'measurements', name: 'Measurements' },
  { id: 'photos', name: 'Photos' },
  { id: 'comparison', name: 'Scene Comparison' },
  { id: 'timeline', name: 'Timeline' },
  { id: 'recommendations', name: 'Recommendations' },
];

export function ReportDialog({
  sceneId,
  sceneName,
  isOpen,
  onClose,
  onGenerate,
}: ReportDialogProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('standard');
  const [selectedSections, setSelectedSections] = useState<string[]>(
    REPORT_TEMPLATES[0].sections
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedReportUrl, setGeneratedReportUrl] = useState<string>('');

  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplate(templateId);
    const template = REPORT_TEMPLATES.find((t) => t.id === templateId);
    if (template && template.id !== 'custom') {
      setSelectedSections(template.sections);
    }
  };

  const toggleSection = (sectionId: string) => {
    setSelectedSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((s) => s !== sectionId)
        : [...prev, sectionId]
    );
  };

  const handleGenerate = async () => {
    if (!onGenerate) return;

    setIsGenerating(true);
    try {
      await onGenerate(selectedTemplate, selectedSections);
      // In a real implementation, this would return a download URL
      setGeneratedReportUrl(`/api/v1/reports/${sceneId}/download`);
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (generatedReportUrl) {
      window.open(generatedReportUrl, '_blank');
    }
  };

  const handleReset = () => {
    setGeneratedReportUrl('');
    setSelectedTemplate('standard');
    setSelectedSections(REPORT_TEMPLATES[0].sections);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Generate Report">
      <div className="space-y-6">
        {/* Scene Info */}
        <div className="bg-surface-base rounded-lg p-4">
          <p className="text-sm text-text-secondary mb-1">Report for</p>
          <p className="text-base font-medium text-text-primary">{sceneName}</p>
        </div>

        {!generatedReportUrl ? (
          <>
            {/* Template Selection */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-3">
                Report Template
              </label>
              <div className="space-y-2">
                {REPORT_TEMPLATES.map((template) => (
                  <label
                    key={template.id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-border-subtle hover:border-accent-primary cursor-pointer transition-colors"
                  >
                    <input
                      type="radio"
                      name="template"
                      value={template.id}
                      checked={selectedTemplate === template.id}
                      onChange={() => handleTemplateChange(template.id)}
                      className="mt-1 w-4 h-4 text-accent-primary bg-surface-base border-border-subtle focus:ring-accent-primary"
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-text-primary">
                        {template.name}
                      </p>
                      <p className="text-xs text-text-secondary mt-1">
                        {template.description}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Section Selection (for custom template) */}
            {selectedTemplate === 'custom' && (
              <div>
                <label className="block text-sm font-medium text-text-primary mb-3">
                  Report Sections
                </label>
                <div className="space-y-2">
                  {AVAILABLE_SECTIONS.map((section) => (
                    <label
                      key={section.id}
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedSections.includes(section.id)}
                        onChange={() => toggleSection(section.id)}
                        className="w-4 h-4 text-accent-primary bg-surface-base border-border-subtle rounded focus:ring-accent-primary"
                      />
                      <span className="text-sm text-text-primary">{section.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Preview Sections */}
            {selectedTemplate !== 'custom' && selectedSections.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Included Sections
                </label>
                <div className="flex flex-wrap gap-2">
                  {selectedSections.map((sectionId) => {
                    const section = AVAILABLE_SECTIONS.find((s) => s.id === sectionId);
                    return (
                      <span
                        key={sectionId}
                        className="px-3 py-1 bg-accent-primary/10 text-accent-primary text-xs rounded-full"
                      >
                        {section?.name}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Generate Button */}
            <Button
              variant="primary"
              onClick={handleGenerate}
              disabled={isGenerating || selectedSections.length === 0}
              className="w-full"
            >
              {isGenerating ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Generating Report...
                </span>
              ) : (
                'Generate Report'
              )}
            </Button>
          </>
        ) : (
          <>
            {/* Success State */}
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-status-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-status-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                Report Generated Successfully
              </h3>
              <p className="text-sm text-text-secondary">
                Your report is ready to download
              </p>
            </div>

            {/* Download Button */}
            <Button variant="primary" onClick={handleDownload} className="w-full">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download PDF Report
            </Button>
          </>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-border-subtle">
          <Button variant="ghost" onClick={onClose} className="flex-1">
            {generatedReportUrl ? 'Done' : 'Cancel'}
          </Button>
          {generatedReportUrl && (
            <Button variant="secondary" onClick={handleReset} className="flex-1">
              Generate Another
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
