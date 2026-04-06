import React from 'react';
import { Card } from '../common/Card';
import { StatusBadge } from '../common/StatusBadge';
import SceneProgressIndicator from '../SceneProgressIndicator';
import { useGetSceneJobsQuery } from '../../store/api/sceneApi';
import type { SceneMetadata } from '../../types/scene.types';

export interface SceneCardProps {
  scene: SceneMetadata;
  onClick: () => void;
  onDelete?: () => void;
  onEdit?: () => void;
  onShare?: () => void;
}

/**
 * SceneCard component - displays individual scene with thumbnail and metadata
 * 
 * Features:
 * - Scene thumbnail with fallback
 * - Status badge
 * - Scene name and metadata
 * - Action buttons (view, delete)
 * - Hover effects
 * 
 * Requirements: 4.2, 4.8
 */
export const SceneCard: React.FC<SceneCardProps> = ({
  scene,
  onClick,
  onDelete,
  onEdit,
  onShare,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const isViewable = scene.status === 'ready' || scene.status === 'completed';
  const isProcessing = [
    'uploaded',
    'uploading',
    'processing',
    'extracting_frames',
    'estimating_poses',
    'generating_depth',
    'reconstructing',
    'tiling',
    'queued_reconstruction',
    'queued_tiling',
  ].includes(scene.status);
  const isFailed = scene.status === 'failed';

  const { data: jobs = [] } = useGetSceneJobsQuery(scene.sceneId, {
    pollingInterval: isProcessing ? 5000 : 0,
    skip: !isProcessing,
  });
  const latestJob = jobs?.[0];
  const jobStatus: string | undefined = latestJob?.status;
  const progressPercent: number | undefined = latestJob?.progress_percent;
  const currentStep: string | undefined = latestJob?.current_step;

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete();
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit();
    }
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onShare) {
      onShare();
    }
  };

  return (
    <Card 
      onClick={onClick} 
      className={`overflow-hidden group ${!isViewable ? 'cursor-default' : ''}`}
    >
      {/* Thumbnail */}
      <div className="relative h-48 bg-hover-bg overflow-hidden">
        {/* Placeholder for thumbnail - will be replaced with actual thumbnail URL */}
        <div className="absolute inset-0 flex items-center justify-center">
          <svg
            className="h-16 w-16 text-text-muted"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        
        {/* Delete icon overlay - top left */}
        {onDelete && (
          <button
            onClick={handleDelete}
            className="absolute top-3 left-3 p-2 bg-red-500/80 hover:bg-red-600 text-white rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100 z-10"
            title="Delete scene"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        )}
        
        {/* Status badge overlay */}
        <div className="absolute top-3 right-3">
          {isProcessing ? (
            <SceneProgressIndicator
              status={jobStatus || scene.status}
              progressPercent={progressPercent}
              currentStep={currentStep}
            />
          ) : (
            <StatusBadge status={scene.status} />
          )}
        </div>

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-300 flex items-center justify-center">
          <span className="text-white font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            {isViewable ? 'View Scene' : isProcessing ? 'Processing...' : 'Failed'}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="text-lg font-semibold text-text-primary mb-2 truncate">
          {scene.name}
        </h3>
        
        <div className="space-y-1 text-sm text-text-secondary mb-4">
          <div className="flex items-center">
            <svg
              className="h-4 w-4 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span>{formatDate(scene.createdAt)}</span>
          </div>
          
          <div className="flex items-center">
            <svg
              className="h-4 w-4 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
              />
            </svg>
            <span className="capitalize">{scene.sourceType}</span>
          </div>

          {scene.gaussianCount && (
            <div className="flex items-center">
              <svg
                className="h-4 w-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <span>{(scene.gaussianCount / 1000000).toFixed(1)}M gaussians</span>
            </div>
          )}
        </div>

        {/* Actions */}
        {(onEdit || onDelete || onShare) && (
          <div className="flex gap-2 pt-3 border-t border-border-color">
            {onShare && (
              <button
                onClick={handleShare}
                className="flex-1 px-3 py-2 text-sm text-text-secondary hover:text-accent-primary hover:bg-accent-primary/10 rounded-lg transition-colors duration-200 flex items-center justify-center gap-1"
                title="Share scene"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
                Share
              </button>
            )}
            {onEdit && (
              <button
                onClick={handleEdit}
                className="flex-1 px-3 py-2 text-sm text-accent-primary hover:text-accent-secondary hover:bg-accent-primary/10 rounded-lg transition-colors duration-200"
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={handleDelete}
                className="flex-1 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition-colors duration-200"
              >
                Delete
              </button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
