/**
 * Unit tests for useWebSocket hook
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import { websocketService } from '../../services/websocket.service';

// Mock the websocket service
vi.mock('../../services/websocket.service', () => ({
  websocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    getStatus: vi.fn(() => 'disconnected'),
    onStatusChange: vi.fn((callback) => {
      // Return unsubscribe function
      return () => {};
    }),
    send: vi.fn(),
    on: vi.fn(() => () => {}),
    sendCursorMove: vi.fn(),
    sendAnnotationCreated: vi.fn(),
    sendAnnotationUpdated: vi.fn(),
    sendAnnotationDeleted: vi.fn(),
  },
}));

describe('useWebSocket', () => {
  const mockSceneId = 'test-scene-id';
  const mockToken = 'test-token';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with disconnected status', () => {
    const { result } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    expect(result.current.status).toBe('disconnected');
    expect(result.current.isConnected).toBe(false);
  });

  it('should auto-connect when autoConnect is true', () => {
    renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: true })
    );

    expect(websocketService.connect).toHaveBeenCalledWith(mockSceneId, mockToken);
  });

  it('should not auto-connect when autoConnect is false', () => {
    renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    expect(websocketService.connect).not.toHaveBeenCalled();
  });

  it('should disconnect on unmount when autoConnect is true', () => {
    const { unmount } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: true })
    );

    unmount();

    expect(websocketService.disconnect).toHaveBeenCalled();
  });

  it('should provide connect function', () => {
    const { result } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    act(() => {
      result.current.connect();
    });

    expect(websocketService.connect).toHaveBeenCalledWith(mockSceneId, mockToken);
  });

  it('should provide disconnect function', () => {
    const { result } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    act(() => {
      result.current.disconnect();
    });

    expect(websocketService.disconnect).toHaveBeenCalled();
  });

  it('should provide send function', () => {
    const { result } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    act(() => {
      result.current.send('test:event', { data: 'test' });
    });

    expect(websocketService.send).toHaveBeenCalledWith('test:event', { data: 'test' });
  });

  it('should provide on function for event subscription', () => {
    const { result } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    const handler = vi.fn();
    act(() => {
      result.current.on('test:event', handler);
    });

    expect(websocketService.on).toHaveBeenCalledWith('test:event', handler);
  });

  it('should provide helper methods for collaboration events', () => {
    const { result } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    expect(typeof result.current.sendCursorMove).toBe('function');
    expect(typeof result.current.sendAnnotationCreated).toBe('function');
    expect(typeof result.current.sendAnnotationUpdated).toBe('function');
    expect(typeof result.current.sendAnnotationDeleted).toBe('function');
  });

  it('should call sendCursorMove on websocket service', () => {
    const { result } = renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    const position: [number, number, number] = [1, 2, 3];
    const cameraPosition: [number, number, number] = [4, 5, 6];

    act(() => {
      result.current.sendCursorMove(position, cameraPosition);
    });

    expect(websocketService.sendCursorMove).toHaveBeenCalledWith(position, cameraPosition);
  });

  it('should subscribe to status changes', () => {
    renderHook(() =>
      useWebSocket({ sceneId: mockSceneId, token: mockToken, autoConnect: false })
    );

    expect(websocketService.onStatusChange).toHaveBeenCalled();
  });
});
