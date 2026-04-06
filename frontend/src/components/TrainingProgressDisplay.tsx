/**
 * TrainingProgressDisplay Component
 * 
 * Displays comprehensive training progress information including:
 * - Progress bar with percentage
 * - Current iteration count
 * - Status message
 * - Estimated time remaining
 */

import React from 'react';
import ProgressBar from './ProgressBar';

interface TrainingProgressDisplayProps {
  /** Progress percentage (0-100) */
  progressPercent: number;
  /** Current iteration number */
  currentIteration?: number;
  /** Total iteration count */
  totalIterations?: number;
  /** Current status message */
  statusMessage: string;
  /** Estimated seconds remaining */
  estimatedSecondsRemaining?: number;
  /** Progress state */
  state?: 'in-progress' | 'complete' | 'failed';
}

/**
 * Format iteration count with thousands separators.
 */
const formatIterationCount = (count: number): string => {
  return count.toLocaleString('en-US');
};

/**
 * Format time remaining in human-readable format.
 */
const formatTimeRemaining = (seconds?: number): string => {
  if (seconds === undefined || seconds === null) {
    return 'Calculating...';
  }
  
  if (seconds < 60) {
    return 'Less than 1 minute remaining';
  }
  
  const minutes = Math.floor(seconds / 60);
  
  if (minutes < 60) {
    return `~${minutes} minute${minutes !== 1 ? 's' : ''} remaining`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  if (remainingMinutes === 0) {
    return `~${hours} hour${hours !== 1 ? 's' : ''} remaining`;
  } else {
    return `~${hours} hour${hours !== 1 ? 's' : ''} ${remainingMinutes} minute${remainingMinutes !== 1 ? 's' : ''} remaining`;
  }
};

export const TrainingProgressDisplay: React.FC<TrainingProgressDisplayProps> = ({
  progressPercent,
  currentIteration,
  totalIterations,
  statusMessage,
  estimatedSecondsRemaining,
  state = 'in-progress',
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
      {/* Status message */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">
          {statusMessage}
        </h3>
        
        {/* State indicator */}
        {state === 'complete' && (
          <span className="flex items-center text-green-600">
            <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Complete
          </span>
        )}
        
        {state === 'failed' && (
          <span className="flex items-center text-red-600">
            <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            Failed
          </span>
        )}
      </div>
      
      {/* Progress bar */}
      <ProgressBar
        progress={progressPercent}
        state={state}
        height={32}
        showPercentage={true}
      />
      
      {/* Iteration count */}
      {currentIteration !== undefined && totalIterations !== undefined && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Iteration</span>
          <span className="font-mono font-medium">
            {formatIterationCount(currentIteration)} / {formatIterationCount(totalIterations)}
          </span>
        </div>
      )}
      
      {/* Time remaining */}
      {state === 'in-progress' && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Estimated time remaining</span>
          <span className="font-medium">
            {formatTimeRemaining(estimatedSecondsRemaining)}
          </span>
        </div>
      )}
      
      {/* Completion time for completed state */}
      {state === 'complete' && (
        <div className="text-center text-sm text-green-600 font-medium">
          Training completed successfully!
        </div>
      )}
    </div>
  );
};

export default TrainingProgressDisplay;
