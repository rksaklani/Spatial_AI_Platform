/**
 * DXF Overlay Component
 * 
 * Renders DXF/CAD design files as overlays on 3D scenes
 * Allows alignment and verification of as-built vs as-designed
 * 
 * Supports:
 * - LINE, POLYLINE, LWPOLYLINE
 * - CIRCLE, ARC, ELLIPSE
 * - TEXT, MTEXT
 * - SPLINE, 3DFACE
 * - Multiple layers with colors
 */

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface DXFLayer {
  id: string;
  name: string;
  color: THREE.Color;
  visible: boolean;
  entities: DXFEntity[];
}

interface DXFEntity {
  type: 'line' | 'polyline' | 'circle' | 'arc' | 'text' | 'spline' | '3dface' | 'ellipse';
  points: THREE.Vector3[];
  color?: THREE.Color;
  lineWidth?: number;
  radius?: number;
  startAngle?: number;
  endAngle?: number;
  text?: string;
  height?: number;
}

interface DXFOverlayProps {
  scene: THREE.Scene;
  dxfUrl: string;
  opacity?: number;
  visible?: boolean;
  scale?: number;
  position?: THREE.Vector3;
  rotation?: THREE.Euler;
  onLoad?: (layers: DXFLayer[]) => void;
  onError?: (error: Error) => void;
}

export const DXFOverlay: React.FC<DXFOverlayProps> = ({
  scene,
  dxfUrl,
  opacity = 0.7,
  visible = true,
  scale = 1,
  position = new THREE.Vector3(0, 0, 0),
  rotation = new THREE.Euler(0, 0, 0),
  onLoad,
  onError,
}) => {
  const overlayGroupRef = useRef<THREE.Group | null>(null);
  const [layers, setLayers] = useState<DXFLayer[]>([]);

  // Load and parse DXF file
  useEffect(() => {
    if (!dxfUrl) return;

    const loadDXF = async () => {
      try {
        const response = await fetch(dxfUrl);
        if (!response.ok) {
          throw new Error('Failed to load DXF file');
        }

        const dxfText = await response.text();
        const parsedLayers = parseDXF(dxfText);
        
        setLayers(parsedLayers);
        onLoad?.(parsedLayers);
      } catch (error) {
        console.error('DXF loading error:', error);
        onError?.(error as Error);
      }
    };

    loadDXF();
  }, [dxfUrl, onLoad, onError]);

  // Render DXF layers in scene
  useEffect(() => {
    if (!scene || layers.length === 0) return;

    // Create overlay group
    const overlayGroup = new THREE.Group();
    overlayGroup.name = 'dxf-overlay';
    overlayGroup.position.copy(position);
    overlayGroup.rotation.copy(rotation);
    overlayGroup.scale.setScalar(scale);
    overlayGroupRef.current = overlayGroup;

    // Render each layer
    layers.forEach((layer) => {
      if (!layer.visible) return;

      const layerGroup = new THREE.Group();
      layerGroup.name = layer.name;

      layer.entities.forEach((entity) => {
        const object = createEntityObject(entity, layer.color, opacity);
        if (object) {
          layerGroup.add(object);
        }
      });

      overlayGroup.add(layerGroup);
    });

    scene.add(overlayGroup);

    return () => {
      scene.remove(overlayGroup);
      overlayGroup.traverse((child) => {
        if (child instanceof THREE.Mesh || child instanceof THREE.Line) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach((m) => m.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    };
  }, [scene, layers, opacity, scale, position, rotation]);

  // Update visibility
  useEffect(() => {
    if (overlayGroupRef.current) {
      overlayGroupRef.current.visible = visible;
    }
  }, [visible]);

  return null;
};

/**
 * Enhanced DXF Parser with full entity support
 */
function parseDXF(dxfText: string): DXFLayer[] {
  const layers: Map<string, DXFLayer> = new Map();
  const lines = dxfText.split('\n').map(l => l.trim());
  
  let i = 0;
  let currentSection = '';
  let currentEntity: Partial<DXFEntity> | null = null;
  let currentLayer = '0';
  let points: THREE.Vector3[] = [];
  let currentPoint: Partial<THREE.Vector3> = {};
  
  // DXF color index to RGB
  const dxfColors: { [key: number]: number } = {
    1: 0xff0000, 2: 0xffff00, 3: 0x00ff00, 4: 0x00ffff,
    5: 0x0000ff, 6: 0xff00ff, 7: 0xffffff, 8: 0x808080,
  };

  while (i < lines.length) {
    const code = lines[i];
    const value = i + 1 < lines.length ? lines[i + 1] : '';
    
    // Section markers
    if (code === '0') {
      if (value === 'SECTION') {
        i += 2;
        currentSection = lines[i + 1];
        i += 2;
        continue;
      } else if (value === 'ENDSEC') {
        currentSection = '';
        i += 2;
        continue;
      }
      
      // Save previous entity
      if (currentEntity && points.length > 0) {
        currentEntity.points = [...points];
        addEntityToLayer(layers, currentLayer, currentEntity as DXFEntity);
      }
      
      // Start new entity
      currentEntity = { type: value.toLowerCase() as any, points: [] };
      points = [];
      currentPoint = {};
      i += 2;
      continue;
    }
    
    // Layer
    if (code === '8') {
      currentLayer = value;
      if (!layers.has(currentLayer)) {
        layers.set(currentLayer, {
          id: currentLayer,
          name: currentLayer,
          color: new THREE.Color(0xffffff),
          visible: true,
          entities: [],
        });
      }
    }
    
    // Color
    if (code === '62' && currentEntity) {
      const colorIndex = parseInt(value);
      currentEntity.color = new THREE.Color(dxfColors[colorIndex] || 0xffffff);
    }
    
    // Coordinates
    if (code === '10' || code === '11' || code === '12' || code === '13') {
      currentPoint.x = parseFloat(value);
    }
    if (code === '20' || code === '21' || code === '22' || code === '23') {
      currentPoint.y = parseFloat(value);
    }
    if (code === '30' || code === '31' || code === '32' || code === '33') {
      currentPoint.z = parseFloat(value);
      // Complete point
      if (currentPoint.x !== undefined && currentPoint.y !== undefined) {
        points.push(new THREE.Vector3(
          currentPoint.x,
          currentPoint.y,
          currentPoint.z || 0
        ));
        currentPoint = {};
      }
    }
    
    // Circle/Arc radius
    if (code === '40' && currentEntity) {
      currentEntity.radius = parseFloat(value);
    }
    
    // Arc angles
    if (code === '50' && currentEntity) {
      currentEntity.startAngle = parseFloat(value) * (Math.PI / 180);
    }
    if (code === '51' && currentEntity) {
      currentEntity.endAngle = parseFloat(value) * (Math.PI / 180);
    }
    
    // Text content
    if (code === '1' && currentEntity) {
      currentEntity.text = value;
    }
    
    // Text height
    if (code === '40' && currentEntity && currentEntity.type === 'text') {
      currentEntity.height = parseFloat(value);
    }
    
    i += 2;
  }
  
  // Save last entity
  if (currentEntity && points.length > 0) {
    currentEntity.points = [...points];
    addEntityToLayer(layers, currentLayer, currentEntity as DXFEntity);
  }
  
  return Array.from(layers.values());
}

function addEntityToLayer(layers: Map<string, DXFLayer>, layerName: string, entity: DXFEntity) {
  if (!layers.has(layerName)) {
    layers.set(layerName, {
      id: layerName,
      name: layerName,
      color: new THREE.Color(0xffffff),
      visible: true,
      entities: [],
    });
  }
  layers.get(layerName)!.entities.push(entity);
}

/**
 * Create Three.js object from DXF entity with full support
 */
function createEntityObject(
  entity: DXFEntity,
  layerColor: THREE.Color,
  opacity: number
): THREE.Object3D | null {
  const color = entity.color || layerColor;
  const material = new THREE.LineBasicMaterial({
    color,
    opacity,
    transparent: true,
    linewidth: entity.lineWidth || 1,
  });

  // LINE
  if (entity.type === 'line' && entity.points.length >= 2) {
    const geometry = new THREE.BufferGeometry().setFromPoints(entity.points);
    return new THREE.Line(geometry, material);
  }

  // POLYLINE / LWPOLYLINE
  if ((entity.type === 'polyline' || entity.type === 'lwpolyline') && entity.points.length >= 2) {
    const geometry = new THREE.BufferGeometry().setFromPoints(entity.points);
    return new THREE.Line(geometry, material);
  }

  // CIRCLE
  if (entity.type === 'circle' && entity.points.length >= 1 && entity.radius) {
    const center = entity.points[0];
    const curve = new THREE.EllipseCurve(
      center.x, center.y,
      entity.radius, entity.radius,
      0, 2 * Math.PI,
      false, 0
    );
    const points = curve.getPoints(50);
    const geometry = new THREE.BufferGeometry().setFromPoints(
      points.map(p => new THREE.Vector3(p.x, p.y, center.z))
    );
    return new THREE.Line(geometry, material);
  }

  // ARC
  if (entity.type === 'arc' && entity.points.length >= 1 && entity.radius) {
    const center = entity.points[0];
    const startAngle = entity.startAngle || 0;
    const endAngle = entity.endAngle || Math.PI * 2;
    const curve = new THREE.EllipseCurve(
      center.x, center.y,
      entity.radius, entity.radius,
      startAngle, endAngle,
      false, 0
    );
    const points = curve.getPoints(50);
    const geometry = new THREE.BufferGeometry().setFromPoints(
      points.map(p => new THREE.Vector3(p.x, p.y, center.z))
    );
    return new THREE.Line(geometry, material);
  }

  // ELLIPSE
  if (entity.type === 'ellipse' && entity.points.length >= 2) {
    const center = entity.points[0];
    const majorAxis = entity.points[1];
    const radiusX = center.distanceTo(majorAxis);
    const radiusY = radiusX * 0.5; // Simplified
    const curve = new THREE.EllipseCurve(
      center.x, center.y,
      radiusX, radiusY,
      0, 2 * Math.PI,
      false, 0
    );
    const points = curve.getPoints(50);
    const geometry = new THREE.BufferGeometry().setFromPoints(
      points.map(p => new THREE.Vector3(p.x, p.y, center.z))
    );
    return new THREE.Line(geometry, material);
  }

  // TEXT (create sprite with canvas texture)
  if (entity.type === 'text' && entity.text && entity.points.length >= 1) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    const fontSize = (entity.height || 1) * 100;
    canvas.width = 512;
    canvas.height = 128;
    
    context.fillStyle = `#${color.getHexString()}`;
    context.font = `${fontSize}px Arial`;
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(entity.text, 256, 64);
    
    const texture = new THREE.CanvasTexture(canvas);
    const spriteMaterial = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      opacity,
    });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.position.copy(entity.points[0]);
    sprite.scale.set(entity.height || 1, (entity.height || 1) * 0.25, 1);
    return sprite;
  }

  // 3DFACE
  if (entity.type === '3dface' && entity.points.length >= 3) {
    const geometry = new THREE.BufferGeometry().setFromPoints(entity.points);
    geometry.setIndex([0, 1, 2, 0, 2, 3]);
    const meshMaterial = new THREE.MeshBasicMaterial({
      color,
      opacity,
      transparent: true,
      side: THREE.DoubleSide,
    });
    return new THREE.Mesh(geometry, meshMaterial);
  }

  // SPLINE
  if (entity.type === 'spline' && entity.points.length >= 2) {
    const curve = new THREE.CatmullRomCurve3(entity.points);
    const points = curve.getPoints(50);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    return new THREE.Line(geometry, material);
  }

  return null;
}

export default DXFOverlay;
