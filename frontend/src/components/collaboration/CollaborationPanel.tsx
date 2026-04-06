/**
 * CollaborationPanel Component
 * 
 * Displays list of connected users with their status and colors
 * Requirements: F6
 */

import { useState, useRef, useEffect } from 'react';
import type { ConnectionStatus } from '../../services/websocket.service';
import type { CollaborationUser } from '../../hooks/useCollaboration';

interface CollaborationPanelProps {
  users: CollaborationUser[];
  connectionStatus: ConnectionStatus;
  onClose?: () => void;
}

const STATUS_COLORS: Record<ConnectionStatus, string> = {
  connected: 'text-status-success',
  connecting: 'text-status-warning',
  disconnected: 'text-text-secondary',
  error: 'text-status-error',
};

const STATUS_LABELS: Record<ConnectionStatus, string> = {
  connected: 'Connected',
  connecting: 'Connecting...',
  disconnected: 'Disconnected',
  error: 'Connection Error',
};

export function CollaborationPanel({
  users,
  connectionStatus,
  onClose,
}: CollaborationPanelProps) {
  const [position, setPosition] = useState({ x: 0, y: 80 }); // Start at top-right
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const panelRef = useRef<HTMLDivElement>(null);

  // Initialize position on mount
  useEffect(() => {
    if (panelRef.current) {
      const rect = panelRef.current.getBoundingClientRect();
      setPosition({ x: window.innerWidth - rect.width - 16, y: 80 });
    }
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    // Prevent text selection while dragging
    e.preventDefault();
    
    setIsDragging(true);
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  };

  useEffect(() => {
    if (isDragging) {
      const handleMove = (e: MouseEvent) => {
        if (panelRef.current) {
          const newX = e.clientX - dragOffset.x;
          const newY = e.clientY - dragOffset.y;

          // Constrain to viewport
          const rect = panelRef.current.getBoundingClientRect();
          const maxX = window.innerWidth - rect.width;
          const maxY = window.innerHeight - rect.height;

          setPosition({
            x: Math.max(0, Math.min(newX, maxX)),
            y: Math.max(0, Math.min(newY, maxY)),
          });
        }
      };

      const handleUp = () => {
        setIsDragging(false);
      };

      document.addEventListener('mousemove', handleMove);
      document.addEventListener('mouseup', handleUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMove);
        document.removeEventListener('mouseup', handleUp);
      };
    }
  }, [isDragging, dragOffset]);

  const isActive = (user: CollaborationUser) => {
    const timeSinceUpdate = Date.now() - user.lastUpdate;
    return timeSinceUpdate < 10000; // Active if updated within last 10 seconds
  };

  return (
    <div
      ref={panelRef}
      className="fixed w-80 bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg shadow-lg z-10"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'default',
      }}
    >
      {/* Header - Draggable */}
      <div
        className="drag-handle flex items-center justify-between p-4 border-b border-border-subtle cursor-grab active:cursor-grabbing select-none"
        onMouseDown={handleMouseDown}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        <div className="flex items-center gap-2">
          {/* Drag indicator */}
          <svg className="w-4 h-4 text-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
          </svg>
          <svg className="w-5 h-5 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="text-sm font-semibold text-text-primary">
            Collaboration
          </h3>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            onMouseDown={(e) => e.stopPropagation()}
            className="text-text-secondary hover:text-text-primary transition-colors"
            aria-label="Close panel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Connection Status */}
      <div className="px-4 py-3 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            connectionStatus === 'connected' ? 'bg-status-success' :
            connectionStatus === 'connecting' ? 'bg-status-warning animate-pulse' :
            connectionStatus === 'error' ? 'bg-status-error' :
            'bg-text-secondary'
          }`} />
          <span className={`text-sm ${STATUS_COLORS[connectionStatus]}`}>
            {STATUS_LABELS[connectionStatus]}
          </span>
        </div>
      </div>

      {/* User List */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-text-secondary uppercase tracking-wide">
            Active Users
          </span>
          <span className="text-xs font-semibold text-text-primary bg-surface-base px-2 py-1 rounded">
            {users.length}
          </span>
        </div>

        {users.length === 0 ? (
          <div className="text-center py-8">
            <svg className="w-12 h-12 mx-auto text-text-tertiary mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="text-sm text-text-secondary">
              {connectionStatus === 'connected' ? 'No other users online' : 'Not connected'}
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {users.map((user) => (
              <div
                key={user.userId}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-base transition-colors"
              >
                {/* User Color Indicator */}
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold"
                  style={{ backgroundColor: user.color }}
                >
                  {user.userName.charAt(0).toUpperCase()}
                </div>

                {/* User Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary truncate">
                      {user.userName}
                    </span>
                    {isActive(user) ? (
                      <span className="flex items-center gap-1 text-xs text-status-success">
                        <div className="w-1.5 h-1.5 rounded-full bg-status-success" />
                        Active
                      </span>
                    ) : (
                      <span className="text-xs text-text-tertiary">
                        Idle
                      </span>
                    )}
                  </div>
                  {user.cursorPosition && (
                    <span className="text-xs text-text-tertiary">
                      Viewing scene
                    </span>
                  )}
                </div>

                {/* User Actions */}
                <button
                  className="text-text-secondary hover:text-text-primary transition-colors"
                  aria-label="User options"
                  title="User options"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border-subtle bg-surface-base/50">
        <p className="text-xs text-text-tertiary text-center">
          Real-time collaboration enabled
        </p>
      </div>
    </div>
  );
}
