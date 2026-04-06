import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ActiveUser {
  userId: string;
  userName: string;
  color: string;
  cursorPosition: [number, number, number] | null;
  cameraPosition: [number, number, number] | null;
}

interface CollaborationOverlayProps {
  users: Map<string, ActiveUser>;
  scene: THREE.Scene | null;
  camera: THREE.Camera | null;
}

export const CollaborationOverlay: React.FC<CollaborationOverlayProps> = ({
  users,
  scene,
  camera,
}) => {
  const cursorMarkersRef = useRef<Map<string, THREE.Group>>(new Map());

  // Generate a consistent color for a user based on their ID
  const generateUserColor = (userId: string): string => {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
      '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788'
    ];
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  // Create a cursor marker for a user
  const createCursorMarker = (user: ActiveUser): THREE.Group => {
    const group = new THREE.Group();
    
    // Create a sphere for the cursor
    const geometry = new THREE.SphereGeometry(0.1, 16, 16);
    const material = new THREE.MeshBasicMaterial({ 
      color: user.color || generateUserColor(user.userId),
      transparent: true,
      opacity: 0.8
    });
    const sphere = new THREE.Mesh(geometry, material);
    group.add(sphere);
    
    // Add a label with the user's name
    // Note: In a real implementation, you'd use a sprite or HTML overlay for the label
    // For now, we'll just use the sphere
    
    return group;
  };

  // Update cursor markers based on active users
  useEffect(() => {
    if (!scene) return;

    const markers = cursorMarkersRef.current;

    // Add or update markers for active users
    users.forEach((user, userId) => {
      if (!user.cursorPosition) return;

      let marker = markers.get(userId);
      
      if (!marker) {
        // Create new marker
        marker = createCursorMarker(user);
        markers.set(userId, marker);
        scene.add(marker);
      }

      // Update marker position
      marker.position.set(
        user.cursorPosition[0],
        user.cursorPosition[1],
        user.cursorPosition[2]
      );
    });

    // Remove markers for users who left
    markers.forEach((marker, userId) => {
      if (!users.has(userId)) {
        scene.remove(marker);
        markers.delete(userId);
      }
    });

    // Cleanup on unmount
    return () => {
      markers.forEach((marker) => {
        scene.remove(marker);
      });
      markers.clear();
    };
  }, [users, scene]);

  // This component doesn't render any DOM elements
  // It only manages Three.js objects in the scene
  return null;
};
