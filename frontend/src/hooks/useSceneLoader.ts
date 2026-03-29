/**
 * Custom hook for loading 3D scene data
 */

import { useState, useEffect } from 'react';
import { apiService } from '../services/api.service';
import type { SceneMetadata } from '../types/scene.types';

export function useSceneLoader(sceneId: string | null) {
  const [scene, setScene] = useState<SceneMetadata | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!sceneId) {
      setScene(null);
      return;
    }

    const loadScene = async () => {
      setLoading(true);
      setError(null);
      try {
        const metadata = await apiService.fetchSceneMetadata(sceneId);
        setScene(metadata);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load scene'));
      } finally {
        setLoading(false);
      }
    };

    loadScene();
  }, [sceneId]);

  return { scene, loading, error };
}
