/**
 * Format Support Display Component
 * Shows all supported 3D file formats with icons and descriptions
 */

import React from 'react';

interface FormatInfo {
  extension: string;
  name: string;
  icon: string;
  category: 'mesh' | 'point_cloud' | 'gaussian' | 'bim';
  directPreview: boolean;
  description: string;
}

const SUPPORTED_FORMATS: FormatInfo[] = [
  // Mesh formats
  { extension: '.glb', name: 'glTF Binary', icon: '🔷', category: 'mesh', directPreview: true, description: 'Industry standard, best for web' },
  { extension: '.gltf', name: 'glTF JSON', icon: '🔷', category: 'mesh', directPreview: true, description: 'Text-based glTF format' },
  { extension: '.obj', name: 'Wavefront OBJ', icon: '🔷', category: 'mesh', directPreview: true, description: 'Legacy format with MTL support' },
  { extension: '.ply', name: 'Polygon File', icon: '🔷', category: 'mesh', directPreview: true, description: 'Point clouds and meshes' },
  { extension: '.stl', name: 'Stereolithography', icon: '🔷', category: 'mesh', directPreview: true, description: 'Popular for 3D printing' },
  { extension: '.fbx', name: 'Autodesk FBX', icon: '🔷', category: 'mesh', directPreview: true, description: 'Supports animations' },
  { extension: '.dae', name: 'COLLADA', icon: '🔷', category: 'mesh', directPreview: true, description: 'XML-based interchange format' },
  
  // Point cloud formats
  { extension: '.las', name: 'LAS Point Cloud', icon: '☁️', category: 'point_cloud', directPreview: false, description: 'Requires processing' },
  { extension: '.laz', name: 'LAZ Compressed', icon: '☁️', category: 'point_cloud', directPreview: false, description: 'Compressed LAS format' },
  { extension: '.e57', name: 'E57 3D Imaging', icon: '☁️', category: 'point_cloud', directPreview: false, description: 'ASTM standard format' },
  
  // Gaussian Splatting
  { extension: '.splat', name: 'Gaussian Splatting', icon: '✨', category: 'gaussian', directPreview: true, description: 'Neural rendering format' },
  
  // BIM
  { extension: '.ifc', name: 'IFC BIM Model', icon: '🏢', category: 'bim', directPreview: false, description: 'Building information modeling' },
];

const CATEGORY_LABELS = {
  mesh: 'Mesh Formats',
  point_cloud: 'Point Cloud Formats',
  gaussian: 'Gaussian Splatting',
  bim: 'BIM Formats',
};

export const FormatSupport: React.FC = () => {
  const groupedFormats = SUPPORTED_FORMATS.reduce((acc, format) => {
    if (!acc[format.category]) {
      acc[format.category] = [];
    }
    acc[format.category].push(format);
    return acc;
  }, {} as Record<string, FormatInfo[]>);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-text-primary mb-2">Supported Formats</h2>
        <p className="text-text-secondary">Upload any of these 3D file formats</p>
      </div>

      {Object.entries(groupedFormats).map(([category, formats]) => (
        <div key={category} className="space-y-3">
          <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <span>{formats[0].icon}</span>
            <span>{CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS]}</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {formats.map((format) => (
              <div
                key={format.extension}
                className="bg-surface-elevated border border-border-subtle rounded-lg p-4 hover:border-accent-primary transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{format.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-sm font-semibold text-accent-primary">
                        {format.extension}
                      </span>
                      {format.directPreview && (
                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                          Direct Preview
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-text-primary mb-1">
                      {format.name}
                    </p>
                    <p className="text-xs text-text-secondary">
                      {format.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="bg-surface-base border border-border-subtle rounded-lg p-4">
        <h4 className="text-sm font-semibold text-text-primary mb-2">📋 Quick Reference</h4>
        <div className="space-y-1 text-xs text-text-secondary">
          <p>• <span className="text-green-400">Direct Preview</span> - View immediately after upload</p>
          <p>• <span className="text-yellow-400">Requires Processing</span> - Converted to Gaussian Splatting</p>
          <p>• Maximum file size: 5GB</p>
          <p>• All formats support annotations and collaboration</p>
        </div>
      </div>
    </div>
  );
};

export default FormatSupport;
