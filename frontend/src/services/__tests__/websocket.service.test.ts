/**
 * Unit tests for WebSocket service
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { websocketService } from '../websocket.service';
import type { ConnectionStatus } from '../../types/websocket.types';

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;
  static CLOSED = 3;

  readyState = MockWebSocket.CLOSED;
  url: string;
  onopen: ((ev: any) => any) | null = null;
  onclose: ((ev: any) => any) | null = null;
  onerror: ((ev: any) => any) | null = null;
  onmessage: ((ev: any) => any) | null = null;

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code: 1000, reason: 'closed' });
  });

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  // Helpers for tests
  __open() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.({});
  }
  __fail(code = 1006) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code, reason: 'abnormal' });
  }
}

describe('WebSocketService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    (globalThis as any).WebSocket = MockWebSocket as any;
    // Clear internal state
    websocketService['eventHandlers'].clear();
    websocketService['statusListeners'].clear();
  });

  afterEach(() => {
    websocketService.disconnect();
    vi.useRealTimers();
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

      // Stub connect so scheduleReconnect doesn't create real WebSocket instances
      const connectSpy = vi.spyOn(websocketService, 'connect').mockImplementation(() => {});

      // Provide the state scheduleReconnect needs
      service.currentSceneId = 'test-scene-id';
      service.currentToken = 'test-token';

      // Attempt 0 -> delay 1000ms
      service.reconnectAttempts = 0;
      service.scheduleReconnect();
      expect(connectSpy).not.toHaveBeenCalled();
      vi.advanceTimersByTime(1000);
      expect(service.reconnectAttempts).toBe(1);
      expect(connectSpy).toHaveBeenCalled();

      // Attempt 3 -> delay 8000ms (1s * 2^3)
      connectSpy.mockClear();
      service.reconnectAttempts = 3;
      service.scheduleReconnect();
      vi.advanceTimersByTime(8000);
      expect(service.reconnectAttempts).toBe(4);
      expect(connectSpy).toHaveBeenCalled();
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
