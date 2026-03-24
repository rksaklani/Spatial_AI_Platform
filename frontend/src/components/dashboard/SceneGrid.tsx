import React from 'react';
import { SceneCard } from './SceneCard';
import type { SceneMetadata } from '../../types/scene.types';

export interface SceneGridProps {
  scenes: SceneMetadata[];
  loading: boolean;
  onSceneClick: (sceneId: string) => void;
  onSceneDelete?: (sceneId: string) => void;
  onSceneEdit?: (sceneId: string) => void;
}

/**
 * SceneGrid component - displays scenes in a responsive grid layout
 * 
 * Features:
 * - Responsive grid (1-4 columns based on screen size)
 * - Loading skeleton state
 * - Empty state with call-to-action
 * - Scene cards with thumbnails and metadata
 * 
 * Requirements: 4.1, 4.2, 4.6, 4.7
 */
export const SceneGrid: React.FC<SceneGridProps> = ({
  scenes,
  loading,
  onSceneClick,
  onSceneDelete,
  onSceneEdit,
}) => {
  // Loading skeleton
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="bg-secondary-bg rounded-xl border border-border-color h-80 animate-pulse"
          >
            <div className="h-48 bg-hover-bg rounded-t-xl" />
            <div className="p-4 space-y-3">
              <div className="h-4 bg-hover-bg rounded w-3/4" />
              <div className="h-3 bg-hover-bg rounded w-1/2" />
              <div className="h-3 bg-hover-bg rounded w-2/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Empty state
  if (scenes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4">
        <div className="text-center max-w-md">
          <svg
            className="mx-auto h-24 w-24 text-text-muted mb-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <h3 className="text-2xl font-bold text-text-primary mb-2">
            No scenes yet
          </h3>
          <p className="text-text-secondary mb-6">
            Get started by uploading your first video or 3D file to create a scene
          </p>
        </div>
      </div>
    );
  }

  // Scene grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {scenes.map((scene) => (
        <SceneCard
          key={scene.sceneId}
          scene={scene}
          onClick={() => onSceneClick(scene.sceneId)}
          onDelete={onSceneDelete ? () => onSceneDelete(scene.sceneId) : undefined}
          onEdit={onSceneEdit ? () => onSceneEdit(scene.sceneId) : undefined}
        />
      ))}
    </div>
  );
};
