/**
 * PublicSceneViewerPage Component
 * 
 * Public scene viewer without authentication
 * Requirements: 15.3
 */

import { useParams, useSearchParams } from 'react-router-dom';
import { GaussianViewer } from '../components/GaussianViewer';
import { ViewerToolbar } from '../components/viewer';
import { useGetPublicSceneQuery } from '../store/api/sharingApi';
import { LoadingSpinner } from '../components/common';
import { useState, useCallback } from 'react';

export function PublicSceneViewerPage() {
  const { sceneId } = useParams<{ sceneId: string }>();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [showFps, setShowFps] = useState(false);
  const [showCoordinates, setShowCoordinates] = useState(false);
  const [fps, setFps] = useState(0);
  const [cameraPosition, setCameraPosition] = useState<[number, number, number]>([5, 5, 5]);

  const { data: scene, isLoading, error } = useGetPublicSceneQuery(
    { sceneId: sceneId!, token: token! },
    { skip: !sceneId || !token }
  );

  const handleResetCamera = useCallback(() => {
    console.log('Reset camera');
  }, []);

  const handleFitToView = useCallback(() => {
    console.log('Fit to view');
  }, []);

  const handlePresetView = useCallback((view: 'top' | 'front' | 'side' | 'isometric') => {
    console.log('Preset view:', view);
  }, []);

  const handleToggleFps = useCallback(() => {
    setShowFps(prev => !prev);
  }, []);

  const handleToggleCoordinates = useCallback(() => {
    setShowCoordinates(prev => !prev);
  }, []);

  const handleFpsUpdate = useCallback((newFps: number) => {
    setFps(newFps);
  }, []);

  if (!sceneId || !token) {
    return (
      <div className="flex items-center justify-center h-screen bg-primary-bg">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-text-primary mb-2">Invalid Link</h1>
          <p className="text-text-secondary">This share link is invalid or incomplete</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-primary-bg">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-text-primary mb-2">Access Denied</h1>
          <p className="text-text-secondary">
            This scene is not available or the share link has expired
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen relative">
      {/* Shared By Banner */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
        <div className="bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg px-4 py-2 shadow-lg">
          <p className="text-sm text-text-secondary">
            Shared by <span className="text-text-primary font-medium">{scene?.name || 'Unknown'}</span>
          </p>
        </div>
      </div>

      <GaussianViewer 
        sceneId={sceneId}
        onError={(error) => console.error('Viewer error:', error)}
        onLoadProgress={(progress) => console.log('Load progress:', progress)}
        onFpsUpdate={handleFpsUpdate}
        enableBIMVisualization={false}
        enable2DOverlays={false}
        enableAnimations={true}
      />
      
      <ViewerToolbar
        onResetCamera={handleResetCamera}
        onFitToView={handleFitToView}
        onPresetView={handlePresetView}
        renderingMode="client"
        onRenderingModeToggle={() => {}}
        fps={fps}
        showFps={showFps}
        onToggleFps={handleToggleFps}
        showCoordinates={showCoordinates}
        onToggleCoordinates={handleToggleCoordinates}
        cameraPosition={cameraPosition}
        onOpenSettings={() => {}}
      />
    </div>
  );
}
