/**
 * Hook for managing annotation creation in 3D viewer
 * Handles raycasting, point collection, and annotation submission
 */

import { useCallback, useState, useRef } from 'react';
import * as THREE from 'three';
import { useCreateAnnotationMutation } from '../store/api/annotationApi';

export type AnnotationType = 'point' | 'line' | 'area' | 'text';
export type AnnotationMode = 'view' | 'create' | 'edit';

interface Position3D {
  x: number;
  y: number;
  z: number;
}

interface UseAnnotationCreationProps {
  sceneId: string;
  scene: THREE.Scene | null;
  camera: THREE.Camera | null;
  mode: AnnotationMode;
  selectedType: AnnotationType | null;
  color: string;
  onAnnotationCreated?: () => void;
}

export function useAnnotationCreation({
  sceneId,
  scene,
  camera,
  mode,
  selectedType,
  color,
  onAnnotationCreated,
}: UseAnnotationCreationProps) {
  const [createAnnotation] = useCreateAnnotationMutation();
  const [points, setPoints] = useState<Position3D[]>([]);
  const [previewPoints, setPreviewPoints] = useState<Position3D[]>([]);
  const raycasterRef = useRef(new THREE.Raycaster());
  const tempMarkersRef = useRef<THREE.Object3D[]>([]);

  // Perform raycasting to get 3D position from mouse click
  const raycast = useCallback(
    (event: MouseEvent, domElement: HTMLElement): Position3D | null => {
      if (!scene || !camera) return null;

      const rect = domElement.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      const mouse = new THREE.Vector2(x, y);
      raycasterRef.current.setFromCamera(mouse, camera);

      // Raycast against all objects in the scene
      const intersects = raycasterRef.current.intersectObjects(scene.children, true);

      if (intersects.length > 0) {
        const point = intersects[0].point;
        return { x: point.x, y: point.y, z: point.z };
      }

      return null;
    },
    [scene, camera]
  );

  // Add temporary marker for visual feedback
  const addTempMarker = useCallback(
    (position: Position3D) => {
      if (!scene) return;

      const geometry = new THREE.SphereGeometry(0.1);
      const material = new THREE.MeshBasicMaterial({
        color: color,
        opacity: 0.8,
        transparent: true,
      });
      const marker = new THREE.Mesh(geometry, material);
      marker.position.set(position.x, position.y, position.z);
      scene.add(marker);
      tempMarkersRef.current.push(marker);
    },
    [scene, color]
  );

  // Clear temporary markers
  const clearTempMarkers = useCallback(() => {
    if (!scene) return;

    tempMarkersRef.current.forEach((marker) => {
      scene.remove(marker);
      if (marker instanceof THREE.Mesh) {
        marker.geometry.dispose();
        if (Array.isArray(marker.material)) {
          marker.material.forEach((m) => m.dispose());
        } else {
          marker.material.dispose();
        }
      }
    });
    tempMarkersRef.current = [];
  }, [scene]);

  // Handle click event for annotation creation
  const handleClick = useCallback(
    async (event: MouseEvent, domElement: HTMLElement) => {
      if (mode !== 'create' || !selectedType) return;

      const position = raycast(event, domElement);
      if (!position) return;

      if (selectedType === 'point') {
        // Point annotation: single click creates annotation
        try {
          await createAnnotation({
            sceneId,
            type: 'marker',
            position: [position.x, position.y, position.z],
            content: 'Point annotation',
            metadata: { color },
          }).unwrap();
          onAnnotationCreated?.();
        } catch (error) {
          console.error('Failed to create point annotation:', error);
        }
      } else if (selectedType === 'text') {
        // Text annotation: show input dialog
        const text = prompt('Enter annotation text:');
        if (text) {
          try {
            await createAnnotation({
              sceneId,
              type: 'comment',
              position: [position.x, position.y, position.z],
              content: text,
              metadata: { color },
            }).unwrap();
            onAnnotationCreated?.();
          } catch (error) {
            console.error('Failed to create text annotation:', error);
          }
        }
      } else if (selectedType === 'line' || selectedType === 'area') {
        // Multi-point annotation: collect points
        const newPoints = [...points, position];
        setPoints(newPoints);
        addTempMarker(position);
      }
    },
    [
      mode,
      selectedType,
      raycast,
      points,
      createAnnotation,
      sceneId,
      color,
      onAnnotationCreated,
      addTempMarker,
    ]
  );

  // Handle double-click to finish multi-point annotation
  const handleDoubleClick = useCallback(
    async (event: MouseEvent, domElement: HTMLElement) => {
      if (mode !== 'create' || !selectedType) return;
      if (selectedType !== 'line' && selectedType !== 'area') return;

      event.preventDefault();

      const position = raycast(event, domElement);
      if (!position) return;

      const finalPoints = [...points, position];

      if (finalPoints.length < 2) {
        alert('Need at least 2 points for line/area annotation');
        return;
      }

      try {
        if (selectedType === 'line') {
          // Calculate line length
          let distance = 0;
          for (let i = 0; i < finalPoints.length - 1; i++) {
            const p1 = finalPoints[i];
            const p2 = finalPoints[i + 1];
            distance += Math.sqrt(
              Math.pow(p2.x - p1.x, 2) +
              Math.pow(p2.y - p1.y, 2) +
              Math.pow(p2.z - p1.z, 2)
            );
          }

          await createAnnotation({
            sceneId,
            type: 'measurement',
            position: [finalPoints[0].x, finalPoints[0].y, finalPoints[0].z],
            content: `Line: ${distance.toFixed(2)}m`,
            metadata: {
              distance,
              points: finalPoints.map((p) => [p.x, p.y, p.z] as [number, number, number]),
              color,
            },
          }).unwrap();
        } else if (selectedType === 'area') {
          // Calculate area (simplified - assumes planar polygon)
          let area = 0;
          for (let i = 0; i < finalPoints.length; i++) {
            const p1 = finalPoints[i];
            const p2 = finalPoints[(i + 1) % finalPoints.length];
            area += p1.x * p2.y - p2.x * p1.y;
          }
          area = Math.abs(area) / 2;

          await createAnnotation({
            sceneId,
            type: 'measurement',
            position: [finalPoints[0].x, finalPoints[0].y, finalPoints[0].z],
            content: `Area: ${area.toFixed(2)}m²`,
            metadata: {
              area,
              points: finalPoints.map((p) => [p.x, p.y, p.z] as [number, number, number]),
              color,
            },
          }).unwrap();
        }

        // Clear state
        setPoints([]);
        clearTempMarkers();
        onAnnotationCreated?.();
      } catch (error) {
        console.error('Failed to create annotation:', error);
      }
    },
    [
      mode,
      selectedType,
      raycast,
      points,
      createAnnotation,
      sceneId,
      color,
      clearTempMarkers,
      onAnnotationCreated,
    ]
  );

  // Handle mouse move for preview
  const handleMouseMove = useCallback(
    (event: MouseEvent, domElement: HTMLElement) => {
      if (mode !== 'create' || !selectedType) return;
      if (selectedType !== 'line' && selectedType !== 'area') return;
      if (points.length === 0) return;

      const position = raycast(event, domElement);
      if (position) {
        setPreviewPoints([...points, position]);
      }
    },
    [mode, selectedType, points, raycast]
  );

  // Cancel current annotation creation
  const cancelCreation = useCallback(() => {
    setPoints([]);
    setPreviewPoints([]);
    clearTempMarkers();
  }, [clearTempMarkers]);

  // Cleanup on unmount
  const cleanup = useCallback(() => {
    clearTempMarkers();
  }, [clearTempMarkers]);

  return {
    points,
    previewPoints,
    handleClick,
    handleDoubleClick,
    handleMouseMove,
    cancelCreation,
    cleanup,
  };
}
