import React, { useState } from 'react';
import { Button } from '../common';

/**
 * ViewerToolbar Component
 * 
 * Floating toolbar at the bottom of the 3D viewer with camera controls,
 * rendering mode toggle, FPS counter, coordinate display, and settings.
 * 
 * Requirements: 5.5, 5.7, 6.4, 7.4
 */

export interface ViewerToolbarProps {
  // Camera controls
  onResetCamera?: () => void;
  onFitToView?: () => void;
  onPresetView?: (view: 'top' | 'front' | 'side' | 'isometric') => void;
  
  // Rendering mode
  renderingMode: 'client' | 'server';
  onRenderingModeToggle?: () => void;
  
  // FPS counter
  fps?: number;
  showFps: boolean;
  onToggleFps?: () => void;
  
  // Coordinate display
  showCoordinates: boolean;
  onToggleCoordinates?: () => void;
  cameraPosition?: [number, number, number];
  
  // Settings
  onOpenSettings?: () => void;
}

export const ViewerToolbar: React.FC<ViewerToolbarProps> = ({
  onResetCamera,
  onFitToView,
  onPresetView,
  renderingMode,
  onRenderingModeToggle,
  fps = 0,
  showFps,
  onToggleFps,
  showCoordinates,
  onToggleCoordinates,
  cameraPosition,
  onOpenSettings,
}) => {
  const [showPresetMenu, setShowPresetMenu] = useState(false);

  // Format camera position for display
  const formatPosition = (pos?: [number, number, number]): string => {
    if (!pos) return 'N/A';
    return `X: ${pos[0].toFixed(2)}, Y: ${pos[1].toFixed(2)}, Z: ${pos[2].toFixed(2)}`;
  };

  // Get FPS color based on performance
  const getFpsColor = (fps: number): string => {
    if (fps >= 50) return 'text-green-400';
    if (fps >= 30) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
      {/* Main toolbar */}
      <div className="bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-2xl px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Camera Controls Section */}
          <div className="flex items-center gap-2 border-r border-border-color pr-3">
            <Button
              variant="icon"
              size="sm"
              onClick={onResetCamera}
              title="Reset Camera"
              aria-label="Reset camera to default position"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </Button>

            <Button
              variant="icon"
              size="sm"
              onClick={onFitToView}
              title="Fit to View"
              aria-label="Fit scene to view"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
                />
              </svg>
            </Button>

            {/* Preset Views Dropdown */}
            <div className="relative">
              <Button
                variant="icon"
                size="sm"
                onClick={() => setShowPresetMenu(!showPresetMenu)}
                title="Preset Views"
                aria-label="Select preset camera view"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </Button>

              {/* Preset menu dropdown */}
              {showPresetMenu && (
                <div className="absolute bottom-full mb-2 left-0 bg-secondary-bg border border-border-color rounded-lg shadow-xl py-1 min-w-[120px]">
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-hover-bg transition-colors"
                    onClick={() => {
                      onPresetView?.('top');
                      setShowPresetMenu(false);
                    }}
                  >
                    Top View
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-hover-bg transition-colors"
                    onClick={() => {
                      onPresetView?.('front');
                      setShowPresetMenu(false);
                    }}
                  >
                    Front View
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-hover-bg transition-colors"
                    onClick={() => {
                      onPresetView?.('side');
                      setShowPresetMenu(false);
                    }}
                  >
                    Side View
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-hover-bg transition-colors"
                    onClick={() => {
                      onPresetView?.('isometric');
                      setShowPresetMenu(false);
                    }}
                  >
                    Isometric
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Rendering Mode Toggle */}
          <div className="flex items-center gap-2 border-r border-border-color pr-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={onRenderingModeToggle}
              title={`Switch to ${renderingMode === 'client' ? 'server' : 'client'}-side rendering`}
              aria-label={`Current rendering mode: ${renderingMode}-side. Click to toggle.`}
            >
              <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {renderingMode === 'client' ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
                  />
                )}
              </svg>
              <span className="text-xs">
                {renderingMode === 'client' ? 'Client' : 'Server'}
              </span>
            </Button>
          </div>

          {/* FPS Counter */}
          <div className="flex items-center gap-2 border-r border-border-color pr-3">
            <Button
              variant="icon"
              size="sm"
              onClick={onToggleFps}
              title={showFps ? 'Hide FPS counter' : 'Show FPS counter'}
              aria-label={`FPS counter: ${showFps ? 'visible' : 'hidden'}. Click to toggle.`}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </Button>
            {showFps && (
              <span className={`text-sm font-mono ${getFpsColor(fps)}`}>
                {fps} FPS
              </span>
            )}
          </div>

          {/* Coordinate Display */}
          <div className="flex items-center gap-2 border-r border-border-color pr-3">
            <Button
              variant="icon"
              size="sm"
              onClick={onToggleCoordinates}
              title={showCoordinates ? 'Hide coordinates' : 'Show coordinates'}
              aria-label={`Coordinates: ${showCoordinates ? 'visible' : 'hidden'}. Click to toggle.`}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                />
              </svg>
            </Button>
            {showCoordinates && (
              <span className="text-xs text-text-secondary font-mono">
                {formatPosition(cameraPosition)}
              </span>
            )}
          </div>

          {/* Settings Button */}
          <Button
            variant="icon"
            size="sm"
            onClick={onOpenSettings}
            title="Open settings"
            aria-label="Open viewer settings"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  );
};
