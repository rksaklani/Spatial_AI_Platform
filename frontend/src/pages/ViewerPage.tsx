import { useParams } from 'react-router-dom';
import { useState, useCallback, useRef, useEffect } from 'react';
import * as THREE from 'three';
import { GaussianViewer } from '../components/GaussianViewer';
import { ModelViewer } from '../components/ModelViewer';
import { AnnotationPreview } from '../components/viewer';
import { CollaborationOverlay } from '../components/CollaborationOverlay';
import { ShareDialog } from '../components/sharing/ShareDialog';
import { TrainingProgressDisplay } from '../components/TrainingProgressDisplay';
import { useAnnotationCreation } from '../hooks/useAnnotationCreation';
import { useCollaboration } from '../hooks/useCollaboration';
import { useSceneProgress } from '../hooks/useSceneProgress';
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
  const { id: sceneId } = useParams<{ id: string }>();
  const [renderingMode, setRenderingMode] = useState<'client' | 'server'>('client');
  const [showFps, setShowFps] = useState(true);
  const [showCoordinates, setShowCoordinates] = useState(false);
  const [fps, setFps] = useState(0);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  
  // Fetch scene data
  const { data: scene } = useGetSceneByIdQuery(sceneId || '', { skip: !sceneId });
  const token = useAppSelector(state => state.auth.token);
  
  // Progress tracking for processing scenes
  const {
    progressPercent,
    currentIteration,
    totalIterations,
    statusMessage,
    estimatedSecondsRemaining,
    isLoading: progressLoading,
    error: progressError,
    isComplete: progressComplete,
    isFailed: progressFailed,
  } = useSceneProgress({
    sceneId: sceneId || '',
    token: token || '',
    enabled: scene?.status === 'processing' || scene?.status === 'reconstructing',
    pollingInterval: 5000,
    enableWebSocket: true,
  });
  
  // Annotation state
  const [annotationMode, setAnnotationMode] = useState<AnnotationMode>('view');
  const [selectedAnnotationType, setSelectedAnnotationType] = useState<AnnotationType | null>(null);
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<string | null>(null);
  const [annotationColor, setAnnotationColor] = useState<string>('#FF6B6B');
  
  // Refs to access viewer internals
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.Camera | null>(null);
  const controlsRef = useRef<any | null>(null);
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

  // Connect WebSocket on mount (non-blocking - collaboration is optional)
  useEffect(() => {
    if (sceneId && token) {
      try {
        websocketService.connect(sceneId, token);
      } catch (error) {
        console.warn('WebSocket connection failed (collaboration disabled):', error);
      }
      
      return () => {
        try {
          websocketService.disconnect();
        } catch (error) {
          console.warn('WebSocket disconnect error:', error);
        }
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
    if (cameraRef.current && sceneRef.current) {
      // Reset camera to default position
      cameraRef.current.position.set(0, 5, 10);
      cameraRef.current.lookAt(0, 0, 0);
      
      // Update controls target if available
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    }
  }, []);

  const handleFitToView = useCallback(() => {
    if (cameraRef.current && sceneRef.current) {
      // Calculate bounding box of scene
      const box = new THREE.Box3().setFromObject(sceneRef.current);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      
      // Calculate camera distance to fit scene
      const maxDim = Math.max(size.x, size.y, size.z);
      const fov = (cameraRef.current as THREE.PerspectiveCamera).fov * (Math.PI / 180);
      let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
      cameraZ *= 1.5; // Add some padding
      
      cameraRef.current.position.set(center.x, center.y, center.z + cameraZ);
      cameraRef.current.lookAt(center);
      
      // Update controls target if available
      if (controlsRef.current) {
        controlsRef.current.target.copy(center);
        controlsRef.current.update();
      }
    }
  }, []);

  const handlePresetView = useCallback((view: 'top' | 'front' | 'side' | 'isometric') => {
    if (cameraRef.current && sceneRef.current) {
      // Calculate bounding box to get proper distance
      const box = new THREE.Box3().setFromObject(sceneRef.current);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const distance = maxDim * 2; // Distance based on scene size
      
      switch (view) {
        case 'top':
          cameraRef.current.position.set(center.x, center.y + distance, center.z);
          break;
        case 'front':
          cameraRef.current.position.set(center.x, center.y, center.z + distance);
          break;
        case 'side':
          cameraRef.current.position.set(center.x + distance, center.y, center.z);
          break;
        case 'isometric':
          cameraRef.current.position.set(
            center.x + distance * 0.7,
            center.y + distance * 0.7,
            center.z + distance * 0.7
          );
          break;
      }
      
      cameraRef.current.lookAt(center);
      
      // Update controls target if available
      if (controlsRef.current) {
        controlsRef.current.target.copy(center);
        controlsRef.current.update();
      }
    }
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
  const handleSceneReady = useCallback((scene: THREE.Scene, camera: THREE.Camera, domElement: HTMLElement, controls?: any) => {
    sceneRef.current = scene;
    cameraRef.current = camera;
    domElementRef.current = domElement;
    controlsRef.current = controls;
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

  // Check if scene is still processing
  if (scene && scene.status === 'processing') {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-primary-bg p-8">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-text-primary mb-2">Processing Video</h2>
            <p className="text-text-secondary mb-4">Your video is being converted to 3D. This may take 20-60 minutes.</p>
            <p className="text-text-muted text-sm">You can close this page and come back later.</p>
          </div>
          
          {/* Real-time progress display */}
          <TrainingProgressDisplay
            progressPercent={progressPercent}
            currentIteration={currentIteration}
            totalIterations={totalIterations}
            statusMessage={statusMessage}
            estimatedSecondsRemaining={estimatedSecondsRemaining}
            state={progressFailed ? 'failed' : progressComplete ? 'complete' : 'in-progress'}
          />
          
          {progressError && (
            <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
              <p className="text-sm text-red-300">{progressError}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Check if scene processing failed
  if (scene && scene.status === 'failed') {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-primary-bg">
        <div className="text-center max-w-md">
          <div className="mb-4">
            <svg className="h-12 w-12 text-red-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">Processing Failed</h2>
          <p className="text-text-secondary mb-4">There was an error processing your video. Please try uploading again.</p>
          <button
            onClick={() => window.location.href = '/app/scenes'}
            className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors"
          >
            Back to Scenes
          </button>
        </div>
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
      {(() => {
        // Determine format
        // For imported models, use sourceFormat
        // For videos, default to 'splat' since they're converted to Gaussian splats
        let format = scene?.sourceFormat || scene?.format || (scene?.sourceType === 'video' ? 'splat' : undefined);
        
        // Remove leading dot if present
        if (format && format.startsWith('.')) {
          format = format.substring(1);
        }
        
        const isImportedModel = scene?.sourceType === 'import';
        const isModelFormat = format && ['glb', 'gltf', 'obj', 'ply', 'stl', 'fbx', 'dae'].includes(format.toLowerCase());
        const isPointCloud = format && ['las', 'laz', 'e57'].includes(format.toLowerCase());
        const isBIM = format && ['ifc'].includes(format.toLowerCase());
        const isSplat = format && ['splat'].includes(format.toLowerCase());
        const isVideoScene = scene?.sourceType === 'video';
        
        console.log('Scene format:', format, 'isModelFormat:', isModelFormat, 'sourceType:', scene?.sourceType, 'isImportedModel:', isImportedModel);
        
        // Use ModelViewer for direct 3D models (GLB, GLTF, OBJ, PLY, STL, FBX, DAE)
        // Use GaussianViewer for point clouds (LAS, LAZ, E57), BIM (IFC), and Gaussian Splats
        return (isModelFormat && !isPointCloud && !isBIM && !isSplat) ? (
          <>
            {console.log('Rendering ModelViewer for format:', format, 'URL:', scene?.fileUrl, 'Scene:', scene)}
            <ModelViewer
              sceneId={sceneId}
              token={token}
              modelUrl={scene?.fileUrl || `/api/v1/scenes/${sceneId}/download`}
              modelType={(format?.toLowerCase() || 'glb') as 'glb' | 'gltf' | 'obj' | 'ply' | 'stl' | 'fbx' | 'dae' | 'splat' | 'las' | 'laz' | 'e57' | 'ifc'}
              onError={(error) => console.error('Viewer error:', error)}
              onLoadProgress={(progress) => console.log('Load progress:', progress)}
              onSceneReady={handleSceneReady}
              annotationMode={annotationMode}
              selectedAnnotationType={selectedAnnotationType}
              annotationColor={annotationColor}
              onAnnotationModeChange={handleAnnotationModeChange}
              onAnnotationTypeSelect={handleAnnotationTypeSelect}
              onAnnotationColorChange={handleAnnotationColorChange}
              connectionStatus={connectionStatus}
              activeUsers={activeUsers}
            />
          </>
        ) : (
          <>
            {console.log('Rendering GaussianViewer for format:', format)}
            <GaussianViewer 
              sceneId={sceneId}
              token={token}
              onError={(error) => console.error('Viewer error:', error)}
              onLoadProgress={(progress) => console.log('Load progress:', progress)}
              onFpsUpdate={handleFpsUpdate}
              enableBIMVisualization={isBIM}
              enable2DOverlays={!isVideoScene}
              enableAnimations={true}
              onSceneReady={handleSceneReady}
              onCanvasClick={handleAnnotationClick}
              onCanvasDoubleClick={handleAnnotationDoubleClick}
              onCanvasMouseMove={handleAnnotationMouseMove}
              onCameraMove={handleCameraMove}
            />
          </>
        );
      })()}
      
      {/* Collaboration overlay showing other users' cursors */}
      <CollaborationOverlay
        users={activeUsers}
        scene={sceneRef.current}
        camera={cameraRef.current}
      />
      
      {/* Annotation preview for multi-point annotations */}
      <AnnotationPreview
        scene={sceneRef.current}
        points={points}
        previewPoints={previewPoints}
        type={selectedAnnotationType === 'line' || selectedAnnotationType === 'area' ? selectedAnnotationType : null}
        color={annotationColor}
      />

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
