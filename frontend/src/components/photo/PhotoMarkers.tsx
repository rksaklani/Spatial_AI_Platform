/**
 * PhotoMarkers Component
 * 
 * Displays photo marker positions in 3D scene
 * Requirements: F4
 */

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface PhotoMarker {
  id: string;
  photoId: string;
  position: [number, number, number];
  thumbnailUrl?: string;
  filename: string;
}

interface PhotoMarkersProps {
  scene: THREE.Scene | null;
  camera: THREE.Camera | null;
  markers: PhotoMarker[];
  onMarkerClick?: (photoId: string) => void;
  onMarkerHover?: (photoId: string | null) => void;
}

export function PhotoMarkers({
  scene,
  camera,
  markers,
  onMarkerClick,
  onMarkerHover,
}: PhotoMarkersProps) {
  const markerObjectsRef = useRef<Map<string, THREE.Group>>(new Map());
  const raycasterRef = useRef(new THREE.Raycaster());
  const mouseRef = useRef(new THREE.Vector2());
  const hoveredMarkerRef = useRef<string | null>(null);

  // Create marker objects
  useEffect(() => {
    if (!scene) return;

    // Remove old markers
    markerObjectsRef.current.forEach((group) => {
      scene.remove(group);
      group.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach((m) => m.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    });
    markerObjectsRef.current.clear();

    // Create new markers
    markers.forEach((marker) => {
      const group = new THREE.Group();
      group.userData = { markerId: marker.id, photoId: marker.photoId };

      // Camera icon geometry
      const iconGeometry = new THREE.BoxGeometry(0.3, 0.2, 0.2);
      const iconMaterial = new THREE.MeshBasicMaterial({
        color: 0x4ECDC4,
        transparent: true,
        opacity: 0.9,
      });
      const iconMesh = new THREE.Mesh(iconGeometry, iconMaterial);
      group.add(iconMesh);

      // Lens geometry
      const lensGeometry = new THREE.CylinderGeometry(0.08, 0.08, 0.15, 16);
      const lensMaterial = new THREE.MeshBasicMaterial({
        color: 0x333333,
      });
      const lensMesh = new THREE.Mesh(lensGeometry, lensMaterial);
      lensMesh.rotation.z = Math.PI / 2;
      lensMesh.position.set(0.15, 0, 0);
      group.add(lensMesh);

      // Marker stem
      const stemGeometry = new THREE.CylinderGeometry(0.02, 0.02, 0.5, 8);
      const stemMaterial = new THREE.MeshBasicMaterial({
        color: 0x4ECDC4,
        transparent: true,
        opacity: 0.6,
      });
      const stemMesh = new THREE.Mesh(stemGeometry, stemMaterial);
      stemMesh.position.set(0, -0.35, 0);
      group.add(stemMesh);

      // Position marker
      group.position.set(
        marker.position[0],
        marker.position[1],
        marker.position[2]
      );

      // Make marker always face camera
      group.userData.isBillboard = true;

      scene.add(group);
      markerObjectsRef.current.set(marker.id, group);
    });

    return () => {
      markerObjectsRef.current.forEach((group) => {
        scene.remove(group);
        group.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.geometry.dispose();
            if (Array.isArray(child.material)) {
              child.material.forEach((m) => m.dispose());
            } else {
              child.material.dispose();
            }
          }
        });
      });
      markerObjectsRef.current.clear();
    };
  }, [scene, markers]);

  // Update billboard rotation to face camera
  useEffect(() => {
    if (!camera) return;

    const updateBillboards = () => {
      markerObjectsRef.current.forEach((group) => {
        if (group.userData.isBillboard) {
          group.lookAt(camera.position);
        }
      });
    };

    // Update on animation frame
    const animate = () => {
      updateBillboards();
      requestAnimationFrame(animate);
    };
    const animationId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [camera]);

  // Handle mouse events for hover and click
  useEffect(() => {
    if (!scene || !camera) return;

    const handleMouseMove = (event: MouseEvent) => {
      const canvas = event.target as HTMLCanvasElement;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycasterRef.current.setFromCamera(mouseRef.current, camera);

      const markerObjects = Array.from(markerObjectsRef.current.values());
      const intersects = raycasterRef.current.intersectObjects(markerObjects, true);

      if (intersects.length > 0) {
        const intersectedGroup = intersects[0].object.parent as THREE.Group;
        const markerId = intersectedGroup?.userData?.markerId;
        const photoId = intersectedGroup?.userData?.photoId;

        if (markerId && photoId && hoveredMarkerRef.current !== markerId) {
          hoveredMarkerRef.current = markerId;
          canvas.style.cursor = 'pointer';
          onMarkerHover?.(photoId);

          // Highlight marker
          intersectedGroup.traverse((child) => {
            if (child instanceof THREE.Mesh && child.material instanceof THREE.MeshBasicMaterial) {
              child.material.opacity = 1.0;
            }
          });
        }
      } else {
        if (hoveredMarkerRef.current) {
          // Unhighlight previous marker
          const prevGroup = markerObjectsRef.current.get(hoveredMarkerRef.current);
          if (prevGroup) {
            prevGroup.traverse((child) => {
              if (child instanceof THREE.Mesh && child.material instanceof THREE.MeshBasicMaterial) {
                child.material.opacity = 0.9;
              }
            });
          }

          hoveredMarkerRef.current = null;
          canvas.style.cursor = 'default';
          onMarkerHover?.(null);
        }
      }
    };

    const handleClick = (event: MouseEvent) => {
      const canvas = event.target as HTMLCanvasElement;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycasterRef.current.setFromCamera(mouseRef.current, camera);

      const markerObjects = Array.from(markerObjectsRef.current.values());
      const intersects = raycasterRef.current.intersectObjects(markerObjects, true);

      if (intersects.length > 0) {
        const intersectedGroup = intersects[0].object.parent as THREE.Group;
        const photoId = intersectedGroup?.userData?.photoId;
        if (photoId) {
          onMarkerClick?.(photoId);
        }
      }
    };

    const canvas = scene.children[0]?.parent as any;
    const domElement = canvas?.domElement || document.querySelector('canvas');

    if (domElement) {
      domElement.addEventListener('mousemove', handleMouseMove);
      domElement.addEventListener('click', handleClick);

      return () => {
        domElement.removeEventListener('mousemove', handleMouseMove);
        domElement.removeEventListener('click', handleClick);
      };
    }
  }, [scene, camera, onMarkerClick, onMarkerHover]);

  return null;
}
