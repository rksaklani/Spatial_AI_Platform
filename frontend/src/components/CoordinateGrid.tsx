/**
 * Coordinate Grid Overlay Component
 * 
 * Displays a coordinate grid overlay in the 3D scene.
 * Shows grid lines with coordinate labels.
 */

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface CoordinateGridProps {
  scene: THREE.Scene;
  size?: number;
  divisions?: number;
  color?: string;
  visible?: boolean;
}

const CoordinateGrid: React.FC<CoordinateGridProps> = ({
  scene,
  size = 100,
  divisions = 10,
  color = '#888888',
  visible = true,
}) => {
  const gridRef = useRef<THREE.GridHelper | null>(null);
  const axesRef = useRef<THREE.AxesHelper | null>(null);

  useEffect(() => {
    if (!scene) return;

    // Create grid helper
    const grid = new THREE.GridHelper(size, divisions, color, color);
    grid.visible = visible;
    gridRef.current = grid;
    scene.add(grid);

    // Create axes helper (X=red, Y=green, Z=blue)
    const axes = new THREE.AxesHelper(size / 2);
    axes.visible = visible;
    axesRef.current = axes;
    scene.add(axes);

    // Cleanup
    return () => {
      if (gridRef.current) {
        scene.remove(gridRef.current);
        gridRef.current.geometry.dispose();
        if (gridRef.current.material instanceof THREE.Material) {
          gridRef.current.material.dispose();
        }
      }
      if (axesRef.current) {
        scene.remove(axesRef.current);
        axesRef.current.geometry.dispose();
        if (axesRef.current.material instanceof THREE.Material) {
          axesRef.current.material.dispose();
        }
      }
    };
  }, [scene, size, divisions, color]);

  useEffect(() => {
    if (gridRef.current) {
      gridRef.current.visible = visible;
    }
    if (axesRef.current) {
      axesRef.current.visible = visible;
    }
  }, [visible]);

  return null; // This component doesn't render DOM elements
};

export default CoordinateGrid;
