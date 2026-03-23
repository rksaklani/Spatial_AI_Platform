import { useParams } from 'react-router-dom';
import { GaussianViewer } from '../components/GaussianViewer';

/**
 * Scene viewer page component - displays 3D scene with controls
 * 
 * Requirements: 5.1, 5.8, 5.9
 */
export function ViewerPage() {
  const { sceneId } = useParams<{ sceneId: string }>();

  if (!sceneId) {
    return (
      <div className="flex items-center justify-center h-screen bg-primary-bg">
        <div className="text-text-primary text-xl">Scene ID not provided</div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen">
      <GaussianViewer 
        sceneId={sceneId}
        onError={(error) => console.error('Viewer error:', error)}
        onLoadProgress={(progress) => console.log('Load progress:', progress)}
        onFpsUpdate={(fps) => console.log('FPS:', fps)}
        enableBIMVisualization={true}
        enable2DOverlays={true}
        enableAnimations={true}
      />
    </div>
  );
}
