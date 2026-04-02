import React, { useState, useRef } from 'react';
import axios, { type CancelTokenSource } from 'axios';
import { Button } from '../common/Button';
import { useAppSelector } from '../../store/hooks';

export interface MultipleUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUploadComplete?: (sceneIds: string[]) => void;
  acceptedTypes?: 'video' | 'image' | 'both';
}

interface FileUploadState {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
  error?: string;
  sceneId?: string;
  cancelToken?: CancelTokenSource;
}

/**
 * MultipleUploadDialog - Upload multiple videos/images at once
 * 
 * Features:
 * - Multiple file selection
 * - Drag and drop multiple files
 * - Individual progress tracking
 * - Parallel uploads
 * - Cancel individual or all uploads
 */
export const MultipleUploadDialog: React.FC<MultipleUploadDialogProps> = ({
  open,
  onClose,
  onUploadComplete,
  acceptedTypes = 'both',
}) => {
  const token = useAppSelector(state => state.auth.token);
  
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<Map<string, FileUploadState>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const VIDEO_FORMATS = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska'];
  const IMAGE_FORMATS = ['image/jpeg', 'image/png', 'image/webp', 'image/tiff'];
  const MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024; // 5GB
  const MAX_FILES = 20;

  if (!open) return null;

  const getAcceptedFormats = () => {
    if (acceptedTypes === 'video') return VIDEO_FORMATS;
    if (acceptedTypes === 'image') return IMAGE_FORMATS;
    return [...VIDEO_FORMATS, ...IMAGE_FORMATS];
  };

  const getAcceptString = () => {
    if (acceptedTypes === 'video') return '.mp4,.mov,.avi,.webm,.mkv';
    if (acceptedTypes === 'image') return '.jpg,.jpeg,.png,.webp,.tiff';
    return '.mp4,.mov,.avi,.webm,.mkv,.jpg,.jpeg,.png,.webp,.tiff';
  };

  const validateFile = (file: File): string | null => {
    const acceptedFormats = getAcceptedFormats();
    if (!acceptedFormats.includes(file.type)) {
      return `Invalid file type: ${file.type}`;
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds 5GB limit';
    }
    return null;
  };

  const addFiles = (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const currentCount = files.size;
    
    if (currentCount + fileArray.length > MAX_FILES) {
      setError(`Maximum ${MAX_FILES} files allowed`);
      return;
    }

    const newFilesMap = new Map(files);
    
    fileArray.forEach(file => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      
      const fileId = `${file.name}-${file.size}-${Date.now()}`;
      newFilesMap.set(fileId, {
        file,
        progress: 0,
        status: 'pending',
      });
    });
    
    setFiles(newFilesMap);
    setError(null);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(e.target.files);
    }
  };

  const uploadFile = async (fileId: string, fileState: FileUploadState) => {
    const cancelToken = axios.CancelToken.source();
    
    // Update state with cancel token
    setFiles(prev => {
      const updated = new Map(prev);
      const state = updated.get(fileId);
      if (state) {
        state.cancelToken = cancelToken;
        state.status = 'uploading';
      }
      return updated;
    });

    try {
      const formData = new FormData();
      formData.append('file', fileState.file);
      
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const endpoint = acceptedTypes === 'image' ? '/photos/upload' : '/scenes/upload';
      
      const response = await axios.post(`${apiBaseUrl}${endpoint}`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        cancelToken: cancelToken.token,
        onUploadProgress: (progressEvent) => {
          const { loaded, total } = progressEvent;
          if (total) {
            const percentage = Math.round((loaded / total) * 100);
            setFiles(prev => {
              const updated = new Map(prev);
              const state = updated.get(fileId);
              if (state) {
                state.progress = percentage;
              }
              return updated;
            });
          }
        },
      });

      // Upload successful
      setFiles(prev => {
        const updated = new Map(prev);
        const state = updated.get(fileId);
        if (state) {
          state.status = 'completed';
          state.sceneId = response.data?.sceneId || response.data?._id;
        }
        return updated;
      });
    } catch (err) {
      if (!axios.isCancel(err)) {
        setFiles(prev => {
          const updated = new Map(prev);
          const state = updated.get(fileId);
          if (state) {
            state.status = 'failed';
            state.error = axios.isAxiosError(err) 
              ? err.response?.data?.message || 'Upload failed'
              : 'Upload failed';
          }
          return updated;
        });
      }
    }
  };

  const handleUploadAll = async () => {
    const pendingFiles = Array.from(files.entries()).filter(([_, state]) => state.status === 'pending');
    
    // Upload all files in parallel
    await Promise.all(
      pendingFiles.map(([fileId, fileState]) => uploadFile(fileId, fileState))
    );
    
    // Check if all completed
    const allCompleted = Array.from(files.values()).every(state => state.status === 'completed');
    if (allCompleted && onUploadComplete) {
      const sceneIds = Array.from(files.values())
        .map(state => state.sceneId)
        .filter(Boolean) as string[];
      onUploadComplete(sceneIds);
    }
  };

  const handleCancelFile = (fileId: string) => {
    const fileState = files.get(fileId);
    if (fileState?.cancelToken) {
      fileState.cancelToken.cancel('Upload cancelled by user');
    }
    
    setFiles(prev => {
      const updated = new Map(prev);
      updated.delete(fileId);
      return updated;
    });
  };

  const handleRemoveFile = (fileId: string) => {
    setFiles(prev => {
      const updated = new Map(prev);
      updated.delete(fileId);
      return updated;
    });
  };

  const handleClose = () => {
    // Cancel all ongoing uploads
    files.forEach((state, fileId) => {
      if (state.status === 'uploading' && state.cancelToken) {
        state.cancelToken.cancel('Dialog closed');
      }
    });
    
    setFiles(new Map());
    setError(null);
    setDragActive(false);
    onClose();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  const getStatusIcon = (status: FileUploadState['status']) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'uploading':
        return '⬆️';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
    }
  };

  const uploadingCount = Array.from(files.values()).filter(s => s.status === 'uploading').length;
  const completedCount = Array.from(files.values()).filter(s => s.status === 'completed').length;
  const failedCount = Array.from(files.values()).filter(s => s.status === 'failed').length;
  const totalCount = files.size;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm"
        onClick={handleClose}
      />

      <div className="relative bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-2xl max-w-4xl w-full p-6 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-text-primary">
              Upload Multiple {acceptedTypes === 'video' ? 'Videos' : acceptedTypes === 'image' ? 'Images' : 'Files'}
            </h2>
            {totalCount > 0 && (
              <p className="text-sm text-text-secondary mt-1">
                {completedCount}/{totalCount} completed
                {failedCount > 0 && ` • ${failedCount} failed`}
              </p>
            )}
          </div>
          <button
            onClick={handleClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Drop zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 mb-4 ${
            dragActive
              ? 'border-accent-primary bg-accent-primary/10'
              : 'border-border-color hover:border-accent-primary/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={getAcceptString()}
            onChange={handleFileInputChange}
            className="hidden"
            multiple
          />

          <svg
            className="mx-auto h-12 w-12 text-text-muted mb-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="text-base text-text-primary mb-2">
            Drag and drop files here
          </p>
          <p className="text-sm text-text-secondary mb-3">
            or click to browse
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
          >
            Choose Files
          </Button>
          <p className="text-xs text-text-muted mt-3">
            Max {MAX_FILES} files • Max 5GB per file
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* File list */}
        {files.size > 0 && (
          <div className="flex-1 overflow-y-auto mb-4 space-y-2">
            {Array.from(files.entries()).map(([fileId, fileState]) => (
              <div
                key={fileId}
                className="bg-secondary-bg rounded-lg p-4 border border-border-color"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getStatusIcon(fileState.status)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">
                      {fileState.file.name}
                    </p>
                    <p className="text-xs text-text-secondary">
                      {formatFileSize(fileState.file.size)}
                    </p>
                    {fileState.error && (
                      <p className="text-xs text-red-400 mt-1">{fileState.error}</p>
                    )}
                  </div>
                  
                  {/* Progress bar */}
                  {fileState.status === 'uploading' && (
                    <div className="w-32">
                      <div className="h-1.5 bg-primary-bg rounded-full overflow-hidden">
                        <div
                          className="h-full bg-accent-primary transition-all duration-300"
                          style={{ width: `${fileState.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-text-secondary text-center mt-1">
                        {fileState.progress}%
                      </p>
                    </div>
                  )}
                  
                  {/* Remove button */}
                  {(fileState.status === 'pending' || fileState.status === 'failed') && (
                    <button
                      onClick={() => handleRemoveFile(fileId)}
                      className="text-text-secondary hover:text-red-400 transition-colors"
                      title="Remove file"
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                  
                  {/* Cancel button */}
                  {fileState.status === 'uploading' && (
                    <button
                      onClick={() => handleCancelFile(fileId)}
                      className="text-text-secondary hover:text-red-400 transition-colors"
                      title="Cancel upload"
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <Button variant="ghost" onClick={handleClose} className="flex-1">
            {uploadingCount > 0 ? 'Cancel All' : 'Close'}
          </Button>
          <Button
            variant="primary"
            onClick={handleUploadAll}
            disabled={files.size === 0 || uploadingCount > 0}
            className="flex-1"
          >
            {uploadingCount > 0 ? `Uploading ${uploadingCount}...` : `Upload ${files.size} Files`}
          </Button>
        </div>
      </div>
    </div>
  );
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}
