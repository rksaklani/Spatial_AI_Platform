/**
 * PhotoMetadataPanel Component
 * 
 * Displays EXIF metadata, GPS coordinates, and alignment status for photos
 * Requirements: F4
 */

import { useState } from 'react';
import { Button } from '../common';

interface PhotoMetadata {
  id: string;
  filename: string;
  captureDate?: string;
  camera?: string;
  lens?: string;
  focalLength?: number;
  aperture?: string;
  shutterSpeed?: string;
  iso?: number;
  width: number;
  height: number;
  fileSize: number;
  gps?: {
    latitude: number;
    longitude: number;
    altitude?: number;
  };
  alignment?: {
    status: 'pending' | 'processing' | 'aligned' | 'failed';
    confidence?: number;
    position?: [number, number, number];
    rotation?: [number, number, number];
  };
}

interface PhotoMetadataPanelProps {
  photo: PhotoMetadata;
  onAlign?: () => void;
  onClose?: () => void;
}

export function PhotoMetadataPanel({
  photo,
  onAlign,
  onClose,
}: PhotoMetadataPanelProps) {
  const [showMap, setShowMap] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const formatCoordinate = (value: number, isLatitude: boolean): string => {
    const abs = Math.abs(value);
    const degrees = Math.floor(abs);
    const minutes = Math.floor((abs - degrees) * 60);
    const seconds = ((abs - degrees - minutes / 60) * 3600).toFixed(2);
    const direction = isLatitude
      ? value >= 0 ? 'N' : 'S'
      : value >= 0 ? 'E' : 'W';
    return `${degrees}° ${minutes}' ${seconds}" ${direction}`;
  };

  const getAlignmentStatusColor = (status: string): string => {
    switch (status) {
      case 'aligned':
        return 'text-status-success';
      case 'processing':
        return 'text-status-warning';
      case 'failed':
        return 'text-status-error';
      default:
        return 'text-text-secondary';
    }
  };

  const getAlignmentStatusLabel = (status: string): string => {
    switch (status) {
      case 'aligned':
        return 'Aligned';
      case 'processing':
        return 'Processing...';
      case 'failed':
        return 'Failed';
      default:
        return 'Not Aligned';
    }
  };

  return (
    <div className="w-80 bg-surface-elevated border-l border-border-subtle h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-surface-elevated border-b border-border-subtle p-4 z-10">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-text-primary">
            Photo Details
          </h3>
          {onClose && (
            <button
              onClick={onClose}
              className="text-text-secondary hover:text-text-primary transition-colors"
              aria-label="Close panel"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <p className="text-xs text-text-secondary truncate" title={photo.filename}>
          {photo.filename}
        </p>
      </div>

      {/* Alignment Status */}
      {photo.alignment && (
        <div className="p-4 border-b border-border-subtle">
          <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-3">
            Alignment Status
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Status</span>
              <span className={`text-sm font-medium ${getAlignmentStatusColor(photo.alignment.status)}`}>
                {getAlignmentStatusLabel(photo.alignment.status)}
              </span>
            </div>
            {photo.alignment.confidence !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-primary">Confidence</span>
                <span className="text-sm text-text-secondary">
                  {(photo.alignment.confidence * 100).toFixed(1)}%
                </span>
              </div>
            )}
            {photo.alignment.position && (
              <div>
                <span className="text-sm text-text-primary block mb-1">Position</span>
                <span className="text-xs text-text-secondary font-mono">
                  X: {photo.alignment.position[0].toFixed(2)}<br />
                  Y: {photo.alignment.position[1].toFixed(2)}<br />
                  Z: {photo.alignment.position[2].toFixed(2)}
                </span>
              </div>
            )}
            {onAlign && photo.alignment.status !== 'processing' && (
              <Button
                variant="primary"
                size="sm"
                onClick={onAlign}
                className="w-full"
              >
                {photo.alignment.status === 'pending' ? 'Align Photo' : 'Re-align Photo'}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* GPS Location */}
      {photo.gps && (
        <div className="p-4 border-b border-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wide">
              GPS Location
            </h4>
            <button
              onClick={() => setShowMap(!showMap)}
              className="text-xs text-accent-primary hover:text-accent-hover transition-colors"
            >
              {showMap ? 'Hide Map' : 'Show Map'}
            </button>
          </div>
          <div className="space-y-2">
            <div>
              <span className="text-xs text-text-secondary block">Latitude</span>
              <span className="text-sm text-text-primary font-mono">
                {formatCoordinate(photo.gps.latitude, true)}
              </span>
            </div>
            <div>
              <span className="text-xs text-text-secondary block">Longitude</span>
              <span className="text-sm text-text-primary font-mono">
                {formatCoordinate(photo.gps.longitude, false)}
              </span>
            </div>
            {photo.gps.altitude !== undefined && (
              <div>
                <span className="text-xs text-text-secondary block">Altitude</span>
                <span className="text-sm text-text-primary">
                  {photo.gps.altitude.toFixed(1)} m
                </span>
              </div>
            )}
          </div>
          {showMap && (
            <div className="mt-3 bg-surface-base rounded border border-border-subtle overflow-hidden">
              <div className="aspect-video flex items-center justify-center text-text-tertiary">
                <div className="text-center">
                  <svg className="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  <p className="text-xs">Map view coming soon</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Camera Settings */}
      <div className="p-4 border-b border-border-subtle">
        <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-3">
          Camera Settings
        </h4>
        <div className="space-y-2">
          {photo.camera && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Camera</span>
              <span className="text-sm text-text-secondary">{photo.camera}</span>
            </div>
          )}
          {photo.lens && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Lens</span>
              <span className="text-sm text-text-secondary">{photo.lens}</span>
            </div>
          )}
          {photo.focalLength && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Focal Length</span>
              <span className="text-sm text-text-secondary">{photo.focalLength}mm</span>
            </div>
          )}
          {photo.aperture && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Aperture</span>
              <span className="text-sm text-text-secondary">{photo.aperture}</span>
            </div>
          )}
          {photo.shutterSpeed && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Shutter Speed</span>
              <span className="text-sm text-text-secondary">{photo.shutterSpeed}</span>
            </div>
          )}
          {photo.iso && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">ISO</span>
              <span className="text-sm text-text-secondary">{photo.iso}</span>
            </div>
          )}
        </div>
      </div>

      {/* File Information */}
      <div className="p-4">
        <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-3">
          File Information
        </h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-primary">Dimensions</span>
            <span className="text-sm text-text-secondary">
              {photo.width} × {photo.height}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-primary">File Size</span>
            <span className="text-sm text-text-secondary">
              {formatFileSize(photo.fileSize)}
            </span>
          </div>
          {photo.captureDate && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Captured</span>
              <span className="text-sm text-text-secondary">
                {new Date(photo.captureDate).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
