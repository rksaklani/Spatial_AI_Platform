/**
 * Type definitions for 3D scene data structures
 */

export interface BoundingBox {
  min: [number, number, number];
  max: [number, number, number];
}

export interface SceneMetadata {
  sceneId: string;
  organizationId: string;
  userId: string;
  name: string;
  sourceType: 'video' | 'import';
  sourceFormat: string;
  format?: 'glb' | 'gltf' | 'obj' | 'ply' | 'splat' | 'las' | 'e57' | 'fbx' | 'dae' | 'stl' | 'ifc' | 'dxf';
  fileUrl?: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  bounds: BoundingBox;
  tileCount: number;
  gaussianCount: number;
  captureDate?: string;
  processingTime?: number;
  createdAt: string;
  updatedAt: string;
}

export interface SceneTile {
  tileId: string;
  url: string;
  lod: 'high' | 'medium' | 'low';
  priority: number;
  distance?: number;
  bounds?: BoundingBox;
  gaussianCount?: number;
}
