/**
 * Orthophoto Controls Component
 * 
 * Provides UI controls for managing orthophotos:
 * - Upload new orthophotos
 * - Adjust opacity (0-100%)
 * - Toggle visibility
 * - Adjust layer ordering
 */

import React, { useState } from 'react';

interface Orthophoto {
  id: string;
  name: string;
  opacity: number;
  visible: boolean;
  layer_order: number;
}

interface OrthophotoControlsProps {
  sceneId: string;
  orthophotos: Orthophoto[];
  onOrthophotoUpdate?: (orthophotoId: string, updates: Partial<Orthophoto>) => void;
  onOrthophotoUpload?: () => void;
}

const OrthophotoControls: React.FC<OrthophotoControlsProps> = ({
  sceneId,
  orthophotos,
  onOrthophotoUpdate,
  onOrthophotoUpload,
}) => {
  const [uploading, setUploading] = useState(false);

  const handleOpacityChange = async (orthophotoId: string, opacity: number) => {
    try {
      const response = await fetch(`/api/v1/orthophotos/${orthophotoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ opacity: opacity / 100 }),
      });

      if (response.ok && onOrthophotoUpdate) {
        onOrthophotoUpdate(orthophotoId, { opacity: opacity / 100 });
      }
    } catch (error) {
      console.error('Error updating opacity:', error);
    }
  };

  const handleVisibilityToggle = async (orthophotoId: string, visible: boolean) => {
    try {
      const response = await fetch(`/api/v1/orthophotos/${orthophotoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ visible }),
      });

      if (response.ok && onOrthophotoUpdate) {
        onOrthophotoUpdate(orthophotoId, { visible });
      }
    } catch (error) {
      console.error('Error toggling visibility:', error);
    }
  };

  const handleLayerOrderChange = async (orthophotoId: string, layerOrder: number) => {
    try {
      const response = await fetch(`/api/v1/orthophotos/${orthophotoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ layer_order: layerOrder }),
      });

      if (response.ok && onOrthophotoUpdate) {
        onOrthophotoUpdate(orthophotoId, { layer_order: layerOrder });
      }
    } catch (error) {
      console.error('Error updating layer order:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('scene_id', sceneId);
      formData.append('name', file.name);

      const response = await fetch('/api/v1/orthophotos/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (response.ok && onOrthophotoUpload) {
        onOrthophotoUpload();
      }
    } catch (error) {
      console.error('Error uploading orthophoto:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="orthophoto-controls">
      <div className="controls-header">
        <h3>Orthophotos</h3>
        <label className="upload-button">
          <input
            type="file"
            accept=".tif,.tiff,.jp2,.j2k,.ecw"
            onChange={handleFileUpload}
            disabled={uploading}
            style={{ display: 'none' }}
          />
          <button disabled={uploading}>
            {uploading ? 'Uploading...' : '+ Upload'}
          </button>
        </label>
      </div>

      <div className="orthophoto-list">
        {orthophotos.length === 0 ? (
          <div className="no-orthophotos">
            No orthophotos uploaded
          </div>
        ) : (
          orthophotos.map((orthophoto) => (
            <div key={orthophoto.id} className="orthophoto-item">
              <div className="orthophoto-header">
                <label className="visibility-toggle">
                  <input
                    type="checkbox"
                    checked={orthophoto.visible}
                    onChange={(e) =>
                      handleVisibilityToggle(orthophoto.id, e.target.checked)
                    }
                  />
                  <span>{orthophoto.name}</span>
                </label>
              </div>

              <div className="orthophoto-controls-row">
                <label className="control-label">
                  Opacity: {Math.round(orthophoto.opacity * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={Math.round(orthophoto.opacity * 100)}
                  onChange={(e) =>
                    handleOpacityChange(orthophoto.id, parseInt(e.target.value))
                  }
                  className="opacity-slider"
                />
              </div>

              <div className="orthophoto-controls-row">
                <label className="control-label">Layer Order:</label>
                <input
                  type="number"
                  value={orthophoto.layer_order}
                  onChange={(e) =>
                    handleLayerOrderChange(orthophoto.id, parseInt(e.target.value))
                  }
                  className="layer-order-input"
                />
              </div>
            </div>
          ))
        )}
      </div>

      <style jsx>{`
        .orthophoto-controls {
          position: absolute;
          bottom: 20px;
          left: 20px;
          background: rgba(255, 255, 255, 0.95);
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
          min-width: 300px;
          max-width: 400px;
          max-height: 500px;
          overflow-y: auto;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .controls-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .controls-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }

        .upload-button button {
          padding: 6px 12px;
          background: #2196f3;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .upload-button button:hover:not(:disabled) {
          background: #1976d2;
        }

        .upload-button button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .orthophoto-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .no-orthophotos {
          padding: 20px;
          text-align: center;
          color: #999;
          font-size: 13px;
        }

        .orthophoto-item {
          padding: 12px;
          background: #f5f5f5;
          border-radius: 6px;
          border: 1px solid #e0e0e0;
        }

        .orthophoto-header {
          margin-bottom: 8px;
        }

        .visibility-toggle {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 500;
          color: #333;
          cursor: pointer;
        }

        .visibility-toggle input[type="checkbox"] {
          cursor: pointer;
        }

        .orthophoto-controls-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 8px;
        }

        .control-label {
          font-size: 12px;
          color: #666;
          min-width: 80px;
        }

        .opacity-slider {
          flex: 1;
          cursor: pointer;
        }

        .layer-order-input {
          width: 60px;
          padding: 4px 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 13px;
        }
      `}</style>
    </div>
  );
};

export default OrthophotoControls;
