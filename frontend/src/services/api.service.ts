/**
 * API service for communicating with the backend
 */

import { httpClient } from './httpInterceptor';
import type { SceneMetadata, SceneTile } from '../types/scene.types';

export class ApiService {
  async fetchSceneMetadata(sceneId: string): Promise<SceneMetadata> {
    return httpClient.get<SceneMetadata>(`/scenes/${sceneId}`);
  }

  async fetchSceneTiles(
    sceneId: string,
    cameraPosition: [number, number, number],
    cameraDirection: [number, number, number],
    fov: number,
    bandwidth: number
  ): Promise<{ tiles: SceneTile[] }> {
    const params = new URLSearchParams({
      cameraPosition: cameraPosition.join(','),
      cameraDirection: cameraDirection.join(','),
      fov: fov.toString(),
      bandwidth: bandwidth.toString(),
    });

    return httpClient.get<{ tiles: SceneTile[] }>(`/scenes/${sceneId}/tiles?${params}`);
  }

  async uploadVideo(file: File, organizationId: string): Promise<SceneMetadata> {
    const formData = new FormData();
    formData.append('video', file);
    formData.append('organizationId', organizationId);

    return httpClient.post<SceneMetadata>('/scenes/upload', formData);
  }

  async importFile(file: File, organizationId: string, format: string): Promise<SceneMetadata> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('organizationId', organizationId);
    formData.append('format', format);

    return httpClient.post<SceneMetadata>('/scenes/import', formData);
  }

  async login(email: string, password: string): Promise<{ user: any; token: string }> {
    return httpClient.post<{ user: any; token: string }>(
      '/auth/login',
      { email, password },
      { skipAuth: true }
    );
  }

  async register(
    email: string,
    password: string,
    name: string
  ): Promise<{ user: any; token: string }> {
    return httpClient.post<{ user: any; token: string }>(
      '/auth/register',
      { email, password, name },
      { skipAuth: true }
    );
  }

  async logout(): Promise<void> {
    return httpClient.post<void>('/auth/logout', {});
  }

  async fetchSceneProgress(sceneId: string): Promise<ProgressResponse> {
    return httpClient.get<ProgressResponse>(`/scenes/${sceneId}/progress`);
  }
}

export const apiService = new ApiService();

// Progress response type
export interface ProgressResponse {
  scene_id: string;
  progress_percent: number;
  current_step: string;
  status_message: string;
  current_iteration?: number;
  total_iterations?: number;
  estimated_seconds_remaining?: number;
  started_at?: string;
  elapsed_seconds?: number;
}
