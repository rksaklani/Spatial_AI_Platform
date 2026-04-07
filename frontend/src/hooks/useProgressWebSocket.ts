/**
 * useProgressWebSocket Hook
 * 
 * Custom hook for managing WebSocket connection to receive real-time
 * progress updates for scene training.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface ProgressUpdate {
  type: 'progress_update' | 'training_complete' | 'training_failed' | 'error';
  scene_id: string;
  progress_percent?: number;
  current_step?: string;
  status_message?: string;
  current_iteration?: number;
  total_iterations?: number;
  estimated_seconds_remaining?: number;
  error_message?: string;
  total_time_seconds?: number;
  timestamp: string;
}

interface UseProgressWebSocketOptions {
  /** Scene ID to subscribe to */
  sceneId: string;
  /** JWT authentication token */
  token: string;
  /** Callback for progress updates */
  onProgressUpdate?: (update: ProgressUpdate) => void;
  /** Callback for training completion */
  onTrainingComplete?: (update: ProgressUpdate) => void;
  /** Callback for training failure */
  onTrainingFailed?: (update: ProgressUpdate) => void;
  /** Enable WebSocket connection */
  enabled?: boolean;
}

export const useProgressWebSocket = ({
  sceneId,
  token,
  onProgressUpdate,
  onTrainingComplete,
  onTrainingFailed,
  enabled = true,
}: UseProgressWebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<ProgressUpdate | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  
  const connect = useCallback(() => {
    if (!enabled || !sceneId || !token) {
      return;
    }
    
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    // Determine WebSocket URL
    // Use VITE_WS_URL if available, otherwise construct from VITE_API_BASE_URL
    let wsBaseUrl: string;
    
    if (import.meta.env.VITE_WS_URL) {
      // Use explicit WebSocket URL from env
      wsBaseUrl = import.meta.env.VITE_WS_URL;
    } else if (import.meta.env.VITE_API_BASE_URL) {
      // Construct from API base URL
      const apiUrl = import.meta.env.VITE_API_BASE_URL;
      const protocol = apiUrl.startsWith('https') ? 'wss:' : 'ws:';
      const host = apiUrl.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '');
      wsBaseUrl = `${protocol}//${host}`;
    } else {
      // Fallback to current host
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsBaseUrl = `${protocol}//${window.location.host}`;
    }
    
    const wsUrl = `${wsBaseUrl}/api/v1/progress/scenes/${sceneId}?token=${encodeURIComponent(token)}`;
    
    console.log(`[ProgressWebSocket] Connecting to ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('[ProgressWebSocket] Connected');
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      
      // Send subscribe message
      ws.send(JSON.stringify({
        type: 'subscribe',
        scene_id: sceneId,
      }));
      
      // Start heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, 30000); // Send heartbeat every 30 seconds
    };
    
    ws.onmessage = (event) => {
      try {
        const update: ProgressUpdate = JSON.parse(event.data);
        console.log('[ProgressWebSocket] Received update:', update);
        
        setLastUpdate(update);
        
        // Call appropriate callback
        switch (update.type) {
          case 'progress_update':
            onProgressUpdate?.(update);
            break;
          case 'training_complete':
            onTrainingComplete?.(update);
            break;
          case 'training_failed':
            onTrainingFailed?.(update);
            break;
          case 'error':
            console.error('[ProgressWebSocket] Error:', update.error_message);
            break;
        }
      } catch (error) {
        console.error('[ProgressWebSocket] Failed to parse message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('[ProgressWebSocket] Error:', error);
    };
    
    ws.onclose = (event) => {
      console.log('[ProgressWebSocket] Disconnected', event.code, event.reason);
      setIsConnected(false);
      
      // Clear heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
      
      // Don't reconnect if:
      // - Not enabled
      // - Max reconnect attempts reached
      // - Close code indicates permanent failure (4000-4999 are custom app codes)
      // - Close code 1000 (normal closure) or 1001 (going away)
      const shouldNotReconnect = 
        !enabled || 
        reconnectAttemptsRef.current >= maxReconnectAttempts ||
        (event.code >= 4000 && event.code < 5000) ||
        event.code === 1000 ||
        event.code === 1001;
      
      if (shouldNotReconnect) {
        console.log(`[ProgressWebSocket] Not reconnecting (code: ${event.code}, attempts: ${reconnectAttemptsRef.current})`);
        return;
      }
      
      // Attempt reconnection
      reconnectAttemptsRef.current++;
      const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
      console.log(`[ProgressWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    };
  }, [sceneId, token, enabled, onProgressUpdate, onTrainingComplete, onTrainingFailed]);
  
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setIsConnected(false);
  }, []);
  
  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (enabled) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);
  
  return {
    isConnected,
    lastUpdate,
    reconnect: connect,
    disconnect,
  };
};

export default useProgressWebSocket;
