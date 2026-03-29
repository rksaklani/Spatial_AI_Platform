/**
 * PhotoInspectorPage Component
 * 
 * Full-screen photo viewer with gigapixel support and metadata
 * Requirements: 13.1, 13.8
 */

import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { GigapixelViewer } from '../components/GigapixelViewer';
import { Button } from '../components/common';

export function PhotoInspectorPage() {
  const { photoId } = useParams<{ photoId: string }>();
  const navigate = useNavigate();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showMetadata, setShowMetadata] = useState(true);

  const handleClose = () => {
    navigate(-1);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  if (!photoId) {
    return (
      <div className="flex items-center justify-center h-screen bg-primary-bg">
        <div className="text-text-primary text-xl">Photo ID not provided</div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-primary-bg relative">
      {/* Top Bar */}
      <div className="absolute top-0 left-0 right-0 z-20 bg-surface-elevated/95 backdrop-blur-sm border-b border-border-subtle">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClose}
              aria-label="Close photo inspector"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
            <h1 className="text-lg font-medium text-text-primary">Photo Inspector</h1>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowMetadata(!showMetadata)}
              aria-label="Toggle metadata panel"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleFullscreen}
              aria-label="Toggle fullscreen"
            >
              {isFullscreen ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-full pt-16">
        {/* Photo Viewer */}
        <div className={`${showMetadata ? 'flex-1' : 'w-full'} h-full`}>
          <GigapixelViewer
            photoId={photoId}
            onError={(error) => console.error('Photo viewer error:', error)}
          />
        </div>

        {/* Metadata Panel */}
        {showMetadata && (
          <div className="w-80 h-full bg-surface-elevated border-l border-border-subtle overflow-y-auto">
            <div className="p-4">
              <h2 className="text-sm font-medium text-text-primary mb-4">Photo Details</h2>
              
              {/* Placeholder for PhotoMetadataPanel */}
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-text-secondary mb-1">Photo ID</p>
                  <p className="text-sm text-text-primary font-mono">{photoId}</p>
                </div>
                
                <div className="text-xs text-text-tertiary">
                  Metadata panel coming soon...
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
