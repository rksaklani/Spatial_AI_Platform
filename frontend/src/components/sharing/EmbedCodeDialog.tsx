/**
 * Embed Code Dialog Component
 * 
 * Generates iframe embed code for scenes
 * Allows customization of viewer appearance and features
 */

import React, { useState } from 'react';
import { Modal, Button } from '../common';
import { CodeBracketIcon, ClipboardDocumentIcon, CheckIcon } from '@heroicons/react/24/outline';

interface EmbedCodeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  sceneId: string;
  sceneName: string;
}

export const EmbedCodeDialog: React.FC<EmbedCodeDialogProps> = ({
  isOpen,
  onClose,
  sceneId,
  sceneName,
}) => {
  const [width, setWidth] = useState('100%');
  const [height, setHeight] = useState('600px');
  const [showControls, setShowControls] = useState(true);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [showMeasurements, setShowMeasurements] = useState(true);
  const [autoRotate, setAutoRotate] = useState(false);
  const [copied, setCopied] = useState(false);

  const generateEmbedCode = () => {
    const baseUrl = window.location.origin;
    const params = new URLSearchParams({
      controls: showControls.toString(),
      annotations: showAnnotations.toString(),
      measurements: showMeasurements.toString(),
      autoRotate: autoRotate.toString(),
    });

    return `<iframe
  src="${baseUrl}/embed/scenes/${sceneId}?${params.toString()}"
  width="${width}"
  height="${height}"
  frameborder="0"
  allowfullscreen
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  title="${sceneName}"
></iframe>`;
  };

  const embedCode = generateEmbedCode();

  const handleCopy = () => {
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Embed Scene">
      <div className="space-y-6">
        {/* Scene Info */}
        <div className="bg-surface-elevated rounded-lg p-4">
          <p className="text-sm text-text-secondary">Scene</p>
          <p className="text-lg font-semibold text-text-primary">{sceneName}</p>
        </div>

        {/* Dimensions */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="width" className="block text-sm font-medium text-text-primary mb-2">
              Width
            </label>
            <input
              type="text"
              id="width"
              value={width}
              onChange={(e) => setWidth(e.target.value)}
              className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="100%"
            />
          </div>
          <div>
            <label htmlFor="height" className="block text-sm font-medium text-text-primary mb-2">
              Height
            </label>
            <input
              type="text"
              id="height"
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="600px"
            />
          </div>
        </div>

        {/* Options */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-text-primary">Viewer Options</p>
          
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={showControls}
              onChange={(e) => setShowControls(e.target.checked)}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Show camera controls</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={showAnnotations}
              onChange={(e) => setShowAnnotations(e.target.checked)}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Show annotations</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={showMeasurements}
              onChange={(e) => setShowMeasurements(e.target.checked)}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Show measurements</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRotate}
              onChange={(e) => setAutoRotate(e.target.checked)}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Auto-rotate camera</span>
          </label>
        </div>

        {/* Embed Code */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-text-primary">
              Embed Code
            </label>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              icon={copied ? <CheckIcon className="w-4 h-4" /> : <ClipboardDocumentIcon className="w-4 h-4" />}
            >
              {copied ? 'Copied!' : 'Copy'}
            </Button>
          </div>
          <div className="relative">
            <pre className="bg-surface-elevated border border-border-subtle rounded-lg p-4 text-xs text-text-primary font-mono overflow-x-auto max-h-48">
              {embedCode}
            </pre>
          </div>
        </div>

        {/* Preview */}
        <div>
          <p className="text-sm font-medium text-text-primary mb-2">Preview</p>
          <div className="bg-surface-elevated border border-border-subtle rounded-lg p-4">
            <div 
              className="bg-primary-bg rounded flex items-center justify-center text-text-muted"
              style={{ width: '100%', height: '200px' }}
            >
              <div className="text-center">
                <CodeBracketIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Embed Preview</p>
                <p className="text-xs mt-1">{width} × {height}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <p className="text-sm text-blue-400">
            💡 Tip: Paste this code into your website's HTML to embed the 3D viewer
          </p>
        </div>

        {/* Close Button */}
        <div className="flex gap-3 pt-4 border-t border-border-subtle">
          <Button variant="ghost" onClick={onClose} className="flex-1">
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};
