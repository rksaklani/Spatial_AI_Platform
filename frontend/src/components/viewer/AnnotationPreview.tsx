/**
 * AnnotationPreview Component
 * 
 * Renders preview lines/areas while creating multi-point annotations
 */

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Position3D {
  x: number;
  y: number;
  z: number;
}

interface AnnotationPreviewProps {
  scene: THREE.Scene | null;
  points: Position3D[];
  previewPoints: Position3D[];
  type: 'line' | 'area' | null;
  color: string;
}

export function AnnotationPreview({
  scene,
  points,
  previewPoints,
  type,
  color,
}: AnnotationPreviewProps) {
  const previewLineRef = useRef<THREE.Line | null>(null);

  useEffect(() => {
    if (!scene || !type || previewPoints.length < 2) {
      // Remove preview line if it exists
      if (previewLineRef.current) {
        scene.remove(previewLineRef.current);
        previewLineRef.current.geometry.dispose();
        (previewLineRef.current.material as THREE.Material).dispose();
        previewLineRef.current = null;
      }
      return;
    }

    // Create or update preview line
    const positions: number[] = [];
    previewPoints.forEach((p) => {
      positions.push(p.x, p.y, p.z);
    });

    // Close polygon for area
    if (type === 'area' && previewPoints.length > 2) {
      positions.push(previewPoints[0].x, previewPoints[0].y, previewPoints[0].z);
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));

    const material = new THREE.LineBasicMaterial({
      color: new THREE.Color(color),
      linewidth: 2,
      opacity: 0.8,
      transparent: true,
      depthTest: false,
    });

    // Remove old preview line
    if (previewLineRef.current) {
      scene.remove(previewLineRef.current);
      previewLineRef.current.geometry.dispose();
      (previewLineRef.current.material as THREE.Material).dispose();
    }

    // Add new preview line
    const line = new THREE.Line(geometry, material);
    line.renderOrder = 999; // Render on top
    scene.add(line);
    previewLineRef.current = line;

    return () => {
      if (previewLineRef.current) {
        scene.remove(previewLineRef.current);
        previewLineRef.current.geometry.dispose();
        (previewLineRef.current.material as THREE.Material).dispose();
        previewLineRef.current = null;
      }
    };
  }, [scene, previewPoints, type, color]);

  return null;
}
