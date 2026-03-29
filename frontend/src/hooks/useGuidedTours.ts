import { useState, useEffect } from 'react';
import { apiService } from '../services/api.service';

interface CameraKeyframe {
  position: [number, number, number];
  rotation: [number, number, number, number];
  timestamp: number;
}

interface Narration {
  timestamp: number;
  text: string;
}

interface GuidedTour {
  id: string;
  scene_id: string;
  user_id: string;
  name: string;
  camera_path: CameraKeyframe[];
  narration: Narration[];
  duration: number;
  created_at: string;
}

interface CreateTourData {
  name: string;
  camera_path: CameraKeyframe[];
  narration: Narration[];
}

export const useGuidedTours = (sceneId: string) => {
  const [tours, setTours] = useState<GuidedTour[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all tours for a scene
  const fetchTours = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.get(`/scenes/${sceneId}/tours`);
      setTours(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch tours');
      console.error('Error fetching tours:', err);
    } finally {
      setLoading(false);
    }
  };

  // Create a new tour
  const createTour = async (tourData: CreateTourData): Promise<GuidedTour | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.post(`/scenes/${sceneId}/tours`, tourData);
      const newTour = response.data;
      setTours(prev => [...prev, newTour]);
      return newTour;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create tour');
      console.error('Error creating tour:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Get a specific tour
  const getTour = async (tourId: string): Promise<GuidedTour | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.get(`/scenes/${sceneId}/tours/${tourId}`);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch tour');
      console.error('Error fetching tour:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Delete a tour
  const deleteTour = async (tourId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      await apiService.delete(`/scenes/${sceneId}/tours/${tourId}`);
      setTours(prev => prev.filter(t => t.id !== tourId));
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete tour');
      console.error('Error deleting tour:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Load tours on mount
  useEffect(() => {
    if (sceneId) {
      fetchTours();
    }
  }, [sceneId]);

  return {
    tours,
    loading,
    error,
    fetchTours,
    createTour,
    getTour,
    deleteTour
  };
};
