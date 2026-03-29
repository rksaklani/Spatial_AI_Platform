import { useState, useRef, useEffect } from 'react';
import { Button } from '../common/Button';
import {
  useGetSupportedFormatsQuery,
  useUpload3DFileMutation,
  useGetImportStatusQuery,
} from '../../store/api/importApi';

interface ImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImportComplete?: (sceneId: string) => void;
}

const FORMAT_ICONS: Record<string, string> = {
  point_cloud: '☁️',
  mesh: '🔷',
  gaussian: '✨',
  bim: '🏢',
};

export function ImportDialog({ open, onClose, onImportComplete }: ImportDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sceneName, setSceneName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: formatsData } = useGetSupportedFormatsQuery();
  const [uploadFile, { isLoading: isUploading }] = useUpload3DFileMutation();
  const { data: statusData } = useGetImportStatusQuery(jobId || '', {
    skip: !jobId,
    pollingInterval: 2000,
  });

  useEffect(() => {
    if (statusData?.status === 'completed') {
      onImportComplete?.(statusData.scene_id);
      handleClose();
    } else if (statusData?.status === 'failed') {
      setError(statusData.error || 'Import failed');
      setJobId(null);
    }
  }, [statusData, onImportComplete]);

  if (!open) return null;

  const handleFileSelect = (file: File) => {
    if (!formatsData) return;

    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    const isSupported = formatsData.formats.some(f => f.extension === extension);

    if (!isSupported) {
      setError(`Unsupported file format: ${extension}`);
      setSelectedFile(null);
      return;
    }

    const maxSizeBytes = formatsData.max_file_size_mb * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`File size exceeds ${formatsData.max_file_size_mb}MB limit`);
      setSelectedFile(null);
      return;
    }

    setError(null);
    setSelectedFile(file);
    if (!sceneName) {
      setSceneName(file.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const result = await uploadFile({
        file: selectedFile,
        name: sceneName || selectedFile.name,
      }).unwrap();

      setJobId(result.job_id);
    } catch (err: any) {
      setError(err?.data?.message || 'Upload failed');
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setSceneName('');
    setError(null);
    setJobId(null);
    onClose();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  const groupedFormats = formatsData?.formats.reduce((acc, format) => {
    if (!acc[format.format_type]) {
      acc[format.format_type] = [];
    }
    acc[format.format_type].push(format);
    return acc;
  }, {} as Record<string, typeof formatsData.formats>);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm" onClick={handleClose} />

      <div className="relative bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-2xl max-w-3xl w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-text-primary">Import 3D File</h2>
          <button onClick={handleClose} className="text-text-secondary hover:text-text-primary transition-colors">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {!jobId ? (
          <>
            {/* Supported formats */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-text-primary mb-3">Supported Formats</h3>
              <div className="space-y-3">
                {groupedFormats && Object.entries(groupedFormats).map(([type, formats]) => (
                  <div key={type} className="bg-secondary-bg rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{FORMAT_ICONS[type]}</span>
                      <span className="text-sm font-medium text-text-primary capitalize">
                        {type.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {formats.map(format => (
                        <span
                          key={format.extension}
                          className="px-2 py-1 bg-primary-bg rounded text-xs text-text-secondary font-mono"
                        >
                          {format.extension}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* File input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-text-primary mb-2">
                Select File
              </label>
              <input
                ref={fileInputRef}
                type="file"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-accent-primary file:text-white file:cursor-pointer"
              />
              {formatsData && (
                <p className="text-xs text-text-muted mt-1">
                  Max file size: {formatsData.max_file_size_mb}MB
                </p>
              )}
            </div>

            {/* Scene name */}
            {selectedFile && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Scene Name
                </label>
                <input
                  type="text"
                  value={sceneName}
                  onChange={(e) => setSceneName(e.target.value)}
                  placeholder="Enter scene name"
                  className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                />
              </div>
            )}

            {/* Selected file info */}
            {selectedFile && (
              <div className="mb-4 p-4 bg-secondary-bg rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📄</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-text-primary">{selectedFile.name}</p>
                    <p className="text-xs text-text-secondary">{formatFileSize(selectedFile.size)}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <Button variant="ghost" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="flex-1"
              >
                {isUploading ? 'Uploading...' : 'Import'}
              </Button>
            </div>
          </>
        ) : (
          <>
            {/* Import progress */}
            <div className="space-y-4">
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-accent-primary mx-auto mb-4"></div>
                <p className="text-lg font-medium text-text-primary mb-2">
                  {statusData?.current_step || 'Processing...'}
                </p>
                {statusData && (
                  <div className="space-y-2">
                    <div className="w-full max-w-xs mx-auto h-2 bg-secondary-bg rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-500"
                        style={{ width: `${statusData.progress_percent}%` }}
                      />
                    </div>
                    <p className="text-sm text-text-secondary">
                      {statusData.progress_percent}% complete
                    </p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
