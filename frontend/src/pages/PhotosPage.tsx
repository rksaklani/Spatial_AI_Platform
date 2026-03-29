import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useGetScenesQuery } from '../store/api/sceneApi';
import { useGetPhotosQuery, useUploadPhotoMutation } from '../store/api/photoApi';
import { Button, Dropdown } from '../components/common';
import { PhotoIcon, ArrowUpTrayIcon, CubeIcon, CloudArrowUpIcon } from '@heroicons/react/24/outline';

export function PhotosPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedSceneId, setSelectedSceneId] = useState<string>('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string>('');
  
  const { data: scenes = [], isLoading: scenesLoading, error: scenesError } = useGetScenesQuery();
  const { data: photos = [], isLoading: photosLoading } = useGetPhotosQuery(selectedSceneId, {
    skip: !selectedSceneId,
  });
  const [uploadPhoto, { isLoading: isUploading }] = useUploadPhotoMutation();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError('');
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setUploadError('Please select an image file');
        return;
      }
      
      // Validate file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        setUploadError('File size must be less than 100MB');
        return;
      }
      
      setUploadFile(file);
    }
  };

  const handleChooseFile = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!uploadFile || !selectedSceneId) return;
    
    setUploadError('');
    try {
      await uploadPhoto({ sceneId: selectedSceneId, file: uploadFile }).unwrap();
      setUploadFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      console.error('Upload failed:', error);
      setUploadError(error?.data?.message || 'Failed to upload photo. Please try again.');
    }
  };

  const handlePhotoClick = (photoId: string) => {
    navigate(`/photos/${photoId}`);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // No scenes available
  if (!scenesLoading && scenes.length === 0) {
    return (
      <div className="min-h-screen p-4 sm:p-6 lg:p-8 flex items-center justify-center">
        <div className="max-w-md w-full text-center">
          <div className="bg-secondary-bg/70 backdrop-blur-sm border border-border-color rounded-2xl p-8 shadow-glass">
            <div className="w-20 h-20 bg-gradient-to-br from-accent-primary/20 to-accent-secondary/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CubeIcon className="w-10 h-10 text-accent-primary" />
            </div>
            <h2 className="text-2xl font-bold text-text-primary mb-3">No Scenes Available</h2>
            <p className="text-text-secondary mb-6">
              You need to create a 3D scene first before uploading photos.
            </p>
            <Link to="/scenes">
              <Button variant="primary" size="lg" icon={<CubeIcon className="w-5 h-5" />}>
                Go to 3D Scenes
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 sm:p-6 lg:p-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-text-primary mb-2">Photos</h1>
        <p className="text-sm sm:text-base text-text-secondary">Upload and manage gigapixel photos for your scenes</p>
      </div>

      {/* Upload Section */}
      <div className="bg-secondary-bg/70 backdrop-blur-sm border border-border-color rounded-2xl p-6 sm:p-8 mb-6 shadow-glass">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-lg flex items-center justify-center shadow-glow">
            <CloudArrowUpIcon className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-bold text-text-primary">Upload Photo</h2>
        </div>

        <div className="space-y-4">
          {/* Scene Selection */}
          <div>
            {scenesLoading ? (
              <div className="text-text-secondary text-sm">Loading scenes...</div>
            ) : scenesError ? (
              <div className="text-red-400 text-sm">Error loading scenes. Please refresh.</div>
            ) : (
              <Dropdown
                label="Select Scene"
                value={selectedSceneId}
                onChange={setSelectedSceneId}
                options={scenes.map(scene => ({
                  value: scene.sceneId,
                  label: scene.name
                }))}
                placeholder="Choose a scene..."
                required
              />
            )}
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-primary mb-2">
              Photo File
              <span className="text-text-muted ml-2">(Max 100MB)</span>
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleChooseFile}
                disabled={!selectedSceneId}
                className="flex-1 px-4 py-3 bg-secondary-bg/70 backdrop-blur-sm border-2 border-dashed border-border-color rounded-xl hover:border-accent-primary transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <div className="flex items-center justify-center gap-3">
                  <PhotoIcon className="w-6 h-6 text-accent-primary group-hover:scale-110 transition-transform" />
                  <div className="text-left">
                    <p className="text-sm font-medium text-text-primary">
                      {uploadFile ? uploadFile.name : 'Choose a photo'}
                    </p>
                    {uploadFile && (
                      <p className="text-xs text-text-muted">
                        {formatFileSize(uploadFile.size)}
                      </p>
                    )}
                    {!uploadFile && (
                      <p className="text-xs text-text-muted">
                        Click to browse
                      </p>
                    )}
                  </div>
                </div>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                disabled={!selectedSceneId}
                className="hidden"
              />
              <Button
                variant="primary"
                onClick={handleUpload}
                disabled={!uploadFile || !selectedSceneId || isUploading}
                icon={<ArrowUpTrayIcon className="w-5 h-5" />}
                className="w-full sm:w-auto px-8"
                size="lg"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </Button>
            </div>
            {!selectedSceneId && (
              <p className="text-xs text-text-muted mt-2">Please select a scene first</p>
            )}
            {uploadError && (
              <p className="text-xs text-red-400 mt-2">{uploadError}</p>
            )}
          </div>
        </div>
      </div>

      {/* Photos Grid */}
      {selectedSceneId && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg sm:text-xl font-bold text-text-primary">
              Photos {photos.length > 0 && `(${photos.length})`}
            </h2>
          </div>
          
          {photosLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto"></div>
              <p className="text-text-secondary mt-4">Loading photos...</p>
            </div>
          ) : photos.length === 0 ? (
            <div className="text-center py-16 bg-secondary-bg/70 backdrop-blur-sm border border-border-color rounded-2xl shadow-glass">
              <PhotoIcon className="w-16 h-16 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary text-lg mb-2">No photos uploaded yet</p>
              <p className="text-text-muted text-sm">Upload your first photo to get started</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {photos.map((photo) => (
                <div
                  key={photo.id}
                  onClick={() => handlePhotoClick(photo.id)}
                  className="bg-secondary-bg/70 backdrop-blur-sm border border-border-color rounded-xl overflow-hidden cursor-pointer hover:border-accent-primary hover:shadow-glow transition-all duration-200 group"
                >
                  <div className="aspect-square bg-primary-bg flex items-center justify-center relative overflow-hidden">
                    <PhotoIcon className="w-12 h-12 text-text-muted group-hover:scale-110 transition-transform duration-200" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div className="p-4">
                    <p className="text-sm font-medium text-text-primary truncate mb-1">
                      {photo.filename}
                    </p>
                    <p className="text-xs text-text-muted">
                      {photo.width} × {photo.height}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
