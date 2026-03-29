/**
 * Custom hook for managing scene annotations
 * 
 * Provides:
 * - Fetching annotations for a scene
 * - Creating new annotations
 * - Updating existing annotations
 * - Deleting annotations
 * - Real-time updates (future: WebSocket integration)
 */

import { useState, useEffect, useCallback } from 'react';
import { Annotation } from '../components/AnnotationOverlay';

interface UseAnnotationsOptions {
  sceneId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseAnnotationsReturn {
  annotations: Annotation[];
  isLoading: boolean;
  error: Error | null;
  createAnnotation: (annotation: Partial<Annotation>) => Promise<Annotation>;
  updateAnnotation: (id: string, updates: Partial<Annotation>) => Promise<Annotation>;
  deleteAnnotation: (id: string) => Promise<void>;
  refreshAnnotations: () => Promise<void>;
}

export const useAnnotations = ({
  sceneId,
  autoRefresh = false,
  refreshInterval = 5000,
}: UseAnnotationsOptions): UseAnnotationsReturn => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Fetch annotations from API
  const fetchAnnotations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/scenes/${sceneId}/annotations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch annotations: ${response.statusText}`);
      }

      const data = await response.json();
      setAnnotations(data.items || []);
    } catch (err) {
      setError(err as Error);
      console.error('Error fetching annotations:', err);
    } finally {
      setIsLoading(false);
    }
  }, [sceneId]);

  // Create new annotation
  const createAnnotation = useCallback(async (annotation: Partial<Annotation>): Promise<Annotation> => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/scenes/${sceneId}/annotations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(annotation),
      });

      if (!response.ok) {
        throw new Error(`Failed to create annotation: ${response.statusText}`);
      }

      const newAnnotation = await response.json();
      setAnnotations(prev => [...prev, newAnnotation]);
      return newAnnotation;
    } catch (err) {
      console.error('Error creating annotation:', err);
      throw err;
    }
  }, [sceneId]);

  // Update existing annotation
  const updateAnnotation = useCallback(async (id: string, updates: Partial<Annotation>): Promise<Annotation> => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/scenes/${sceneId}/annotations/${id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update annotation: ${response.statusText}`);
      }

      const updatedAnnotation = await response.json();
      setAnnotations(prev => prev.map(a => a._id === id ? updatedAnnotation : a));
      return updatedAnnotation;
    } catch (err) {
      console.error('Error updating annotation:', err);
      throw err;
    }
  }, [sceneId]);

  // Delete annotation
  const deleteAnnotation = useCallback(async (id: string): Promise<void> => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/scenes/${sceneId}/annotations/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete annotation: ${response.statusText}`);
      }

      setAnnotations(prev => prev.filter(a => a._id !== id));
    } catch (err) {
      console.error('Error deleting annotation:', err);
      throw err;
    }
  }, [sceneId]);

  // Initial fetch
  useEffect(() => {
    fetchAnnotations();
  }, [fetchAnnotations]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAnnotations();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAnnotations]);

  return {
    annotations,
    isLoading,
    error,
    createAnnotation,
    updateAnnotation,
    deleteAnnotation,
    refreshAnnotations: fetchAnnotations,
  };
};

export default useAnnotations;
