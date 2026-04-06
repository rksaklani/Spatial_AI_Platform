/**
 * ProgressBar Component
 * 
 * Visual progress bar with percentage display for training progress.
 * Supports different states (in-progress, complete, failed) with color coding.
 */

import React from 'react';

interface ProgressBarProps {
  /** Progress percentage (0-100) */
  progress: number;
  /** Progress state */
  state?: 'in-progress' | 'complete' | 'failed';
  /** Custom height in pixels */
  height?: number;
  /** Show percentage text */
  showPercentage?: boolean;
  /** Custom className */
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  state = 'in-progress',
  height = 24,
  showPercentage = true,
  className = '',
}) => {
  // Clamp progress between 0 and 100
  const clampedProgress = Math.min(100, Math.max(0, progress));
  
  // Determine color based on state
  const getBarColor = () => {
    switch (state) {
      case 'complete':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'in-progress':
      default:
        return 'bg-blue-500';
    }
  };
  
  const getBackgroundColor = () => {
    switch (state) {
      case 'complete':
        return 'bg-green-100';
      case 'failed':
        return 'bg-red-100';
      case 'in-progress':
      default:
        return 'bg-gray-200';
    }
  };
  
  return (
    <div className={`w-full ${className}`}>
      <div
        className={`relative ${getBackgroundColor()} rounded-full overflow-hidden`}
        style={{ height: `${height}px` }}
      >
        {/* Progress fill */}
        <div
          className={`${getBarColor()} h-full transition-all duration-300 ease-out`}
          style={{ width: `${clampedProgress}%` }}
        />
        
        {/* Percentage text */}
        {showPercentage && (
          <div
            className="absolute inset-0 flex items-center justify-center text-sm font-medium text-gray-700"
            style={{ textShadow: '0 0 2px white' }}
          >
            {clampedProgress.toFixed(1)}%
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressBar;
