/**
 * API Client Utility
 * Provides authenticated fetch wrapper that uses correct base URL and token from Redux store
 */

import { store } from '../store';

/**
 * Get the authentication token from Redux store
 */
export function getAuthToken(): string | null {
  const state = store.getState();
  return state.auth?.token || null;
}

/**
 * Get the API base URL from environment variables
 */
export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
}

/**
 * Authenticated fetch wrapper
 * Automatically adds Authorization header and uses correct base URL
 */
export async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAuthToken();
  const baseUrl = getApiBaseUrl();
  
  // Remove leading slash from endpoint if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  
  // Construct full URL
  const url = `${baseUrl}/${cleanEndpoint}`;
  
  // Add Authorization header
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  // Make request
  return fetch(url, {
    ...options,
    headers,
  });
}

/**
 * Authenticated fetch with JSON response
 */
export async function authenticatedFetchJson<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await authenticatedFetch(endpoint, options);
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }
  
  return response.json();
}
