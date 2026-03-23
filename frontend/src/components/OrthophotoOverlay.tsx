/**
 * Orthophoto Overlay Component
 * 
 * Renders orthophotos as textured planes aligned with 3D terrain.
 * Supports transparency adjustment and layer ordering.
 */

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface Orthophoto {
  id: string;
  name: string;
  file_path: string;
  width: number;
  height: number;
  bbox_min_lon: number;
  bbox_min_lat: number;
  bbox_max_lon: number;
  bbox_max_lat: number;
  opacity: number;
  visible: boolean;
  layer_order: number;
  is_tiled: boolean;
  tiles_path?: string;
}

interface OrthophotoOverlayProps {
  sceneId: string;
  scene: THREE.Scene;
  onOrthophotosLoaded?: (orthophotos: Orthophoto[]) => void;
}

const OrthophotoOverlay: React.FC<OrthophotoOverlayProps> = ({
  sceneId,
  scene,
  onOrthophotosLoaded,
}) => {
  const [orthophotos, setOrthophotos] = useState<Orthophoto[]>([]);
  const [loading, setLoading] = useState(false);
  const meshesRef = useRef<Map<string, THREE.Mesh>>(new Map());

  // Fetch orthophotos for scene
  useEffect(() => {
    const fetchOrthophotos = async () => {
      setLoading(true);

      try {
        const response = await fetch(
          `/api/v1/orthophotos/scenes/${sceneId}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch orthophotos');
        }

        const data = await response.json();
        setOrthophotos(data.items || []);
        
        if (onOrthophotosLoaded) {
          onOrthophotosLoaded(data.items || []);
        }
      } catch (error) {
        console.error('Error fetching orthophotos:', error);
      } finally {
        setLoading(false);
      }
    };

    if (sceneId) {
      fetchOrthophotos();
    }
  }, [sceneId, onOrthophotosLoaded]);

  // Load and render orthophotos
  useEffect(() => {
    if (!scene || orthophotos.length === 0) return;

    const loadOrthophoto = async (orthophoto: Orthophoto) => {
      try {
        // Load texture
        const textureLoader = new THREE.TextureLoader();
        const texture = await textureLoader.loadAsync(
          `/api/v1/orthophotos/${orthophoto.id}/image`
        );

        // Calculate plane dimensions from bounding box
        // This is simplified - in production would use proper coordinate transformation
        const width = (orthophoto.bbox_max_lon - orthophoto.bbox_min_lon) * 111320; // Approximate meters
        const height = (orthophoto.bbox_max_lat - orthophoto.bbox_min_lat) * 111320;

        // Create plane geometry
        const geometry = new THREE.PlaneGeometry(width, height);

        // Create material with texture
        const material = new THREE.MeshBasicMaterial({
          map: texture,
          transparent: true,
          opacity: orthophoto.opacity,
          side: THREE.DoubleSide,
          depthWrite: false, // Allow transparency to work correctly
        });

        // Create mesh
        const mesh = new THREE.Mesh(geometry, material);

        // Position plane (simplified - would use proper georeferencing)
        const centerLon = (orthophoto.bbox_min_lon + orthophoto.bbox_max_lon) / 2;
        const centerLat = (orthophoto.bbox_min_lat + orthophoto.bbox_max_lat) / 2;
        mesh.position.set(centerLon * 111320, 0, centerLat * 111320);

        // Rotate to lie flat (XZ plane)
        mesh.rotation.x = -Math.PI / 2;

        // Set render order based on layer_order
        mesh.renderOrder = orthophoto.layer_order;

        // Set visibility
        mesh.visible = orthophoto.visible;

        // Add to scene
        scene.add(mesh);

        // Store reference
        meshesRef.current.set(orthophoto.id, mesh);
      } catch (error) {
        console.error(`Error loading orthophoto ${orthophoto.id}:`, error);
      }
    };

    // Load all orthophotos
    orthophotos.forEach(loadOrthophoto);

    // Cleanup
    return () => {
      meshesRef.current.forEach((mesh) => {
        scene.remove(mesh);
        mesh.geometry.dispose();
        if (mesh.material instanceof THREE.Material) {
          mesh.material.dispose();
          if (mesh.material.map) {
            mesh.material.map.dispose();
          }
        }
      });
      meshesRef.current.clear();
    };
  }, [scene, orthophotos]);

  // Update orthophoto properties when they change
  useEffect(() => {
    orthophotos.forEach((orthophoto) => {
      const mesh = meshesRef.current.get(orthophoto.id);
      if (mesh) {
        // Update opacity
        if (mesh.material instanceof THREE.MeshBasicMaterial) {
          mesh.material.opacity = orthophoto.opacity;
          mesh.material.needsUpdate = true;
        }

        // Update visibility
        mesh.visible = orthophoto.visible;

        // Update render order
        mesh.renderOrder = orthophoto.layer_order;
      }
    });
  }, [orthophotos]);

  return null; // This component doesn't render DOM elements
};

export default OrthophotoOverlay;
