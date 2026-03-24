import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetScenesQuery } from '../store/api/sceneApi';
import { useGetPhotosQuery, useUploadPhotoMutation } from '../store/api/photoApi';
import { Button } from '../components/common/Button';
import { PhotoIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';

export function PhotosPage() {
  const navigate = useNavigate();
  const [selectedSceneId, setSelectedSceneId] = useState<string>('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  
  const { data: scenes = [] } = useGetScenesQuery();
  const { data: photos = [], isLoading } = useGetPhotosQuery(selectedSceneId, {
    skip: !selectedSceneId,
  });
  const [uploadPhoto, { isLoading: isUploading }] = useUploadPhotoMutation();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile || !selectedSceneId) return;
    
    try {
      await uploadPhoto({ sceneId: selectedSceneId, file: uploadFile }).unwrap();
      setUploadFile(null);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handlePhotoClick = (photoId: string) => {
    navigate(`/photos/${photoId}`);
  };

  return (
    <div className="min-h-screen p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Photos</h1>
        <p className="text-text-secondary">Upload and manage gigapixel photos for your scenes</p>
      </div>

      <div className="bg-secondary-bg border border-border-color rounded-xl p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
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
            <label className="block text-sm font-medium text-text-primary mb-2">
              Upload Photo
            </label>
            <div className="flex gap-2">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                disabled={!selectedSceneId}
                className="flex-1 px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary file:mr-4 file:py-1 file:px-4 file:rounded file:border-0 file:bg-accent-primary file:text-white"
              />
              <Button
                variant="primary"
                onClick={handleUpload}
                disabled={!uploadFile || !selectedSceneId || isUploading}
                icon={<ArrowUpTrayIcon className="w-5 h-5" />}
              >
                Upload
              </Button>
            </div>
          </div>
        </div>
      </div>

      {selectedSceneId && (
        <div>
          <h2 className="text-xl font-bold text-text-primary mb-4">
            Photos ({photos.length})
          </h2>
          
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto"></div>
              <p className="text-text-secondary mt-4">Loading photos...</p>
            </div>
          ) : photos.length === 0 ? (
            <div className="text-center py-12 bg-secondary-bg border border-border-color rounded-xl">
              <PhotoIcon className="w-16 h-16 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">No photos uploaded yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {photos.map((photo) => (
                <div
                  key={photo.id}
                  onClick={() => handlePhotoClick(photo.id)}
                  className="bg-secondary-bg border border-border-color rounded-xl overflow-hidden cursor-pointer hover:border-accent-primary transition-all"
                >
                  <div className="aspect-square bg-primary-bg flex items-center justify-center">
                    <PhotoIcon className="w-12 h-12 text-text-muted" />
                  </div>
                  <div className="p-3">
                    <p className="text-sm font-medium text-text-primary truncate">
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
