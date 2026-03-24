import { useState } from 'react';
import { useGetScenesQuery } from '../store/api/sceneApi';
import { useGenerateReportMutation, useGetReportStatusQuery } from '../store/api/reportApi';
import { Button } from '../components/common/Button';
import { DocumentTextIcon, ArrowDownTrayIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

export function ReportsPage() {
  const [selectedSceneId, setSelectedSceneId] = useState<string>('');
  const [generatedReportId, setGeneratedReportId] = useState<string>('');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeAnnotations, setIncludeAnnotations] = useState(true);
  const [includePhotos, setIncludePhotos] = useState(false);
  const [includeMeasurements, setIncludeMeasurements] = useState(true);
  
  const { data: scenes = [] } = useGetScenesQuery();
  const [generateReport, { isLoading: isGenerating }] = useGenerateReportMutation();
  const { data: reportStatus } = useGetReportStatusQuery(
    { sceneId: selectedSceneId, reportId: generatedReportId },
    { skip: !selectedSceneId || !generatedReportId, pollingInterval: 2000 }
  );

  const handleGenerateReport = async () => {
    if (!selectedSceneId) return;
    
    try {
      const result = await generateReport({
        sceneId: selectedSceneId,
        options: {
          include_metadata: includeMetadata,
          include_annotations: includeAnnotations,
          include_photos: includePhotos,
          include_measurements: includeMeasurements,
        },
      }).unwrap();
      
      setGeneratedReportId(result.id);
    } catch (error) {
      console.error('Report generation failed:', error);
    }
  };

  const handleDownload = () => {
    if (reportStatus?.download_url) {
      window.open(reportStatus.download_url, '_blank');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'processing':
        return 'text-blue-400';
      default:
        return 'text-text-muted';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-400" />;
      case 'processing':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-400"></div>;
      default:
        return <DocumentTextIcon className="w-5 h-5 text-text-muted" />;
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Reports</h1>
        <p className="text-text-secondary">Generate PDF reports for your 3D scenes</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Report Generation */}
        <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <DocumentTextIcon className="w-6 h-6 text-accent-primary" />
            <h2 className="text-xl font-bold text-text-primary">Generate Report</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Select Scene
              </label>
              <select
                value={selectedSceneId}
                onChange={(e) => setSelectedSceneId(e.target.value)}
                className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
              >
                <option value="">Choose a scene...</option>
                {scenes.map((scene) => (
                  <option key={scene.sceneId} value={scene.sceneId}>
                    {scene.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <p className="text-sm font-medium text-text-primary mb-3">Report Options</p>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeMetadata}
                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                    className="w-4 h-4 rounded border-border-color bg-primary-bg text-accent-primary focus:ring-2 focus:ring-accent-primary"
                  />
                  <span className="text-sm text-text-secondary">Include Metadata</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeAnnotations}
                    onChange={(e) => setIncludeAnnotations(e.target.checked)}
                    className="w-4 h-4 rounded border-border-color bg-primary-bg text-accent-primary focus:ring-2 focus:ring-accent-primary"
                  />
                  <span className="text-sm text-text-secondary">Include Annotations</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includePhotos}
                    onChange={(e) => setIncludePhotos(e.target.checked)}
                    className="w-4 h-4 rounded border-border-color bg-primary-bg text-accent-primary focus:ring-2 focus:ring-accent-primary"
                  />
                  <span className="text-sm text-text-secondary">Include Photos</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeMeasurements}
                    onChange={(e) => setIncludeMeasurements(e.target.checked)}
                    className="w-4 h-4 rounded border-border-color bg-primary-bg text-accent-primary focus:ring-2 focus:ring-accent-primary"
                  />
                  <span className="text-sm text-text-secondary">Include Measurements</span>
                </label>
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleGenerateReport}
              disabled={!selectedSceneId || isGenerating}
              icon={<DocumentTextIcon className="w-5 h-5" />}
              className="w-full"
            >
              {isGenerating ? 'Generating...' : 'Generate Report'}
            </Button>
          </div>
        </div>

        {/* Report Status */}
        <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <DocumentTextIcon className="w-6 h-6 text-accent-primary" />
            <h2 className="text-xl font-bold text-text-primary">Report Status</h2>
          </div>

          {reportStatus ? (
            <div className="space-y-4">
              <div className="p-4 bg-primary-bg rounded-lg">
                <div className="flex items-center gap-3 mb-3">
                  {getStatusIcon(reportStatus.status)}
                  <div>
                    <p className="text-sm text-text-muted">Status</p>
                    <p className={`text-lg font-medium capitalize ${getStatusColor(reportStatus.status)}`}>
                      {reportStatus.status}
                    </p>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-text-muted">Report ID: </span>
                    <span className="text-text-primary font-mono">{reportStatus.id}</span>
                  </div>
                  <div>
                    <span className="text-text-muted">Created: </span>
                    <span className="text-text-primary">
                      {new Date(reportStatus.created_at).toLocaleString()}
                    </span>
                  </div>
                  {reportStatus.completed_at && (
                    <div>
                      <span className="text-text-muted">Completed: </span>
                      <span className="text-text-primary">
                        {new Date(reportStatus.completed_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {reportStatus.status === 'completed' && reportStatus.download_url && (
                <Button
                  variant="primary"
                  onClick={handleDownload}
                  icon={<ArrowDownTrayIcon className="w-5 h-5" />}
                  className="w-full"
                >
                  Download Report
                </Button>
              )}

              {reportStatus.status === 'failed' && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <p className="text-sm text-red-400">
                    Report generation failed. Please try again.
                  </p>
                </div>
              )}

              {reportStatus.status === 'processing' && (
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <p className="text-sm text-blue-400">
                    Your report is being generated. This may take a few minutes...
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <DocumentTextIcon className="w-16 h-16 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">No report generated yet</p>
              <p className="text-sm text-text-muted mt-2">
                Select a scene and generate a report to see its status here
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
