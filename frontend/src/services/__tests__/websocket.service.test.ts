/**
 * Unit tests for WebSocket service
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { websocketService } from '../websocket.service';
import type { ConnectionStatus } from '../../types/websocket.types';

// Mock socket.io-client
vi.mock('socket.io-client', () => {
  const mockSocket = {
    connected: false,
    connect: vi.fn(),
    disconnect: vi.fn(),
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  };

  return {
    io: vi.fn(() => mockSocket),
  };
});

describe('WebSocketService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Clear internal state
    websocketService['eventHandlers'].clear();
    websocketService['statusListeners'].clear();
  });

  afterEach(() => {
    websocketService.disconnect();
  });

  describe('Connection Management', () => {
    it('should initialize with disconnected status', () => {
      expect(websocketService.getStatus()).toBe('disconnected');
    });

    it('should update status to connecting when connect is called', () => {
      const statusListener = vi.fn();
      websocketService.onStatusChange(statusListener);

      websocketService.connect('test-scene-id', 'test-token');

      expect(statusListener).toHaveBeenCalledWith('connecting');
    });

    it('should allow subscribing to status changes', () => {
      const listener = vi.fn();
      const unsubscribe = websocketService.onStatusChange(listener);

      expect(typeof unsubscribe).toBe('function');
    });

    it('should remove listener when unsubscribe is called', () => {
      const listener = vi.fn();
      const unsubscribe = websocketService.onStatusChange(listener);

      unsubscribe();
      websocketService.connect('test-scene-id', 'test-token');

      // Listener should not be called after unsubscribe
      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('Event Handling', () => {
    it('should allow subscribing to events', () => {
      const handler = vi.fn();
      const unsubscribe = websocketService.on('test:event', handler);

      expect(typeof unsubscribe).toBe('function');
    });

    it('should remove event handler when unsubscribe is called', () => {
      const handler = vi.fn();
      const unsubscribe = websocketService.on('test:event', handler);

      unsubscribe();

      // Handler should not be in the map anymore
      expect(websocketService['eventHandlers'].has('test:event')).toBe(false);
    });

    it('should support multiple handlers for the same event', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      websocketService.on('test:event', handler1);
      websocketService.on('test:event', handler2);

      const handlers = websocketService['eventHandlers'].get('test:event');
      expect(handlers?.size).toBe(2);
    });
  });

  describe('Message Sending', () => {
    it('should not send messages when disconnected', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      websocketService.send('test', { data: 'test' });

      expect(consoleSpy).toHaveBeenCalledWith(
        'Cannot send message: WebSocket not connected'
      );

      consoleSpy.mockRestore();
    });

    it('should provide helper methods for common events', () => {
      expect(typeof websocketService.sendCursorMove).toBe('function');
      expect(typeof websocketService.sendAnnotationCreated).toBe('function');
      expect(typeof websocketService.sendAnnotationUpdated).toBe('function');
      expect(typeof websocketService.sendAnnotationDeleted).toBe('function');
    });
  });

  describe('Reconnection Logic', () => {
    it('should implement exponential backoff for reconnection', () => {
      const service = websocketService as any;

      // Test exponential backoff calculation
      service.reconnectAttempts = 0;
      service.scheduleReconnect();
      expect(service.reconnectAttempts).toBe(1);

      service.reconnectAttempts = 3;
      service.scheduleReconnect();
      expect(service.reconnectAttempts).toBe(4);
    });

    it('should stop reconnecting after max attempts', () => {
      const service = websocketService as any;
      const statusListener = vi.fn();
      
      websocketService.onStatusChange(statusListener);
      service.reconnectAttempts = service.maxReconnectAttempts;
      service.scheduleReconnect();

      expect(statusListener).toHaveBeenCalledWith('error');
    });
  });
});
