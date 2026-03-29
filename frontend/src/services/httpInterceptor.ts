/**
 * HTTP interceptor for adding authentication and handling responses
 */

import { store } from '../store';
import { logout } from '../store/slices/authSlice';

interface RequestConfig extends RequestInit {
  skipAuth?: boolean;
}

class HttpInterceptor {
  private baseUrl: string;

  constructor(baseUrl: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1') {
    this.baseUrl = baseUrl;
  }

  /**
   * Intercept and enhance fetch requests
   */
  async fetch(url: string, config: RequestConfig = {}): Promise<Response> {
    const { skipAuth, ...fetchConfig } = config;

    // Build full URL
    const fullUrl = url.startsWith('http') ? url : `${this.baseUrl}${url}`;

    // Add authentication token
    const headers = new Headers(fetchConfig.headers);
    if (!skipAuth) {
      const token = store.getState().auth.token;
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
    }

    // Add content type if not set
    if (!headers.has('Content-Type') && !(fetchConfig.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    // Make request
    const response = await fetch(fullUrl, {
      ...fetchConfig,
      headers,
    });

    // Handle unauthorized
    if (response.status === 401) {
      store.dispatch(logout());
      throw new Error('Unauthorized');
    }

    // Handle errors
    if (!response.ok) {
      const error = await this.parseError(response);
      throw error;
    }

    return response;
  }

  /**
   * GET request
   */
  async get<T>(url: string, config?: RequestConfig): Promise<T> {
    const response = await this.fetch(url, { ...config, method: 'GET' });
    return response.json();
  }

  /**
   * POST request
   */
  async post<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    const response = await this.fetch(url, { ...config, method: 'POST', body });
    return response.json();
  }

  /**
   * PUT request
   */
  async put<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    const response = await this.fetch(url, { ...config, method: 'PUT', body });
    return response.json();
  }

  /**
   * PATCH request
   */
  async patch<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    const response = await this.fetch(url, { ...config, method: 'PATCH', body });
    return response.json();
  }

  /**
   * DELETE request
   */
  async delete<T>(url: string, config?: RequestConfig): Promise<T> {
    const response = await this.fetch(url, { ...config, method: 'DELETE' });
    return response.json();
  }

  /**
   * Parse error from response
   */
  private async parseError(response: Response): Promise<Error> {
    try {
      const data = await response.json();
      return new Error(data.message || data.error || 'Request failed');
    } catch {
      return new Error(`Request failed with status ${response.status}`);
    }
  }
}

export const httpClient = new HttpInterceptor();
