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
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/progress/scenes/${sceneId}?token=${encodeURIComponent(token)}`;
    
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
    
    ws.onclose = () => {
      console.log('[ProgressWebSocket] Disconnected');
      setIsConnected(false);
      
      // Clear heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
      
      // Attempt reconnection
      if (enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        console.log(`[ProgressWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      }
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
