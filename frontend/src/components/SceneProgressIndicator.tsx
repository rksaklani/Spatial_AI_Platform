/**
 * SceneProgressIndicator Component
 * 
 * Compact progress indicator for scene list view.
 * Shows progress bar, percentage, and status badge.
 */

import React from 'react';

interface SceneProgressIndicatorProps {
  /** Scene status */
  status: string;
  /** Progress percentage (0-100) */
  progressPercent?: number;
  /** Current processing step */
  currentStep?: string;
}

export const SceneProgressIndicator: React.FC<SceneProgressIndicatorProps> = ({
  status,
  progressPercent = 0,
  currentStep,
}) => {
  // Determine badge color and text based on status
  const getBadgeInfo = () => {
    switch (status) {
      case 'completed':
      case 'ready':
        return {
          color: 'bg-green-100 text-green-800',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Ready',
        };
      
      case 'failed':
        return {
          color: 'bg-red-100 text-red-800',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Failed',
        };
      
      case 'processing':
      case 'running':
      case 'reconstructing':
      case 'training':
        return {
          color: 'bg-blue-100 text-blue-800',
          icon: (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ),
          text: getStepLabel(currentStep),
        };
      
      case 'uploaded':
      case 'queued':
        return {
          color: 'bg-yellow-100 text-yellow-800',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Queued',
        };
      
      default:
        return {
          color: 'bg-gray-100 text-gray-800',
          icon: null,
          text: status,
        };
    }
  };
  
  const badgeInfo = getBadgeInfo();
  const showProgress = ['processing', 'running', 'reconstructing', 'training'].includes(status);
  
  return (
    <div className="space-y-2">
      {/* Status badge */}
      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeInfo.color}`}>
        {badgeInfo.icon && <span className="mr-1">{badgeInfo.icon}</span>}
        {badgeInfo.text}
      </div>
      
      {/* Progress bar (only for processing states) */}
      {showProgress && (
        <div className="w-full">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>{progressPercent.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Get human-readable label for processing step.
 */
function getStepLabel(step?: string): string {
  if (!step) return 'Processing';
  
  const labels: Record<string, string> = {
    'extracting_frames': 'Extracting Frames',
    'estimating_poses': 'Estimating Poses',
    'estimating_depth': 'Estimating Depth',
    'training': 'Training',
    'reconstructing': 'Reconstructing',
    'tiling': 'Tiling',
    'optimizing': 'Optimizing',
  };
  
  return labels[step] || step.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

export default SceneProgressIndicator;
