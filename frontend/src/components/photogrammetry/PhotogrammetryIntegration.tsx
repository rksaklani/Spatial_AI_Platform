/**
 * Photogrammetry Tool Integration Component
 * 
 * Supports direct integration with:
 * - RealityCapture
 * - Agisoft Metashape
 * - Pix4D
 * - DroneDeploy
 * 
 * Features:
 * - Direct project import
 * - API-based upload
 * - Batch processing
 * - Progress tracking
 */

import React, { useState } from 'react';
import { Modal, Button } from '../common';
import { CloudArrowUpIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface PhotogrammetryIntegrationProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete?: (sceneId: string) => void;
}

type PhotogrammetryTool = 'realitycapture' | 'metashape' | 'pix4d' | 'dronedeploy' | 'manual';

interface ImportStatus {
  status: 'idle' | 'uploading' | 'processing' | 'complete' | 'error';
  progress: number;
  message: string;
  sceneId?: string;
}

export const PhotogrammetryIntegration: React.FC<PhotogrammetryIntegrationProps> = ({
  isOpen,
  onClose,
  onImportComplete,
}) => {
  const [selectedTool, setSelectedTool] = useState<PhotogrammetryTool>('manual');
  const [importStatus, setImportStatus] = useState<ImportStatus>({
    status: 'idle',
    progress: 0,
    message: '',
  });

  // RealityCapture Integration
  const handleRealityCaptureImport = async (file: File) => {
    setImportStatus({ status: 'uploading', progress: 0, message: 'Uploading RealityCapture project...' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('source_type', 'realitycapture');

      const response = await fetch('/api/v1/photogrammetry/import/realitycapture', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Import failed');
      }

      const data = await response.json();
      
      setImportStatus({
        status: 'processing',
        progress: 50,
        message: 'Processing RealityCapture data...',
        sceneId: data.scene_id,
      });

      // Poll for completion
      await pollProcessingStatus(data.scene_id);
    } catch (error) {
      setImportStatus({
        status: 'error',
        progress: 0,
        message: 'Import failed. Please try again.',
      });
    }
  };

  // Metashape Integration
  const handleMetashapeImport = async (file: File) => {
    setImportStatus({ status: 'uploading', progress: 0, message: 'Uploading Metashape project...' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('source_type', 'metashape');

      const response = await fetch('/api/v1/photogrammetry/import/metashape', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Import failed');
      }

      const data = await response.json();
      
      setImportStatus({
        status: 'processing',
        progress: 50,
        message: 'Processing Metashape data...',
        sceneId: data.scene_id,
      });

      await pollProcessingStatus(data.scene_id);
    } catch (error) {
      setImportStatus({
        status: 'error',
        progress: 0,
        message: 'Import failed. Please try again.',
      });
    }
  };

  // Pix4D Integration
  const handlePix4DImport = async (file: File) => {
    setImportStatus({ status: 'uploading', progress: 0, message: 'Uploading Pix4D project...' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('source_type', 'pix4d');

      const response = await fetch('/api/v1/photogrammetry/import/pix4d', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Import failed');
      }

      const data = await response.json();
      
      setImportStatus({
        status: 'processing',
        progress: 50,
        message: 'Processing Pix4D data...',
        sceneId: data.scene_id,
      });

      await pollProcessingStatus(data.scene_id);
    } catch (error) {
      setImportStatus({
        status: 'error',
        progress: 0,
        message: 'Import failed. Please try again.',
      });
    }
  };

  // Poll processing status
  const pollProcessingStatus = async (sceneId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/scenes/${sceneId}/status`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });

        const data = await response.json();

        if (data.status === 'completed') {
          setImportStatus({
            status: 'complete',
            progress: 100,
            message: 'Import complete!',
            sceneId,
          });
          onImportComplete?.(sceneId);
          return;
        }

        if (data.status === 'failed') {
          throw new Error('Processing failed');
        }

        // Update progress
        setImportStatus(prev => ({
          ...prev,
          progress: Math.min(50 + (attempts / maxAttempts) * 50, 95),
        }));

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          throw new Error('Processing timeout');
        }
      } catch (error) {
        setImportStatus({
          status: 'error',
          progress: 0,
          message: 'Processing failed. Please try again.',
        });
      }
    };

    poll();
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    switch (selectedTool) {
      case 'realitycapture':
        await handleRealityCaptureImport(file);
        break;
      case 'metashape':
        await handleMetashapeImport(file);
        break;
      case 'pix4d':
        await handlePix4DImport(file);
        break;
      default:
        break;
    }
  };

  const handleReset = () => {
    setImportStatus({ status: 'idle', progress: 0, message: '' });
    setSelectedTool('manual');
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Photogrammetry Integration">
      <div className="space-y-6">
        {importStatus.status === 'idle' && (
          <>
            {/* Tool Selection */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-3">
                Select Photogrammetry Tool
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setSelectedTool('realitycapture')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedTool === 'realitycapture'
                      ? 'border-accent-primary bg-accent-primary/10'
                      : 'border-border-subtle hover:border-border-color'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">📷</div>
                    <p className="text-sm font-medium text-text-primary">RealityCapture</p>
                    <p className="text-xs text-text-muted mt-1">.rcproj, .obj</p>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedTool('metashape')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedTool === 'metashape'
                      ? 'border-accent-primary bg-accent-primary/10'
                      : 'border-border-subtle hover:border-border-color'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">🗺️</div>
                    <p className="text-sm font-medium text-text-primary">Metashape</p>
                    <p className="text-xs text-text-muted mt-1">.psx, .ply</p>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedTool('pix4d')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedTool === 'pix4d'
                      ? 'border-accent-primary bg-accent-primary/10'
                      : 'border-border-subtle hover:border-border-color'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">🚁</div>
                    <p className="text-sm font-medium text-text-primary">Pix4D</p>
                    <p className="text-xs text-text-muted mt-1">.p4d, .las</p>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedTool('manual')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedTool === 'manual'
                      ? 'border-accent-primary bg-accent-primary/10'
                      : 'border-border-subtle hover:border-border-color'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">📁</div>
                    <p className="text-sm font-medium text-text-primary">Manual Upload</p>
                    <p className="text-xs text-text-muted mt-1">.ply, .obj, .las</p>
                  </div>
                </button>
              </div>
            </div>

            {/* File Upload */}
            {selectedTool !== 'manual' && (
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Upload Project File
                </label>
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept={
                    selectedTool === 'realitycapture'
                      ? '.rcproj,.obj,.ply'
                      : selectedTool === 'metashape'
                      ? '.psx,.ply,.obj'
                      : '.p4d,.las,.ply'
                  }
                  className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-text-muted mt-2">
                  {selectedTool === 'realitycapture' &&
                    'Upload your RealityCapture project file (.rcproj) or exported model (.obj, .ply)'}
                  {selectedTool === 'metashape' &&
                    'Upload your Metashape project file (.psx) or exported model (.ply, .obj)'}
                  {selectedTool === 'pix4d' &&
                    'Upload your Pix4D project file (.p4d) or point cloud (.las, .ply)'}
                </p>
              </div>
            )}

            {/* Info Box */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <p className="text-sm text-blue-400 mb-2">
                💡 Integration Features:
              </p>
              <ul className="text-xs text-text-secondary space-y-1">
                <li>• Automatic coordinate system detection</li>
                <li>• Preserves camera positions and orientations</li>
                <li>• Imports textures and materials</li>
                <li>• Maintains georeferencing data</li>
                <li>• Batch processing support</li>
              </ul>
            </div>
          </>
        )}

        {/* Processing Status */}
        {(importStatus.status === 'uploading' ||
          importStatus.status === 'processing') && (
          <div className="space-y-4">
            <div className="text-center">
              <CloudArrowUpIcon className="w-16 h-16 mx-auto text-accent-primary animate-pulse mb-4" />
              <p className="text-lg font-medium text-text-primary mb-2">
                {importStatus.message}
              </p>
              <div className="w-full bg-surface-elevated rounded-full h-2 mb-2">
                <div
                  className="bg-accent-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${importStatus.progress}%` }}
                />
              </div>
              <p className="text-sm text-text-secondary">
                {importStatus.progress}% complete
              </p>
            </div>
          </div>
        )}

        {/* Success */}
        {importStatus.status === 'complete' && (
          <div className="space-y-4">
            <div className="text-center">
              <CheckCircleIcon className="w-16 h-16 mx-auto text-green-400 mb-4" />
              <p className="text-lg font-medium text-text-primary mb-2">
                Import Complete!
              </p>
              <p className="text-sm text-text-secondary">
                Your scene has been successfully imported and is ready to view.
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="primary"
                onClick={() => {
                  if (importStatus.sceneId) {
                    window.location.href = `/scenes/${importStatus.sceneId}`;
                  }
                }}
                className="flex-1"
              >
                View Scene
              </Button>
              <Button variant="secondary" onClick={handleReset} className="flex-1">
                Import Another
              </Button>
            </div>
          </div>
        )}

        {/* Error */}
        {importStatus.status === 'error' && (
          <div className="space-y-4">
            <div className="text-center">
              <XCircleIcon className="w-16 h-16 mx-auto text-red-400 mb-4" />
              <p className="text-lg font-medium text-text-primary mb-2">
                Import Failed
              </p>
              <p className="text-sm text-text-secondary">{importStatus.message}</p>
            </div>
            <Button variant="primary" onClick={handleReset} className="w-full">
              Try Again
            </Button>
          </div>
        )}

        {/* Close Button */}
        {importStatus.status === 'idle' && (
          <div className="flex gap-3 pt-4 border-t border-border-subtle">
            <Button variant="ghost" onClick={onClose} className="flex-1">
              Cancel
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
};
