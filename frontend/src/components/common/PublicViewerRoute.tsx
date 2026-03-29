import { useParams, Navigate } from 'react-router-dom';
import { useGetSceneByShareTokenQuery } from '../../store/api/sharingApi';
import { GaussianViewer } from '../GaussianViewer';
import { LoadingSpinner } from './LoadingSpinner';

/**
 * PublicViewerRoute - Public scene viewer accessible via share token
 * No authentication required
 */
export function PublicViewerRoute() {
  const { token } = useParams<{ token: string }>();
  const { data: scene, isLoading, error } = useGetSceneByShareTokenQuery(token || '', {
    skip: !token,
  });

  if (!token) {
    return <Navigate to="/" replace />;
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-primary-bg">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-text-secondary mt-4">Loading shared scene...</p>
        </div>
      </div>
    );
  }

  if (error || !scene) {
    return (
      <div className="flex items-center justify-center h-screen bg-primary-bg">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">
            Invalid or Expired Link
          </h2>
          <p className="text-text-secondary">
            This share link is invalid or has expired. Please contact the person who shared it with you.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen relative">
      {/* Watermark */}
      <div className="absolute top-4 left-4 z-20 bg-black/50 backdrop-blur-sm rounded-lg px-4 py-2">
        <p className="text-white text-sm font-medium">{scene.name}</p>
        <p className="text-white/70 text-xs">Shared via Spatial AI Platform</p>
      </div>

      <GaussianViewer
        sceneId={scene.sceneId}
        onError={(error) => console.error('Viewer error:', error)}
        onLoadProgress={(progress) => console.log('Load progress:', progress)}
      />
    </div>
  );
}
