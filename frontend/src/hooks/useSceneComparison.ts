/**
 * Scene Comparison Hook
 * 
 * Provides functionality for comparing two scenes including:
 * - Loading scene data
 * - Calculating change metrics
 * - Managing comparison state
 */

import { useState, useCallback, useEffect } from 'react';

export interface ChangeMetrics {
  volumeDifference: number;
  areaDifference: number;
  pointCountDifference: number;
  addedPoints: number;
  removedPoints: number;
  changedPoints: number;
}

export interface ComparisonMode {
  type: 'side-by-side' | 'temporal' | 'difference';
  opacity?: number;
}

export interface SceneComparisonState {
  isLoading: boolean;
  error: Error | null;
  metrics: ChangeMetrics | null;
  mode: ComparisonMode;
}

export const useSceneComparison = (sceneId1: string, sceneId2: string) => {
  const [state, setState] = useState<SceneComparisonState>({
    isLoading: false,
    error: null,
    metrics: null,
    mode: { type: 'side-by-side' },
  });

  const setMode = useCallback((mode: ComparisonMode) => {
    setState(prev => ({ ...prev, mode }));
  }, []);

  const setOpacity = useCallback((opacity: number) => {
    setState(prev => ({
      ...prev,
      mode: { ...prev.mode, opacity },
    }));
  }, []);

  const loadComparison = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // Fetch scene metadata for both scenes
      const [response1, response2] = await Promise.all([
        fetch(`/api/v1/scenes/${sceneId1}/metadata`),
        fetch(`/api/v1/scenes/${sceneId2}/metadata`),
      ]);

      if (!response1.ok || !response2.ok) {
        throw new Error('Failed to load scene metadata');
      }

      const [metadata1, metadata2] = await Promise.all([
        response1.json(),
        response2.json(),
      ]);

      // Calculate metrics (simplified - in production, this would be more sophisticated)
      const metrics: ChangeMetrics = {
        volumeDifference: Math.abs((metadata2.bounds?.volume || 0) - (metadata1.bounds?.volume || 0)),
        areaDifference: Math.abs((metadata2.bounds?.area || 0) - (metadata1.bounds?.area || 0)),
        pointCountDifference: (metadata2.gaussian_count || 0) - (metadata1.gaussian_count || 0),
        addedPoints: Math.max(0, (metadata2.gaussian_count || 0) - (metadata1.gaussian_count || 0)),
        removedPoints: Math.max(0, (metadata1.gaussian_count || 0) - (metadata2.gaussian_count || 0)),
        changedPoints: 0, // Would require detailed point-by-point comparison
      };

      setState(prev => ({
        ...prev,
        isLoading: false,
        metrics,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error,
      }));
    }
  }, [sceneId1, sceneId2]);

  useEffect(() => {
    loadComparison();
  }, [loadComparison]);

  return {
    ...state,
    setMode,
    setOpacity,
    reload: loadComparison,
  };
};

export default useSceneComparison;
