/**
 * Photo Inspector Component
 * 
 * Task 28.4: Implement view synchronization
 * - Synchronize 3D camera with photo viewpoint
 * - Highlight 3D position when clicking in photo
 * 
 * Requirements: 26.7, 26.9
 */

import React, { useState, useEffect, useCallback } from 'react';
import GigapixelViewer from './GigapixelViewer';

interface PhotoMarker {
  photo_id: string;
  filename: string;
  position: [number, number, number];
  rotation?: [number, number, number, number];
  thumbnail_url?: string;
  megapixels: number;
  capture_datetime?: string;
}

interface PhotoMetadata {
  id: string;
  filename: string;
  width: number;
  height: number;
  megapixels: number;
  originalUrl: string;
  tilesUrl?: string;
  position: [number, number, number];
  rotation?: [number, number, number, number];
}

interface PhotoInspectorProps {
  sceneId: string;
  markers: PhotoMarker[];
  onCameraSync?: (position: [number, number, number], rotation?: [number, number, number, number]) => void;
  onPositionHighlight?: (position: [number, number, number]) => void;
}

const PhotoInspector: React.FC<PhotoInspectorProps> = ({
  sceneId,
  markers,
  onCameraSync,
  onPositionHighlight,
}) => {
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Load photo details when marker is clicked
  const handleMarkerClick = useCallback(async (marker: PhotoMarker) => {
    setIsLoading(true);
    
    try {
      // Fetch full photo details
      const response = await fetch(`/api/v1/photos/${marker.photo_id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to load photo');
      }
      
      const photoData = await response.json();
      
      // Build photo metadata
      const photo: PhotoMetadata = {
        id: photoData.id,
        filename: photoData.filename,
        width: photoData.exif?.width || 1920,
        height: photoData.exif?.height || 1080,
        megapixels: photoData.exif?.megapixels || 0,
        originalUrl: `/api/v1/photos/${marker.photo_id}/download`,
        position: marker.position,
        rotation: marker.rotation,
      };
      
      setSelectedPhoto(photo);
      
      // Sync 3D camera to photo position
      if (onCameraSync) {
        onCameraSync(marker.position, marker.rotation);
      }
    } catch (error) {
      console.error('Failed to load photo:', error);
      alert('Failed to load photo');
    } finally {
      setIsLoading(false);
    }
  }, [onCameraSync]);
  
  // Handle photo viewer close
  const handleCloseViewer = useCallback(() => {
    setSelectedPhoto(null);
  }, []);
  
  // Handle position click in photo
  const handlePhotoPositionClick = useCallback((normalizedX: number, normalizedY: number) => {
    if (!selectedPhoto || !onPositionHighlight) return;
    
    // Convert normalized photo coordinates to 3D position
    // This is a simplified approach - in production, this would use
    // camera projection matrices and depth information
    
    const photoPos = selectedPhoto.position;
    
    // Estimate 3D position based on photo click
    // For now, just highlight the photo's capture position
    // In a full implementation, this would raycast into the scene
    onPositionHighlight(photoPos);
  }, [selectedPhoto, onPositionHighlight]);
  
  return (
    <>
      {/* Photo Markers List */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-sm max-h-96 overflow-y-auto">
        <h3 className="text-lg font-semibold mb-3">Photos ({markers.length})</h3>
        
        {markers.length === 0 && (
          <p className="text-gray-500 text-sm">No photos attached to this scene</p>
        )}
        
        <div className="space-y-2">
          {markers.map((marker) => (
            <button
              key={marker.photo_id}
              onClick={() => handleMarkerClick(marker)}
              className="w-full flex items-center space-x-3 p-2 hover:bg-gray-100 rounded transition"
            >
              {marker.thumbnail_url && (
                <img
                  src={marker.thumbnail_url}
                  alt={marker.filename}
                  className="w-16 h-16 object-cover rounded"
                />
              )}
              <div className="flex-1 text-left">
                <p className="text-sm font-medium truncate">{marker.filename}</p>
                <p className="text-xs text-gray-500">
                  {marker.megapixels.toFixed(1)} MP
                </p>
                {marker.capture_datetime && (
                  <p className="text-xs text-gray-400">
                    {new Date(marker.capture_datetime).toLocaleDateString()}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
      
      {/* Loading Indicator */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 z-40">
          <div className="bg-white rounded-lg p-6">
            <p className="text-lg">Loading photo...</p>
          </div>
        </div>
      )}
      
      {/* Gigapixel Viewer */}
      {selectedPhoto && (
        <GigapixelViewer
          photo={selectedPhoto}
          onClose={handleCloseViewer}
          onPositionClick={handlePhotoPositionClick}
        />
      )}
    </>
  );
};

export default PhotoInspector;
