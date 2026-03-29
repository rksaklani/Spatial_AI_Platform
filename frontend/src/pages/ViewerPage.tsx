import { useParams } from 'react-router-dom';
import { useState, useCallback, useRef, useEffect } from 'react';
import * as THREE from 'three';
import { GaussianViewer } from '../components/GaussianViewer';
import { ModelViewer } from '../components/ModelViewer';
import { ViewerToolbar, AnnotationToolbar, AnnotationPreview } from '../components/viewer';
import { CollaborationOverlay } from '../components/CollaborationOverlay';
import { CollaborationPanel } from '../components/collaboration/CollaborationPanel';
import { ShareDialog } from '../components/sharing/ShareDialog';
import { useAnnotationCreation } from '../hooks/useAnnotationCreation';
import { useCollaboration } from '../hooks/useCollaboration';
import { websocketService } from '../services/websocket.service';
import { useAppSelector } from '../store/hooks';
import { useGetSceneByIdQuery } from '../store/api/sceneApi';
import { ShareIcon } from '@heroicons/react/24/outline';
import type { AnnotationType, AnnotationMode } from '../hooks/useAnnotationCreation';

/**
 * Scene viewer page component - displays 3D scene with controls
 * 
 * Requirements: 5.1, 5.8, 5.9, F5
 */
export function ViewerPage() {
  const { sceneId } = useParams<{ sceneId: string }>();
  const [renderingMode, setRenderingMode] = useState<'client' | 'server'>('client');
  const [showFps, setShowFps] = useState(true);
  const [showCoordinates, setShowCoordinates] = useState(false);
  const [fps, setFps] = useState(0);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  
  // Fetch scene data
  const { data: scene } = useGetSceneByIdQuery(sceneId || '', { skip: !sceneId });
  const token = useAppSelector(state => state.auth.token);
  
  // Annotation state
  const [annotationMode, setAnnotationMode] = useState<AnnotationMode>('view');
  const [selectedAnnotationType, setSelectedAnnotationType] = useState<AnnotationType | null>(null);
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<string | null>(null);
  const [annotationColor, setAnnotationColor] = useState<string>('#FF6B6B');
  
  // Collaboration panel state
  const [showCollaborationPanel, setShowCollaborationPanel] = useState(true);
  
  // Refs to access viewer internals
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.Camera | null>(null);
  const domElementRef = useRef<HTMLElement | null>(null);

  // Collaboration hook
  const {
    connectionStatus,
    activeUsers,
    sendCursorPosition,
    broadcastAnnotationCreated,
  } = useCollaboration({
    sceneId: sceneId || '',
    enabled: true,
    onAnnotationCreated: (annotation) => {
      console.log('Remote annotation created:', annotation);
      // The annotation will be automatically fetched via RTK Query cache invalidation
    },
    onAnnotationUpdated: (annotationId, changes) => {
      console.log('Remote annotation updated:', annotationId, changes);
    },
    onAnnotationDeleted: (annotationId) => {
      console.log('Remote annotation deleted:', annotationId);
    },
  });

  // Connect WebSocket on mount
  useEffect(() => {
    if (sceneId && token) {
      websocketService.connect(sceneId, token);
      
      return () => {
        websocketService.disconnect();
      };
    }
  }, [sceneId, token]);

  // Annotation creation hook
  const {
    points,
    previewPoints,
    handleClick: handleAnnotationClick,
    handleDoubleClick: handleAnnotationDoubleClick,
    handleMouseMove: handleAnnotationMouseMove,
    cancelCreation,
    cleanup: cleanupAnnotations,
  } = useAnnotationCreation({
    sceneId: sceneId || '',
    scene: sceneRef.current,
    camera: cameraRef.current,
    mode: annotationMode,
    selectedType: selectedAnnotationType,
    color: annotationColor,
    onAnnotationCreated: () => {
      // Reset to view mode after creating annotation
      setAnnotationMode('view');
      setSelectedAnnotationType(null);
      
      // Broadcast to other users (annotation will be sent via API, this is just for real-time notification)
      // The actual annotation data will be synced via the backend WebSocket
    },
  });

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupAnnotations();
    };
  }, [cleanupAnnotations]);

  // Camera control handlers
  const handleResetCamera = useCallback(() => {
    // This would call a method on the GaussianViewer to reset camera
    console.log('Reset camera');
    // viewerRef.current?.resetCamera();
  }, []);

  const handleFitToView = useCallback(() => {
    // This would call a method on the GaussianViewer to fit scene to view
    console.log('Fit to view');
    // viewerRef.current?.fitToView();
  }, []);

  const handlePresetView = useCallback((view: 'top' | 'front' | 'side' | 'isometric') => {
    // This would call a method on the GaussianViewer to set preset view
    console.log('Preset view:', view);
    // viewerRef.current?.setPresetView(view);
  }, []);

  // Rendering mode toggle
  const handleRenderingModeToggle = useCallback(() => {
    setRenderingMode(prev => prev === 'client' ? 'server' : 'client');
  }, []);

  // FPS counter toggle
  const handleToggleFps = useCallback(() => {
    setShowFps(prev => !prev);
  }, []);

  // Coordinate display toggle
  const handleToggleCoordinates = useCallback(() => {
    setShowCoordinates(prev => !prev);
  }, []);

  // Settings handler
  const handleOpenSettings = useCallback(() => {
    console.log('Open settings');
    // This would open a settings modal/panel
  }, []);

  // FPS update handler
  const handleFpsUpdate = useCallback((newFps: number) => {
    setFps(newFps);
  }, []);

  // Annotation handlers
  const handleAnnotationModeChange = useCallback((mode: AnnotationMode) => {
    setAnnotationMode(mode);
    if (mode === 'view') {
      setSelectedAnnotationType(null);
      cancelCreation(); // Cancel any in-progress annotation
    }
  }, [cancelCreation]);

  const handleAnnotationTypeSelect = useCallback((type: AnnotationType) => {
    setSelectedAnnotationType(type);
    setAnnotationMode('create');
  }, []);

  const handleAnnotationEdit = useCallback(() => {
    if (selectedAnnotationId) {
      setAnnotationMode('edit');
      console.log('Edit annotation:', selectedAnnotationId);
      // This would trigger edit mode in the viewer
    }
  }, [selectedAnnotationId]);

  const handleAnnotationDelete = useCallback(() => {
    if (selectedAnnotationId) {
      console.log('Delete annotation:', selectedAnnotationId);
      // This would call the delete annotation API
      setSelectedAnnotationId(null);
    }
  }, [selectedAnnotationId]);

  const handleAnnotationColorChange = useCallback((color: string) => {
    setAnnotationColor(color);
  }, []);

  // Handle scene ready callback
  const handleSceneReady = useCallback((scene: THREE.Scene, camera: THREE.Camera, domElement: HTMLElement) => {
    sceneRef.current = scene;
    cameraRef.current = camera;
    domElementRef.current = domElement;
  }, []);

  // Handle camera movement for cursor broadcasting
  const handleCameraMove = useCallback((cameraPosition: [number, number, number]) => {
    // Send cursor position to other users
    // For now, we'll use camera position as cursor position
    sendCursorPosition(cameraPosition, cameraPosition);
  }, [sendCursorPosition]);

  if (!sceneId) {
    return (
      <div className="flex items-center justify-center h-screen bg-primary-bg">
        <div className="text-text-primary text-xl">Scene ID not provided</div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen relative">
      {/* Share Button - Fixed Position */}
      <button
        onClick={() => setShareDialogOpen(true)}
        className="absolute top-4 right-4 z-20 bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg px-4 py-2 shadow-lg hover:bg-surface-elevated transition-colors flex items-center gap-2"
        title="Share scene"
      >
        <ShareIcon className="w-5 h-5 text-text-primary" />
        <span className="text-sm font-medium text-text-primary">Share</span>
      </button>

      {/* Render appropriate viewer based on file type */}
      {scene && (scene.format === 'glb' || scene.format === 'gltf' || scene.format === 'obj' || scene.format === 'ply') ? (
        <ModelViewer
          sceneId={sceneId}
          modelUrl={scene.fileUrl || `/api/v1/scenes/${sceneId}/download`}
          modelType={scene.format as 'glb' | 'gltf' | 'obj' | 'ply' | 'splat'}
          onError={(error) => console.error('Viewer error:', error)}
          onLoadProgress={(progress) => console.log('Load progress:', progress)}
        />
      ) : (
        <GaussianViewer 
          sceneId={sceneId}
          onError={(error) => console.error('Viewer error:', error)}
          onLoadProgress={(progress) => console.log('Load progress:', progress)}
          onFpsUpdate={handleFpsUpdate}
          enableBIMVisualization={true}
          enable2DOverlays={true}
          enableAnimations={true}
          onSceneReady={handleSceneReady}
          onCanvasClick={handleAnnotationClick}
          onCanvasDoubleClick={handleAnnotationDoubleClick}
          onCanvasMouseMove={handleAnnotationMouseMove}
          onCameraMove={handleCameraMove}
        />
      )}
      
      {/* Collaboration overlay showing other users' cursors */}
      <CollaborationOverlay
        users={activeUsers}
        scene={sceneRef.current}
        camera={cameraRef.current}
      />
      
      <ViewerToolbar
        onResetCamera={handleResetCamera}
        onFitToView={handleFitToView}
        onPresetView={handlePresetView}
        renderingMode={renderingMode}
        onRenderingModeToggle={handleRenderingModeToggle}
        fps={fps}
        showFps={showFps}
        onToggleFps={handleToggleFps}
        showCoordinates={showCoordinates}
        onToggleCoordinates={handleToggleCoordinates}
        cameraPosition={[0, 0, 0]}
        onOpenSettings={handleOpenSettings}
      />

      <AnnotationToolbar
        mode={annotationMode}
        onModeChange={handleAnnotationModeChange}
        selectedType={selectedAnnotationType}
        onTypeSelect={handleAnnotationTypeSelect}
        selectedAnnotationId={selectedAnnotationId}
        onEdit={handleAnnotationEdit}
        onDelete={handleAnnotationDelete}
        selectedColor={annotationColor}
        onColorChange={handleAnnotationColorChange}
        pointsCollected={points.length}
      />

      {/* Annotation preview for multi-point annotations */}
      <AnnotationPreview
        scene={sceneRef.current}
        points={points}
        previewPoints={previewPoints}
        type={selectedAnnotationType === 'line' || selectedAnnotationType === 'area' ? selectedAnnotationType : null}
        color={annotationColor}
      />

      {/* Collaboration panel */}
      {showCollaborationPanel && (
        <CollaborationPanel
          users={activeUsers}
          connectionStatus={connectionStatus}
          onClose={() => setShowCollaborationPanel(false)}
        />
      )}

      {/* Toggle collaboration panel button */}
      {!showCollaborationPanel && (
        <button
          onClick={() => setShowCollaborationPanel(true)}
          className="absolute top-20 right-4 bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg p-3 shadow-lg hover:bg-surface-elevated transition-colors z-10"
          aria-label="Show collaboration panel"
          title="Show collaboration panel"
        >
          <svg className="w-5 h-5 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </button>
      )}

      {/* Share Dialog */}
      {scene && (
        <ShareDialog
          open={shareDialogOpen}
          sceneId={sceneId || ''}
          sceneName={scene.name}
          onClose={() => setShareDialogOpen(false)}
        />
      )}
    </div>
  );
}
