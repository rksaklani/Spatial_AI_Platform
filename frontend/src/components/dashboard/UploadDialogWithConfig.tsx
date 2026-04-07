import React, { useState, useRef } from 'react';
import axios, { type CancelTokenSource } from 'axios';
import { Button } from '../common/Button';
import { useAppSelector } from '../../store/hooks';

export interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File) => void;
  onUploadComplete?: (sceneId: string) => void;
  onRefresh?: () => void;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed: number;
  estimatedTimeRemaining: number;
}

type UploadMode = 'video' | 'photos';
type Preset = 'fast' | 'balanced' | 'quality' | 'custom';

interface PipelineConfig {
  preset: Preset;
  frames: {
    frame_rate: number;
    max_frames: number;
    resize_width: number;
  };
  colmap: {
    feature_type: 'SIFT' | 'AKAZE';
    max_num_features: number;
    matching_type: 'exhaustive' | 'sequential' | 'vocab_tree';
    camera_model: 'SIMPLE_RADIAL' | 'PINHOLE' | 'RADIAL';
  };
  training: {
    iterations: number;
    sh_degree: number;
    densify_until_iter: number;
  };
  tiles: {
    lod_levels: number;
  };
}

const PRESET_CONFIGS: Record<Preset, Partial<PipelineConfig>> = {
  fast: {
    frames: { frame_rate: 2, max_frames: 300, resize_width: 1280 },
    colmap: { feature_type: 'SIFT', max_num_features: 6000, matching_type: 'sequential', camera_model: 'SIMPLE_RADIAL' },
    training: { iterations: 7000, sh_degree: 3, densify_until_iter: 3500 },
    tiles: { lod_levels: 2 },
  },
  balanced: {
    frames: { frame_rate: 3, max_frames: 400, resize_width: 1280 },
    colmap: { feature_type: 'SIFT', max_num_features: 8000, matching_type: 'sequential', camera_model: 'SIMPLE_RADIAL' },
    training: { iterations: 30000, sh_degree: 3, densify_until_iter: 15000 },
    tiles: { lod_levels: 3 },
  },
  quality: {
    frames: { frame_rate: 5, max_frames: 600, resize_width: 1920 },
    colmap: { feature_type: 'SIFT', max_num_features: 12000, matching_type: 'exhaustive', camera_model: 'SIMPLE_RADIAL' },
    training: { iterations: 50000, sh_degree: 4, densify_until_iter: 25000 },
    tiles: { lod_levels: 4 },
  },
  custom: {},
};

/**
 * Enhanced UploadDialog with pipeline configuration
 */
export const UploadDialogWithConfig: React.FC<UploadDialogProps> = ({
  open,
  onClose,
  onUpload,
  onUploadComplete,
  onRefresh,
}) => {
  const token = useAppSelector(state => state.auth.token);
  
  const [uploadMode, setUploadMode] = useState<UploadMode>('video');
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const [config, setConfig] = useState<PipelineConfig>({
    preset: 'balanced',
    ...PRESET_CONFIGS.balanced as PipelineConfig,
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cancelTokenRef = useRef<CancelTokenSource | null>(null);
  const uploadStartTimeRef = useRef<number>(0);
  const lastLoadedRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  const ACCEPTED_FORMATS = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska'];
  const ACCEPTED_IMAGE_FORMATS = ['image/jpeg', 'image/png', 'image/jpg'];
  const MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024; // 5GB
  const MAX_IMAGE_SIZE = 50 * 1024 * 1024; // 50MB per image
  const MIN_IMAGES = 10;
  const MAX_IMAGES = 1000;

  if (!open) return null;

  const validateFile = (file: File): string | null => {
    if (uploadMode === 'video') {
      if (!ACCEPTED_FORMATS.includes(file.type)) {
        return 'Invalid file type. Please upload MP4, MOV, AVI, WebM, or MKV files.';
      }
      if (file.size > MAX_FILE_SIZE) {
        return 'File size exceeds 5GB limit.';
      }
    } else {
      if (!ACCEPTED_IMAGE_FORMATS.includes(file.type)) {
        return 'Invalid file type. Please upload JPG or PNG files.';
      }
      if (file.size > MAX_IMAGE_SIZE) {
        return `File size exceeds 50MB limit: ${file.name}`;
      }
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

  const handleMultipleFileSelect = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    if (fileArray.length < MIN_IMAGES) {
      setError(`Please select at least ${MIN_IMAGES} photos`);
      return;
    }
    
    if (fileArray.length > MAX_IMAGES) {
      setError(`Maximum ${MAX_IMAGES} photos allowed`);
      return;
    }
    
    // Validate each file
    for (const file of fileArray) {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
    }
    
    setError(null);
    setSelectedFiles(fileArray);
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
      if (uploadMode === 'video' && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files[0]);
      } else if (uploadMode === 'photos') {
        handleMultipleFileSelect(e.dataTransfer.files);
      }
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      if (uploadMode === 'video' && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
      } else if (uploadMode === 'photos') {
        handleMultipleFileSelect(e.target.files);
      }
    }
  };

  const handlePresetChange = (preset: Preset) => {
    setConfig({
      preset,
      ...PRESET_CONFIGS[preset] as PipelineConfig,
    });
  };

  const handleUpload = async () => {
    if (uploadMode === 'video' && !selectedFile) return;
    if (uploadMode === 'photos' && selectedFiles.length === 0) return;

    setUploading(true);
    setError(null);
    uploadStartTimeRef.current = Date.now();
    lastLoadedRef.current = 0;
    lastTimeRef.current = Date.now();

    cancelTokenRef.current = axios.CancelToken.source();

    try {
      const formData = new FormData();
      
      if (uploadMode === 'video') {
        formData.append('file', selectedFile!);
      } else {
        // Append all photos
        selectedFiles.forEach((file) => {
          formData.append('files', file);
        });
      }
      
      formData.append('pipeline_config', JSON.stringify(config));
      
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const endpoint = uploadMode === 'video' ? '/scenes/upload' : '/scenes/upload-photos';
      
      const response = await axios.post(`${apiBaseUrl}${endpoint}`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        cancelToken: cancelTokenRef.current.token,
        onUploadProgress: (progressEvent) => {
          const { loaded, total } = progressEvent;
          
          if (total) {
            const currentTime = Date.now();
            const timeDiff = (currentTime - lastTimeRef.current) / 1000;
            const loadedDiff = loaded - lastLoadedRef.current;
            
            const speed = timeDiff > 0 ? loadedDiff / timeDiff : 0;
            const percentage = Math.round((loaded / total) * 100);
            const remainingBytes = total - loaded;
            const estimatedTimeRemaining = speed > 0 ? remainingBytes / speed : 0;
            
            setUploadProgress({
              loaded,
              total,
              percentage,
              speed,
              estimatedTimeRemaining,
            });
            
            lastLoadedRef.current = loaded;
            lastTimeRef.current = currentTime;
          }
        },
      });

      const sceneId = response.data?._id || response.data?.sceneId;
      
      if (onUploadComplete && sceneId) {
        onUploadComplete(sceneId);
      }
      
      if (uploadMode === 'video' && selectedFile) {
        onUpload(selectedFile);
      }
      
      if (onRefresh) {
        onRefresh();
      }
      
      handleClose();
    } catch (err) {
      if (axios.isCancel(err)) {
        setError('Upload cancelled');
      } else if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || err.response?.data?.message || 'Upload failed. Please try again.');
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
    setStep(1);
    setUploadMode('video');
    setSelectedFile(null);
    setSelectedFiles([]);
    setError(null);
    setDragActive(false);
    setUploading(false);
    setUploadProgress(null);
    setShowAdvanced(false);
    setConfig({
      preset: 'balanced',
      ...PRESET_CONFIGS.balanced as PipelineConfig,
    });
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

  const getEstimatedProcessingTime = (): string => {
    if (config.training.iterations <= 7000) return '5-15 min';
    if (config.training.iterations <= 30000) return '20-40 min';
    return '40-80 min';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm"
        onClick={handleClose}
      />

      <div className="relative bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-2xl max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-text-primary">
              {uploadMode === 'video' ? 'Upload Video' : 'Upload Photos'}
            </h2>
            <p className="text-sm text-text-secondary mt-1">
              Step {step} of 2: {step === 1 ? 'Select Files' : 'Configure Processing'}
            </p>
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

        {/* Step 1: File Selection */}
        {step === 1 && (
          <>
            {/* Mode Selection */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => {
                  setUploadMode('video');
                  setSelectedFile(null);
                  setSelectedFiles([]);
                  setError(null);
                }}
                className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                  uploadMode === 'video'
                    ? 'border-accent-primary bg-accent-primary/10'
                    : 'border-border-color hover:border-accent-primary/50'
                }`}
              >
                <div className="text-center">
                  <svg className="mx-auto h-8 w-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <p className="font-medium text-text-primary">Video</p>
                  <p className="text-xs text-text-secondary mt-1">Single video file</p>
                </div>
              </button>
              
              <button
                onClick={() => {
                  setUploadMode('photos');
                  setSelectedFile(null);
                  setSelectedFiles([]);
                  setError(null);
                }}
                className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                  uploadMode === 'photos'
                    ? 'border-accent-primary bg-accent-primary/10'
                    : 'border-border-color hover:border-accent-primary/50'
                }`}
              >
                <div className="text-center">
                  <svg className="mx-auto h-8 w-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p className="font-medium text-text-primary">Photos</p>
                  <p className="text-xs text-text-secondary mt-1">10-1000 images</p>
                </div>
              </button>
            </div>

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
                accept={uploadMode === 'video' ? ".mp4,.mov,.avi,.webm,.mkv" : ".jpg,.jpeg,.png"}
                multiple={uploadMode === 'photos'}
                onChange={handleFileInputChange}
                className="hidden"
              />

              {uploadMode === 'video' && !selectedFile && (
                <>
                  <svg className="mx-auto h-16 w-16 text-text-muted mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-lg text-text-primary mb-2">Drag and drop your video here</p>
                  <p className="text-sm text-text-secondary mb-4">or click to browse</p>
                  <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                    Choose File
                  </Button>
                  <p className="text-xs text-text-muted mt-4">
                    Supported formats: MP4, MOV, AVI, WebM, MKV (max 5GB)
                  </p>
                </>
              )}

              {uploadMode === 'video' && selectedFile && (
                <div className="space-y-4">
                  <svg className="mx-auto h-16 w-16 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-lg text-text-primary font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-text-secondary">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedFile(null)}>
                    Choose Different File
                  </Button>
                </div>
              )}

              {uploadMode === 'photos' && selectedFiles.length === 0 && (
                <>
                  <svg className="mx-auto h-16 w-16 text-text-muted mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p className="text-lg text-text-primary mb-2">Drag and drop your photos here</p>
                  <p className="text-sm text-text-secondary mb-4">or click to browse</p>
                  <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                    Choose Photos
                  </Button>
                  <p className="text-xs text-text-muted mt-4">
                    Supported formats: JPG, PNG • Min: 10 photos • Max: 1000 photos • 50MB per photo
                  </p>
                </>
              )}

              {uploadMode === 'photos' && selectedFiles.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg text-text-primary font-medium">
                        {selectedFiles.length} photos selected
                      </p>
                      <p className="text-sm text-text-secondary">
                        Total size: {formatFileSize(selectedFiles.reduce((sum, f) => sum + f.size, 0))}
                      </p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setSelectedFiles([])}>
                      Clear All
                    </Button>
                  </div>
                  
                  {/* Photo grid preview */}
                  <div className="grid grid-cols-6 gap-2 max-h-48 overflow-y-auto p-2 bg-secondary-bg/30 rounded-lg">
                    {selectedFiles.slice(0, 18).map((file, idx) => (
                      <div key={idx} className="aspect-square bg-secondary-bg rounded overflow-hidden border border-border-color">
                        <img
                          src={URL.createObjectURL(file)}
                          alt={file.name}
                          className="w-full h-full object-cover"
                          onLoad={(e) => URL.revokeObjectURL((e.target as HTMLImageElement).src)}
                        />
                      </div>
                    ))}
                    {selectedFiles.length > 18 && (
                      <div className="aspect-square bg-secondary-bg rounded flex items-center justify-center border border-border-color">
                        <p className="text-xs text-text-secondary font-medium">+{selectedFiles.length - 18}</p>
                      </div>
                    )}
                  </div>
                  
                  <Button variant="ghost" size="sm" onClick={() => fileInputRef.current?.click()}>
                    Add More Photos
                  </Button>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <Button variant="ghost" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => setStep(2)}
                disabled={uploadMode === 'video' ? !selectedFile : selectedFiles.length === 0}
                className="flex-1"
              >
                Next: Configure
              </Button>
            </div>
          </>
        )}

        {/* Step 2: Configuration */}
        {step === 2 && (
          <>
            <div className="space-y-6">
              {/* Preset Selection */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-3">
                  Processing Preset
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['fast', 'balanced', 'quality'] as const).map((preset) => (
                    <button
                      key={preset}
                      onClick={() => handlePresetChange(preset)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        config.preset === preset
                          ? 'border-accent-primary bg-accent-primary/10'
                          : 'border-border-color hover:border-accent-primary/50'
                      }`}
                    >
                      <div className="text-left">
                        <p className="font-medium text-text-primary capitalize">{preset}</p>
                        <p className="text-xs text-text-secondary mt-1">
                          {preset === 'fast' && '5-15 min • Quick preview'}
                          {preset === 'balanced' && '20-40 min • Recommended'}
                          {preset === 'quality' && '40-80 min • Best quality'}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Preset Details */}
              <div className="bg-secondary-bg/50 rounded-lg p-4 space-y-2">
                <h4 className="font-medium text-text-primary">Configuration Summary</h4>
                <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                  <div>
                    <span className="text-text-secondary">Frame Rate:</span>
                    <span className="text-text-primary ml-2">{config.frames.frame_rate} fps</span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Max Frames:</span>
                    <span className="text-text-primary ml-2">{config.frames.max_frames}</span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Training Iterations:</span>
                    <span className="text-text-primary ml-2">{config.training.iterations.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Est. Time:</span>
                    <span className="text-text-primary ml-2">{getEstimatedProcessingTime()}</span>
                  </div>
                </div>
              </div>

              {/* Advanced Options Toggle */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-sm text-accent-primary hover:text-accent-secondary transition-colors flex items-center gap-2"
              >
                <svg
                  className={`h-4 w-4 transition-transform ${showAdvanced ? 'rotate-90' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                Advanced Options
              </button>

              {/* Advanced Options */}
              {showAdvanced && (
                <div className="space-y-4 pl-6 border-l-2 border-border-color">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      Training Iterations
                    </label>
                    <input
                      type="range"
                      min="7000"
                      max="50000"
                      step="1000"
                      value={config.training.iterations}
                      onChange={(e) => {
                        const iterations = parseInt(e.target.value);
                        setConfig({
                          ...config,
                          preset: 'custom',
                          training: {
                            ...config.training,
                            iterations,
                            densify_until_iter: Math.floor(iterations * 0.5),
                          },
                        });
                      }}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-text-muted mt-1">
                      <span>7k (fast)</span>
                      <span className="text-text-primary font-medium">{config.training.iterations.toLocaleString()}</span>
                      <span>50k (best)</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      Frame Rate (fps)
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={config.frames.frame_rate}
                      onChange={(e) => setConfig({
                        ...config,
                        preset: 'custom',
                        frames: { ...config.frames, frame_rate: parseInt(e.target.value) },
                      })}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-text-muted mt-1">
                      <span>1</span>
                      <span className="text-text-primary font-medium">{config.frames.frame_rate}</span>
                      <span>10</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Upload Progress */}
            {uploading && uploadProgress && (
              <div className="mt-6 space-y-3">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-secondary">Uploading...</span>
                    <span className="text-text-primary font-medium">{uploadProgress.percentage}%</span>
                  </div>
                  <div className="h-2 bg-secondary-bg rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress.percentage}%` }}
                    />
                  </div>
                </div>
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

            {error && (
              <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              {uploading ? (
                <Button variant="ghost" onClick={handleClose} className="flex-1">
                  Cancel Upload
                </Button>
              ) : (
                <>
                  <Button variant="ghost" onClick={() => setStep(1)} className="flex-1">
                    Back
                  </Button>
                  <Button variant="primary" onClick={handleUpload} className="flex-1">
                    Upload & Process
                  </Button>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
