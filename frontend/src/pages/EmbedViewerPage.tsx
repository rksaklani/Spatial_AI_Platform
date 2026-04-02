/**
 * Embed Viewer Page
 * 
 * Minimal 3D viewer for iframe embedding
 * Supports query parameters for customization
 */

import { useParams, useSearchParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { GaussianViewer } from '../components/GaussianViewer';
import { ViewerToolbar } from '../components/viewer/ViewerToolbar';

export function EmbedViewerPage() {
  const { id: sceneId } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  
  // Parse query parameters
  const showControls = searchParams.get('controls') !== 'false';
  const showAnnotations = searchParams.get('annotations') !== 'false';
  const showMeasurements = searchParams.get('measurements') !== 'false';
  const autoRotate = searchParams.get('autoRotate') === 'true';
  
  const [renderingMode, setRenderingMode] = useState<'client' | 'server'>('client');
  const [showFps, setShowFps] = useState(false);
  const [showCoordinates, setShowCoordinates] = useState(false);
  const [fps, setFps] = useState(0);

  if (!sceneId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-primary-bg">
        <p className="text-text-secondary">Invalid scene ID</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-screen bg-primary-bg overflow-hidden">
      {/* 3D Viewer */}
      <GaussianViewer
        sceneId={sceneId}
        onFpsUpdate={setFps}
        onError={(error) => console.error('Viewer error:', error)}
      />

      {/* Toolbar (if controls enabled) */}
      {showControls && (
        <ViewerToolbar
          renderingMode={renderingMode}
          onRenderingModeToggle={() => setRenderingMode(prev => prev === 'client' ? 'server' : 'client')}
          fps={fps}
          showFps={showFps}
          onToggleFps={() => setShowFps(!showFps)}
          showCoordinates={showCoordinates}
          onToggleCoordinates={() => setShowCoordinates(!showCoordinates)}
        />
      )}

      {/* Watermark */}
      <div className="absolute bottom-4 right-4 text-xs text-text-muted opacity-50">
        Powered by Spatial AI
      </div>
    </div>
  );
}
