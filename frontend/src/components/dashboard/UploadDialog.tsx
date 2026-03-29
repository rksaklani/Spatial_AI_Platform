import React, { useState, useRef } from 'react';
import axios, { type CancelTokenSource } from 'axios';
import { Button } from '../common/Button';
import { useAppSelector } from '../../store/hooks';

export interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File) => void;
  onUploadComplete?: (sceneId: string) => void;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed: number; // bytes per second
  estimatedTimeRemaining: number; // seconds
}

/**
 * UploadDialog component - modal for uploading video files
 * 
 * Features:
 * - File picker with drag-and-drop
 * - File type and size validation
 * - Upload progress display
 * - Glassmorphism modal design
 * 
 * Requirements: 3.1, 3.2, 3.3
 */
export const UploadDialog: React.FC<UploadDialogProps> = ({
  open,
  onClose,
  onUpload,
  onUploadComplete,
}) => {
  // Get auth token from Redux store
  const token = useAppSelector(state => state.auth.token);
  
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cancelTokenRef = useRef<CancelTokenSource | null>(null);
  const uploadStartTimeRef = useRef<number>(0);
  const lastLoadedRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  const ACCEPTED_FORMATS = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska'];
  const MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024; // 5GB

  if (!open) return null;

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_FORMATS.includes(file.type)) {
      return 'Invalid file type. Please upload MP4, MOV, AVI, WebM, or MKV files.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds 5GB limit.';
    }
    return null;
  };

  const handleFileSelect = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }
    setError(null);
    setSelectedFile(file);
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

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    uploadStartTimeRef.current = Date.now();
    lastLoadedRef.current = 0;
    lastTimeRef.current = Date.now();

    // Create cancel token
    cancelTokenRef.current = axios.CancelToken.source();

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // Get API base URL from environment
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      
      const response = await axios.post(`${apiBaseUrl}/scenes/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`,
        },
        cancelToken: cancelTokenRef.current.token,
        onUploadProgress: (progressEvent) => {
          const { loaded, total } = progressEvent;
          
          if (total) {
            const currentTime = Date.now();
            const timeDiff = (currentTime - lastTimeRef.current) / 1000; // seconds
            const loadedDiff = loaded - lastLoadedRef.current;
            
            // Calculate upload speed (bytes per second)
            const speed = timeDiff > 0 ? loadedDiff / timeDiff : 0;
            
            // Calculate percentage
            const percentage = Math.round((loaded / total) * 100);
            
            // Calculate ETA (estimated time remaining in seconds)
            const remainingBytes = total - loaded;
            const estimatedTimeRemaining = speed > 0 ? remainingBytes / speed : 0;
            
            setUploadProgress({
              loaded,
              total,
              percentage,
              speed,
              estimatedTimeRemaining,
            });
            
            // Update refs for next calculation
            lastLoadedRef.current = loaded;
            lastTimeRef.current = currentTime;
          }
        },
      });

      // Upload successful
      if (onUploadComplete && response.data?.sceneId) {
        onUploadComplete(response.data.sceneId);
      }
      
      // Call the original onUpload callback
      onUpload(selectedFile);
      
      // Close dialog
      handleClose();
    } catch (err) {
      if (axios.isCancel(err)) {
        setError('Upload cancelled');
      } else if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message || 'Upload failed. Please try again.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      setUploading(false);
      setUploadProgress(null);
    }
  };

  const handleCancelUpload = () => {
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel('Upload cancelled by user');
      cancelTokenRef.current = null;
    }
    setUploading(false);
    setUploadProgress(null);
  };

  const handleClose = () => {
    if (uploading) {
      handleCancelUpload();
    }
    setSelectedFile(null);
    setError(null);
    setDragActive(false);
    setUploading(false);
    setUploadProgress(null);
    onClose();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  const formatSpeed = (bytesPerSecond: number): string => {
    if (bytesPerSecond < 1024) return bytesPerSecond.toFixed(0) + ' B/s';
    if (bytesPerSecond < 1024 * 1024) return (bytesPerSecond / 1024).toFixed(1) + ' KB/s';
    return (bytesPerSecond / (1024 * 1024)).toFixed(1) + ' MB/s';
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return Math.round(seconds) + 's';
    if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const secs = Math.round(seconds % 60);
      return `${minutes}m ${secs}s`;
    }
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-2xl max-w-2xl w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-text-primary">Upload Video</h2>
          <button
            onClick={handleClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Drop zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 ${
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
            accept=".mp4,.mov,.avi,.webm,.mkv"
            onChange={handleFileInputChange}
            className="hidden"
          />

          {!selectedFile ? (
            <>
              <svg
                className="mx-auto h-16 w-16 text-text-muted mb-4"
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
              <p className="text-lg text-text-primary mb-2">
                Drag and drop your video here
              </p>
              <p className="text-sm text-text-secondary mb-4">
                or click to browse
              </p>
              <Button
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
              >
                Choose File
              </Button>
              <p className="text-xs text-text-muted mt-4">
                Supported formats: MP4, MOV, AVI, WebM, MKV (max 5GB)
              </p>
            </>
          ) : (
            <div className="space-y-4">
              <svg
                className="mx-auto h-16 w-16 text-accent-primary"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <p className="text-lg text-text-primary font-medium">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-text-secondary">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedFile(null)}
              >
                Choose Different File
              </Button>
            </div>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Upload progress */}
        {uploading && uploadProgress && (
          <div className="mt-6 space-y-3">
            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Uploading...</span>
                <span className="text-text-primary font-medium">
                  {uploadProgress.percentage}%
                </span>
              </div>
              <div className="h-2 bg-secondary-bg rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress.percentage}%` }}
                />
              </div>
            </div>

            {/* Upload stats */}
            <div className="flex justify-between text-xs text-text-secondary">
              <span>
                {formatFileSize(uploadProgress.loaded)} / {formatFileSize(uploadProgress.total)}
              </span>
              <span>
                {formatSpeed(uploadProgress.speed)} • ETA: {formatTime(uploadProgress.estimatedTimeRemaining)}
              </span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 mt-6">
          {uploading ? (
            <>
              <Button variant="ghost" onClick={handleClose} className="flex-1">
                Cancel Upload
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleUpload}
                disabled={!selectedFile}
                className="flex-1"
              >
                Upload
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
