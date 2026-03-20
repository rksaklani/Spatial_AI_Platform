/**
 * Scene Viewer component with RTK Query integration
 */

import { Scene3D } from './Scene3D';
import { useAppSelector } from '../store/hooks';
import { useGetSceneByIdQuery } from '../store/api/sceneApi';
import { toggleSidebar } from '../store/slices/uiSlice';
import { useDispatch } from 'react-redux';

interface SceneViewerProps {
  sceneId: string;
}

export function SceneViewer({ sceneId }: SceneViewerProps) {
  const dispatch = useDispatch();
  const { sidebarOpen } = useAppSelector((state) => state.ui);
  
  // Use RTK Query hook to fetch scene data
  const { data: currentScene, isLoading, error } = useGetSceneByIdQuery(sceneId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-white text-xl">Loading scene...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-red-500 text-xl">
          Error: {'status' in error ? `${error.status}` : 'Failed to load scene'}
        </div>
      </div>
    );
  }

  if (!currentScene) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-gray-400 text-xl">No scene loaded</div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-screen bg-gray-900">
      {/* Scene Info Overlay */}
      <div className="absolute top-4 left-4 z-10 bg-black bg-opacity-50 text-white p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">{currentScene.name}</h2>
        <div className="text-sm space-y-1">
          <p>Status: <span className="capitalize">{currentScene.status}</span></p>
          <p>Gaussians: {currentScene.gaussianCount.toLocaleString()}</p>
          <p>Tiles: {currentScene.tileCount}</p>
        </div>
      </div>

      {/* Sidebar Toggle */}
      <button
        className="absolute top-4 right-4 z-10 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        onClick={() => dispatch(toggleSidebar())}
      >
        {sidebarOpen ? 'Hide' : 'Show'} Sidebar
      </button>

      {/* 3D Scene */}
      <Scene3D />
    </div>
  );
}
