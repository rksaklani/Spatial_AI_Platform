/**
 * Annotation Overlay Component
 * 
 * Renders annotations as 3D overlays in the scene:
 * - Comment markers with text content
 * - Measurement lines and areas
 * - Marker pins
 * - Defect markers with color-coded icons
 * - Hover/click interactions
 */

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

export interface Position3D {
  x: number;
  y: number;
  z: number;
}

export interface MeasurementData {
  measurement_type: string;
  value: number;
  unit: string;
  points: Position3D[];
}

export interface DefectData {
  category: string;
  severity: string;
  custom_category?: string;
  photo_paths: string[];
}

export interface Annotation {
  _id: string;
  scene_id: string;
  annotation_type: 'comment' | 'measurement' | 'marker' | 'defect';
  position: Position3D;
  content: string;
  measurement_data?: MeasurementData;
  defect_data?: DefectData;
  user_name: string;
  created_at: string;
  updated_at: string;
}

interface AnnotationOverlayProps {
  annotations: Annotation[];
  scene: THREE.Scene;
  camera: THREE.Camera;
  domElement: HTMLElement;
  onAnnotationClick?: (annotation: Annotation) => void;
  onAnnotationHover?: (annotation: Annotation | null) => void;
}

export const AnnotationOverlay: React.FC<AnnotationOverlayProps> = ({
  annotations,
  scene,
  camera,
  domElement,
  onAnnotationClick,
  onAnnotationHover,
}) => {
  const labelRendererRef = useRef<CSS2DRenderer | null>(null);
  const annotationObjectsRef = useRef<Map<string, THREE.Group>>(new Map());
  const raycasterRef = useRef<THREE.Raycaster>(new THREE.Raycaster());
  const mouseRef = useRef<THREE.Vector2>(new THREE.Vector2());
  const [hoveredAnnotation, setHoveredAnnotation] = useState<string | null>(null);

  // Initialize CSS2D renderer for labels
  useEffect(() => {
    const labelRenderer = new CSS2DRenderer();
    labelRenderer.setSize(domElement.clientWidth, domElement.clientHeight);
    labelRenderer.domElement.style.position = 'absolute';
    labelRenderer.domElement.style.top = '0';
    labelRenderer.domElement.style.pointerEvents = 'none';
    domElement.appendChild(labelRenderer.domElement);
    labelRendererRef.current = labelRenderer;

    return () => {
      if (labelRenderer.domElement.parentElement) {
        labelRenderer.domElement.parentElement.removeChild(labelRenderer.domElement);
      }
    };
  }, [domElement]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (labelRendererRef.current) {
        labelRendererRef.current.setSize(domElement.clientWidth, domElement.clientHeight);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [domElement]);

  // Create annotation marker geometry
  const createMarkerGeometry = (type: string, defectCategory?: string, severity?: string): THREE.Mesh => {
    let geometry: THREE.BufferGeometry;
    let material: THREE.Material;

    if (type === 'defect') {
      // Color-coded by severity
      let color = 0xffff00; // yellow default
      if (severity === 'low') color = 0x00ff00; // green
      else if (severity === 'medium') color = 0xffaa00; // orange
      else if (severity === 'high') color = 0xff6600; // red-orange
      else if (severity === 'critical') color = 0xff0000; // red

      geometry = new THREE.OctahedronGeometry(0.15);
      material = new THREE.MeshBasicMaterial({ color, opacity: 0.9, transparent: true });
    } else if (type === 'measurement') {
      geometry = new THREE.BoxGeometry(0.1, 0.1, 0.1);
      material = new THREE.MeshBasicMaterial({ color: 0x00aaff, opacity: 0.8, transparent: true });
    } else if (type === 'marker') {
      geometry = new THREE.ConeGeometry(0.1, 0.3, 8);
      material = new THREE.MeshBasicMaterial({ color: 0xff00ff, opacity: 0.8, transparent: true });
    } else {
      // comment
      geometry = new THREE.SphereGeometry(0.1);
      material = new THREE.MeshBasicMaterial({ color: 0xffffff, opacity: 0.8, transparent: true });
    }

    return new THREE.Mesh(geometry, material);
  };

  // Create measurement line
  const createMeasurementLine = (points: Position3D[]): THREE.Line => {
    const geometry = new THREE.BufferGeometry();
    const positions: number[] = [];

    points.forEach(p => {
      positions.push(p.x, p.y, p.z);
    });

    // Close polygon for area measurements
    if (points.length > 2) {
      positions.push(points[0].x, points[0].y, points[0].z);
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const material = new THREE.LineBasicMaterial({ color: 0x00aaff, linewidth: 2 });
    return new THREE.Line(geometry, material);
  };

  // Create label element
  const createLabel = (annotation: Annotation): CSS2DObject => {
    const div = document.createElement('div');
    div.className = 'annotation-label';
    div.style.padding = '4px 8px';
    div.style.background = 'rgba(0, 0, 0, 0.8)';
    div.style.color = 'white';
    div.style.borderRadius = '4px';
    div.style.fontSize = '12px';
    div.style.whiteSpace = 'nowrap';
    div.style.pointerEvents = 'auto';
    div.style.cursor = 'pointer';

    let labelText = '';
    if (annotation.annotation_type === 'measurement' && annotation.measurement_data) {
      labelText = `${annotation.measurement_data.value.toFixed(2)} ${annotation.measurement_data.unit}`;
    } else if (annotation.annotation_type === 'defect' && annotation.defect_data) {
      labelText = `${annotation.defect_data.category} (${annotation.defect_data.severity})`;
    } else {
      labelText = annotation.content.substring(0, 30) + (annotation.content.length > 30 ? '...' : '');
    }

    div.textContent = labelText;

    // Click handler
    div.addEventListener('click', (e) => {
      e.stopPropagation();
      onAnnotationClick?.(annotation);
    });

    // Hover handlers
    div.addEventListener('mouseenter', () => {
      setHoveredAnnotation(annotation._id);
      onAnnotationHover?.(annotation);
    });

    div.addEventListener('mouseleave', () => {
      setHoveredAnnotation(null);
      onAnnotationHover?.(null);
    });

    const label = new CSS2DObject(div);
    label.position.set(0, 0.3, 0); // Offset above marker
    return label;
  };

  // Render annotations
  useEffect(() => {
    // Clear existing annotations
    annotationObjectsRef.current.forEach((group) => {
      scene.remove(group);
    });
    annotationObjectsRef.current.clear();

    // Create new annotation objects
    annotations.forEach((annotation) => {
      const group = new THREE.Group();
      group.userData.annotationId = annotation._id;

      // Create marker
      const marker = createMarkerGeometry(
        annotation.annotation_type,
        annotation.defect_data?.category,
        annotation.defect_data?.severity
      );
      marker.position.set(annotation.position.x, annotation.position.y, annotation.position.z);
      group.add(marker);

      // Create measurement lines if applicable
      if (annotation.annotation_type === 'measurement' && annotation.measurement_data) {
        const line = createMeasurementLine(annotation.measurement_data.points);
        group.add(line);
      }

      // Create label
      const label = createLabel(annotation);
      marker.add(label);

      // Add to scene
      scene.add(group);
      annotationObjectsRef.current.set(annotation._id, group);
    });

    return () => {
      // Cleanup
      annotationObjectsRef.current.forEach((group) => {
        scene.remove(group);
      });
      annotationObjectsRef.current.clear();
    };
  }, [annotations, scene]);

  // Update label renderer
  useEffect(() => {
    const animate = () => {
      if (labelRendererRef.current) {
        labelRendererRef.current.render(scene, camera);
      }
      requestAnimationFrame(animate);
    };
    animate();
  }, [scene, camera]);

  // Handle hover highlighting
  useEffect(() => {
    annotationObjectsRef.current.forEach((group, id) => {
      const marker = group.children[0] as THREE.Mesh;
      if (marker && marker.material) {
        const material = marker.material as THREE.MeshBasicMaterial;
        if (id === hoveredAnnotation) {
          material.emissive = new THREE.Color(0x444444);
        } else {
          material.emissive = new THREE.Color(0x000000);
        }
      }
    });
  }, [hoveredAnnotation]);

  return null; // This component doesn't render React elements
};

export default AnnotationOverlay;
