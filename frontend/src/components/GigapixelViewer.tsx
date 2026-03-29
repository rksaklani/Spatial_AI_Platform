/**
 * Gigapixel Photo Viewer Component
 * 
 * Task 28.3: Implement gigapixel viewer
 * - Open photos in zoomable viewer
 * - Support zoom up to 10x for photos > 100MP
 * - Use tiled image loading for progressive zoom
 * 
 * Requirements: 26.5, 26.6, 26.8
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';

interface PhotoMetadata {
  id: string;
  filename: string;
  width: number;
  height: number;
  megapixels: number;
  originalUrl: string;
  tilesUrl?: string;
}

interface GigapixelViewerProps {
  photo: PhotoMetadata;
  onClose: () => void;
  onPositionClick?: (x: number, y: number) => void;
}

interface ViewState {
  zoom: number;
  offsetX: number;
  offsetY: number;
}

const GigapixelViewer: React.FC<GigapixelViewerProps> = ({
  photo,
  onClose,
  onPositionClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  
  const [viewState, setViewState] = useState<ViewState>({
    zoom: 1,
    offsetX: 0,
    offsetY: 0,
  });
  
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(true);
  
  // Maximum zoom level based on megapixels
  const maxZoom = photo.megapixels > 100 ? 10 : 5;
  const minZoom = 0.5;
  
  // Load image
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = photo.originalUrl;
    
    img.onload = () => {
      imageRef.current = img;
      setIsLoading(false);
      renderImage();
    };
    
    img.onerror = () => {
      console.error('Failed to load image');
      setIsLoading(false);
    };
  }, [photo.originalUrl]);
  
  // Render image on canvas
  const renderImage = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    
    if (!canvas || !img) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size to container size
    const container = containerRef.current;
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }
    
    // Clear canvas
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Calculate scaled dimensions
    const scaledWidth = img.width * viewState.zoom;
    const scaledHeight = img.height * viewState.zoom;
    
    // Center image if smaller than canvas
    let drawX = viewState.offsetX;
    let drawY = viewState.offsetY;
    
    if (scaledWidth < canvas.width) {
      drawX = (canvas.width - scaledWidth) / 2;
    }
    if (scaledHeight < canvas.height) {
      drawY = (canvas.height - scaledHeight) / 2;
    }
    
    // Draw image
    ctx.drawImage(
      img,
      drawX,
      drawY,
      scaledWidth,
      scaledHeight
    );
  }, [viewState]);
  
  // Re-render when view state changes
  useEffect(() => {
    if (!isLoading) {
      renderImage();
    }
  }, [viewState, isLoading, renderImage]);
  
  // Handle zoom
  const handleZoom = useCallback((delta: number, centerX?: number, centerY?: number) => {
    setViewState(prev => {
      const newZoom = Math.max(minZoom, Math.min(maxZoom, prev.zoom + delta));
      
      if (centerX !== undefined && centerY !== undefined) {
        // Zoom towards cursor position
        const zoomRatio = newZoom / prev.zoom;
        const newOffsetX = centerX - (centerX - prev.offsetX) * zoomRatio;
        const newOffsetY = centerY - (centerY - prev.offsetY) * zoomRatio;
        
        return {
          zoom: newZoom,
          offsetX: newOffsetX,
          offsetY: newOffsetY,
        };
      }
      
      return { ...prev, zoom: newZoom };
    });
  }, [maxZoom, minZoom]);
  
  // Handle wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const centerX = e.clientX - rect.left;
    const centerY = e.clientY - rect.top;
    
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    handleZoom(delta, centerX, centerY);
  }, [handleZoom]);
  
  // Handle mouse down
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  }, []);
  
  // Handle mouse move
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return;
    
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    
    setViewState(prev => ({
      ...prev,
      offsetX: prev.offsetX + dx,
      offsetY: prev.offsetY + dy,
    }));
    
    setDragStart({ x: e.clientX, y: e.clientY });
  }, [isDragging, dragStart]);
  
  // Handle mouse up
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  // Handle canvas click for position selection
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onPositionClick || !imageRef.current) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;
    
    // Convert canvas coordinates to image coordinates
    const imageX = (canvasX - viewState.offsetX) / viewState.zoom;
    const imageY = (canvasY - viewState.offsetY) / viewState.zoom;
    
    // Normalize to 0-1 range
    const normalizedX = imageX / imageRef.current.width;
    const normalizedY = imageY / imageRef.current.height;
    
    if (normalizedX >= 0 && normalizedX <= 1 && normalizedY >= 0 && normalizedY <= 1) {
      onPositionClick(normalizedX, normalizedY);
    }
  }, [viewState, onPositionClick]);
  
  // Zoom controls
  const zoomIn = () => handleZoom(0.5);
  const zoomOut = () => handleZoom(-0.5);
  const resetZoom = () => setViewState({ zoom: 1, offsetX: 0, offsetY: 0 });
  
  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-90 flex flex-col">
      {/* Header */}
      <div className="bg-gray-900 text-white p-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{photo.filename}</h2>
          <p className="text-sm text-gray-400">
            {photo.width} × {photo.height} ({photo.megapixels.toFixed(1)} MP)
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:text-gray-300 text-2xl font-bold px-4"
        >
          ×
        </button>
      </div>
      
      {/* Viewer */}
      <div ref={containerRef} className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-white text-lg">Loading image...</div>
          </div>
        )}
        
        <canvas
          ref={canvasRef}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onClick={handleCanvasClick}
          className="cursor-move"
          style={{ display: isLoading ? 'none' : 'block' }}
        />
      </div>
      
      {/* Controls */}
      <div className="bg-gray-900 text-white p-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={zoomOut}
            disabled={viewState.zoom <= minZoom}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded"
          >
            Zoom Out
          </button>
          <span className="text-sm">
            {(viewState.zoom * 100).toFixed(0)}%
          </span>
          <button
            onClick={zoomIn}
            disabled={viewState.zoom >= maxZoom}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded"
          >
            Zoom In
          </button>
          <button
            onClick={resetZoom}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            Reset
          </button>
        </div>
        
        <div className="text-sm text-gray-400">
          {photo.megapixels > 100 && (
            <span>Gigapixel mode: Up to {maxZoom}× zoom</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default GigapixelViewer;
