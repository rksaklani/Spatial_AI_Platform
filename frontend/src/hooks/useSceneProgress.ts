/**
 * useSceneProgress Hook
 * 
 * Comprehensive hook for tracking scene progress using both WebSocket
 * (real-time) and REST polling (fallback).
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService, ProgressResponse } from '../services/api.service';
import { useProgressWebSocket, ProgressUpdate } from './useProgressWebSocket';

interface UseSceneProgressOptions {
  /** Scene ID to track */
  sceneId: string;
  /** JWT authentication token */
  token: string;
  /** Enable progress tracking */
  enabled?: boolean;
  /** Polling interval in milliseconds (default: 5000) */
  pollingInterval?: number;
  /** Enable WebSocket connection */
  enableWebSocket?: boolean;
}

interface SceneProgressState {
  progressPercent: number;
  currentStep: string;
  statusMessage: string;
  currentIteration?: number;
  totalIterations?: number;
  estimatedSecondsRemaining?: number;
  startedAt?: string;
  elapsedSeconds?: number;
  isLoading: boolean;
  error: string | null;
  isComplete: boolean;
  isFailed: boolean;
}

export const useSceneProgress = ({
  sceneId,
  token,
  enabled = true,
  pollingInterval = 5000,
  enableWebSocket = true,
}: UseSceneProgressOptions) => {
  const [progress, setProgress] = useState<SceneProgressState>({
    progressPercent: 0,
    currentStep: 'pending',
    statusMessage: 'Initializing...',
    isLoading: true,
    error: null,
    isComplete: false,
    isFailed: false,
  });
  
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);
  
  // Fetch progress from REST API
  const fetchProgress = useCallback(async () => {
    if (!enabled || !sceneId) {
      return;
    }
    
    try {
      const response = await apiService.fetchSceneProgress(sceneId);
      
      if (!isMountedRef.current) return;
      
      setProgress(prev => ({
        ...prev,
        progressPercent: response.progress_percent,
        currentStep: response.current_step,
        statusMessage: response.status_message,
        currentIteration: response.current_iteration,
        totalIterations: response.total_iterations,
        estimatedSecondsRemaining: response.estimated_seconds_remaining,
        startedAt: response.started_at,
        elapsedSeconds: response.elapsed_seconds,
        isLoading: false,
        error: null,
        isComplete: response.progress_percent >= 100,
        isFailed: response.current_step === 'failed',
      }));
    } catch (error: any) {
      if (!isMountedRef.current) return;
      
      console.error('[useSceneProgress] Failed to fetch progress:', error);
      setProgress(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to fetch progress',
      }));
    }
  }, [sceneId, enabled]);
  
  // Handle WebSocket progress update
  const handleProgressUpdate = useCallback((update: ProgressUpdate) => {
    if (!isMountedRef.current) return;
    
    setProgress(prev => ({
      ...prev,
      progressPercent: update.progress_percent ?? prev.progressPercent,
      currentStep: update.current_step ?? prev.currentStep,
      statusMessage: update.status_message ?? prev.statusMessage,
      currentIteration: update.current_iteration ?? prev.currentIteration,
      totalIterations: update.total_iterations ?? prev.total_iterations,
      estimatedSecondsRemaining: update.estimated_seconds_remaining ?? prev.estimatedSecondsRemaining,
      isLoading: false,
      error: null,
    }));
  }, []);
  
  // Handle training completion
  const handleTrainingComplete = useCallback((update: ProgressUpdate) => {
    if (!isMountedRef.current) return;
    
    setProgress(prev => ({
      ...prev,
      progressPercent: 100,
      currentStep: 'completed',
      statusMessage: 'Training completed successfully',
      isLoading: false,
      error: null,
      isComplete: true,
      isFailed: false,
    }));
    
    // Stop polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);
  
  // Handle training failure
  const handleTrainingFailed = useCallback((update: ProgressUpdate) => {
    if (!isMountedRef.current) return;
    
    setProgress(prev => ({
      ...prev,
      currentStep: 'failed',
      statusMessage: 'Training failed',
      isLoading: false,
      error: update.error_message || 'Training failed',
      isComplete: false,
      isFailed: true,
    }));
    
    // Stop polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);
  
  // WebSocket connection
  const { isConnected: isWebSocketConnected } = useProgressWebSocket({
    sceneId,
    token,
    enabled: enabled && enableWebSocket,
    onProgressUpdate: handleProgressUpdate,
    onTrainingComplete: handleTrainingComplete,
    onTrainingFailed: handleTrainingFailed,
  });
  
  // Initial fetch and polling setup
  useEffect(() => {
    if (!enabled) {
      return;
    }
    
    // Fetch initial progress
    fetchProgress();
    
    // Set up polling (as fallback or when WebSocket is disabled)
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    pollingIntervalRef.current = setInterval(() => {
      // Only poll if not complete or failed
      if (!progress.isComplete && !progress.isFailed) {
        fetchProgress();
      } else {
        // Stop polling if complete or failed
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    }, pollingInterval);
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [enabled, fetchProgress, pollingInterval, progress.isComplete, progress.isFailed]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);
  
  return {
    ...progress,
    isWebSocketConnected,
    refresh: fetchProgress,
  };
};

export default useSceneProgress;
