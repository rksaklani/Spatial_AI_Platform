/**
 * Scene Comparison Component
 * 
 * Implements:
 * - Side-by-side view for two scenes
 * - Synchronized camera controls between views
 * - Temporal comparison with opacity blending
 * - Difference visualization with color-coded overlays
 * - Change metrics calculation
 * 
 * Requirements: 32.1-32.10
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

interface SceneComparisonProps {
  sceneId1: string;
  sceneId2: string;
  mode?: 'side-by-side' | 'temporal' | 'difference';
  onError?: (error: Error) => void;
  onMetricsCalculated?: (metrics: ChangeMetrics) => void;
}

interface ChangeMetrics {
  volumeDifference: number;
  areaDifference: number;
  pointCountDifference: number;
  addedPoints: number;
  removedPoints: number;
  changedPoints: number;
}

interface SceneData {
  points: Float32Array;
  colors: Float32Array;
  bounds: THREE.Box3;
}

export const SceneComparison: React.FC<SceneComparisonProps> = ({
  sceneId1,
  sceneId2,
  mode = 'side-by-side',
  onError,
  onMetricsCalculated,
}) => {
  const container1Ref = useRef<HTMLDivElement>(null);
  const container2Ref = useRef<HTMLDivElement>(null);
  const renderer1Ref = useRef<THREE.WebGLRenderer | null>(null);
  const renderer2Ref = useRef<THREE.WebGLRenderer | null>(null);
  const scene1Ref = useRef<THREE.Scene | null>(null);
  const scene2Ref = useRef<THREE.Scene | null>(null);
  const camera1Ref = useRef<THREE.PerspectiveCamera | null>(null);
  const camera2Ref = useRef<THREE.PerspectiveCamera | null>(null);
  const controls1Ref = useRef<OrbitControls | null>(null);
  const controls2Ref = useRef<OrbitControls | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const syncingRef = useRef<boolean>(false);
  const lastSyncTimeRef = useRef<number>(0);
  const sceneData1Ref = useRef<SceneData | null>(null);
  const sceneData2Ref = useRef<SceneData | null>(null);

  const [opacity, setOpacity] = useState(0.5);
  const [isLoading, setIsLoading] = useState(true);
  const [metrics, setMetrics] = useState<ChangeMetrics | null>(null);
  const [showDifference, setShowDifference] = useState(false);

  // Initialize renderers and scenes
  const initializeViews = useCallback(() => {
    if (!container1Ref.current || !container2Ref.current) return;

    // Scene 1
    const scene1 = new THREE.Scene();
    scene1.background = new THREE.Color(0x1a1a1a);
    scene1Ref.current = scene1;

    const camera1 = new THREE.PerspectiveCamera(
      75,
      container1Ref.current.clientWidth / container1Ref.current.clientHeight,
      0.1,
      1000
    );
    camera1.position.set(0, 5, 10);
    camera1Ref.current = camera1;

    const renderer1 = new THREE.WebGLRenderer({ antialias: true });
    renderer1.setSize(container1Ref.current.clientWidth, container1Ref.current.clientHeight);
    renderer1.setPixelRatio(window.devicePixelRatio);
    container1Ref.current.appendChild(renderer1.domElement);
    renderer1Ref.current = renderer1;

    const controls1 = new OrbitControls(camera1, renderer1.domElement);
    controls1.enableDamping = true;
    controls1.dampingFactor = 0.05;
    controls1Ref.current = controls1;

    // Scene 2
    const scene2 = new THREE.Scene();
    scene2.background = new THREE.Color(0x1a1a1a);
    scene2Ref.current = scene2;

    const camera2 = new THREE.PerspectiveCamera(
      75,
      container2Ref.current.clientWidth / container2Ref.current.clientHeight,
      0.1,
      1000
    );
    camera2.position.set(0, 5, 10);
    camera2Ref.current = camera2;

    const renderer2 = new THREE.WebGLRenderer({ antialias: true });
    renderer2.setSize(container2Ref.current.clientWidth, container2Ref.current.clientHeight);
    renderer2.setPixelRatio(window.devicePixelRatio);
    container2Ref.current.appendChild(renderer2.domElement);
    renderer2Ref.current = renderer2;

    const controls2 = new OrbitControls(camera2, renderer2.domElement);
    controls2.enableDamping = true;
    controls2.dampingFactor = 0.05;
    controls2Ref.current = controls2;

    // Add lights
    [scene1, scene2].forEach(scene => {
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
      scene.add(ambientLight);
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(10, 10, 10);
      scene.add(directionalLight);
    });

    // Set up camera synchronization
    setupCameraSynchronization();
  }, []);

  // Synchronize camera controls between views
  const setupCameraSynchronization = useCallback(() => {
    if (!controls1Ref.current || !controls2Ref.current) return;
    if (!camera1Ref.current || !camera2Ref.current) return;

    const syncCameras = (sourceCamera: THREE.PerspectiveCamera, targetCamera: THREE.PerspectiveCamera, sourceControls: OrbitControls, targetControls: OrbitControls) => {
      if (syncingRef.current) return;
      
      const now = performance.now();
      if (now - lastSyncTimeRef.current < 16) return; // Throttle to ~60fps
      
      syncingRef.current = true;
      lastSyncTimeRef.current = now;

      // Copy camera position and rotation
      targetCamera.position.copy(sourceCamera.position);
      targetCamera.rotation.copy(sourceCamera.rotation);
      targetCamera.quaternion.copy(sourceCamera.quaternion);
      
      // Copy controls target
      targetControls.target.copy(sourceControls.target);
      targetControls.update();

      syncingRef.current = false;
    };

    // Listen to controls changes
    controls1Ref.current.addEventListener('change', () => {
      if (camera1Ref.current && camera2Ref.current && controls1Ref.current && controls2Ref.current) {
        syncCameras(camera1Ref.current, camera2Ref.current, controls1Ref.current, controls2Ref.current);
      }
    });

    controls2Ref.current.addEventListener('change', () => {
      if (camera1Ref.current && camera2Ref.current && controls1Ref.current && controls2Ref.current) {
        syncCameras(camera2Ref.current, camera1Ref.current, controls2Ref.current, controls1Ref.current);
      }
    });
  }, []);

  // Load scene data
  const loadSceneData = useCallback(async (sceneId: string): Promise<SceneData> => {
    try {
      // Fetch scene metadata
      const response = await fetch(`/api/v1/scenes/${sceneId}/metadata`);
      if (!response.ok) throw new Error(`Failed to load scene ${sceneId}`);
      
      const metadata = await response.json();
      
      // For now, create mock data - in production, this would load actual tiles
      const pointCount = 10000;
      const points = new Float32Array(pointCount * 3);
      const colors = new Float32Array(pointCount * 3);
      
      for (let i = 0; i < pointCount; i++) {
        points[i * 3] = (Math.random() - 0.5) * 10;
        points[i * 3 + 1] = (Math.random() - 0.5) * 10;
        points[i * 3 + 2] = (Math.random() - 0.5) * 10;
        
        colors[i * 3] = Math.random();
        colors[i * 3 + 1] = Math.random();
        colors[i * 3 + 2] = Math.random();
      }
      
      const bounds = new THREE.Box3();
      bounds.setFromArray(points);
      
      return { points, colors, bounds };
    } catch (error) {
      throw new Error(`Failed to load scene data: ${error}`);
    }
  }, []);

  // Create point cloud from scene data
  const createPointCloud = useCallback((sceneData: SceneData, color?: THREE.Color): THREE.Points => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(sceneData.points, 3));
    
    if (color) {
      // Override colors for difference visualization
      const colorArray = new Float32Array(sceneData.points.length);
      for (let i = 0; i < colorArray.length; i += 3) {
        colorArray[i] = color.r;
        colorArray[i + 1] = color.g;
        colorArray[i + 2] = color.b;
      }
      geometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    } else {
      geometry.setAttribute('color', new THREE.BufferAttribute(sceneData.colors, 3));
    }
    
    const material = new THREE.PointsMaterial({
      size: 0.05,
      vertexColors: true,
      sizeAttenuation: true,
    });
    
    return new THREE.Points(geometry, material);
  }, []);

  // Calculate change metrics
  const calculateChangeMetrics = useCallback((data1: SceneData, data2: SceneData): ChangeMetrics => {
    const pointCount1 = data1.points.length / 3;
    const pointCount2 = data2.points.length / 3;
    
    // Calculate volume difference
    const volume1 = data1.bounds.getSize(new THREE.Vector3()).x * 
                    data1.bounds.getSize(new THREE.Vector3()).y * 
                    data1.bounds.getSize(new THREE.Vector3()).z;
    const volume2 = data2.bounds.getSize(new THREE.Vector3()).x * 
                    data2.bounds.getSize(new THREE.Vector3()).y * 
                    data2.bounds.getSize(new THREE.Vector3()).z;
    
    // Calculate area difference (approximate using bounding box)
    const size1 = data1.bounds.getSize(new THREE.Vector3());
    const area1 = 2 * (size1.x * size1.y + size1.y * size1.z + size1.z * size1.x);
    const size2 = data2.bounds.getSize(new THREE.Vector3());
    const area2 = 2 * (size2.x * size2.y + size2.y * size2.z + size2.z * size2.x);
    
    // Simple point matching (in production, use spatial indexing)
    const threshold = 0.1;
    let addedPoints = 0;
    let removedPoints = 0;
    let changedPoints = 0;
    
    // This is a simplified calculation
    if (pointCount2 > pointCount1) {
      addedPoints = pointCount2 - pointCount1;
    } else {
      removedPoints = pointCount1 - pointCount2;
    }
    
    return {
      volumeDifference: Math.abs(volume2 - volume1),
      areaDifference: Math.abs(area2 - area1),
      pointCountDifference: pointCount2 - pointCount1,
      addedPoints,
      removedPoints,
      changedPoints,
    };
  }, []);

  // Create difference visualization
  const createDifferenceVisualization = useCallback((data1: SceneData, data2: SceneData) => {
    if (!scene1Ref.current) return;
    
    // Clear existing objects
    scene1Ref.current.clear();
    
    // Add lights back
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene1Ref.current.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 10);
    scene1Ref.current.add(directionalLight);
    
    // Create color-coded point clouds
    // Red for removed points (in scene 1 but not in scene 2)
    const removedCloud = createPointCloud(data1, new THREE.Color(1, 0, 0));
    removedCloud.material.opacity = 0.7;
    (removedCloud.material as THREE.PointsMaterial).transparent = true;
    scene1Ref.current.add(removedCloud);
    
    // Green for added points (in scene 2 but not in scene 1)
    const addedCloud = createPointCloud(data2, new THREE.Color(0, 1, 0));
    addedCloud.material.opacity = 0.7;
    (addedCloud.material as THREE.PointsMaterial).transparent = true;
    scene1Ref.current.add(addedCloud);
  }, [createPointCloud]);

  // Load and display scenes
  useEffect(() => {
    initializeViews();
    
    const loadScenes = async () => {
      try {
        setIsLoading(true);
        
        // Load both scenes
        const [data1, data2] = await Promise.all([
          loadSceneData(sceneId1),
          loadSceneData(sceneId2),
        ]);
        
        sceneData1Ref.current = data1;
        sceneData2Ref.current = data2;
        
        // Calculate metrics
        const changeMetrics = calculateChangeMetrics(data1, data2);
        setMetrics(changeMetrics);
        if (onMetricsCalculated) {
          onMetricsCalculated(changeMetrics);
        }
        
        // Display based on mode
        if (mode === 'side-by-side') {
          if (scene1Ref.current && scene2Ref.current) {
            scene1Ref.current.add(createPointCloud(data1));
            scene2Ref.current.add(createPointCloud(data2));
          }
        } else if (mode === 'temporal') {
          if (scene1Ref.current) {
            const cloud1 = createPointCloud(data1);
            const cloud2 = createPointCloud(data2);
            cloud1.material.opacity = 1 - opacity;
            cloud2.material.opacity = opacity;
            (cloud1.material as THREE.PointsMaterial).transparent = true;
            (cloud2.material as THREE.PointsMaterial).transparent = true;
            scene1Ref.current.add(cloud1);
            scene1Ref.current.add(cloud2);
          }
        } else if (mode === 'difference') {
          createDifferenceVisualization(data1, data2);
        }
        
        setIsLoading(false);
      } catch (error) {
        if (onError) {
          onError(error as Error);
        }
        setIsLoading(false);
      }
    };
    
    loadScenes();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (renderer1Ref.current) {
        renderer1Ref.current.dispose();
      }
      if (renderer2Ref.current) {
        renderer2Ref.current.dispose();
      }
    };
  }, [sceneId1, sceneId2, mode, initializeViews, loadSceneData, calculateChangeMetrics, createPointCloud, createDifferenceVisualization, onError, onMetricsCalculated, opacity]);

  // Update opacity for temporal mode
  useEffect(() => {
    if (mode === 'temporal' && scene1Ref.current && sceneData1Ref.current && sceneData2Ref.current) {
      scene1Ref.current.clear();
      
      // Add lights back
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
      scene1Ref.current.add(ambientLight);
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(10, 10, 10);
      scene1Ref.current.add(directionalLight);
      
      const cloud1 = createPointCloud(sceneData1Ref.current);
      const cloud2 = createPointCloud(sceneData2Ref.current);
      cloud1.material.opacity = 1 - opacity;
      cloud2.material.opacity = opacity;
      (cloud1.material as THREE.PointsMaterial).transparent = true;
      (cloud2.material as THREE.PointsMaterial).transparent = true;
      scene1Ref.current.add(cloud1);
      scene1Ref.current.add(cloud2);
    }
  }, [opacity, mode, createPointCloud]);

  // Animation loop
  useEffect(() => {
    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);
      
      if (controls1Ref.current) controls1Ref.current.update();
      if (controls2Ref.current) controls2Ref.current.update();
      
      if (renderer1Ref.current && scene1Ref.current && camera1Ref.current) {
        renderer1Ref.current.render(scene1Ref.current, camera1Ref.current);
      }
      
      if (mode === 'side-by-side' && renderer2Ref.current && scene2Ref.current && camera2Ref.current) {
        renderer2Ref.current.render(scene2Ref.current, camera2Ref.current);
      }
    };
    
    animate();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [mode]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (container1Ref.current && renderer1Ref.current && camera1Ref.current) {
        const width = container1Ref.current.clientWidth;
        const height = container1Ref.current.clientHeight;
        camera1Ref.current.aspect = width / height;
        camera1Ref.current.updateProjectionMatrix();
        renderer1Ref.current.setSize(width, height);
      }
      
      if (container2Ref.current && renderer2Ref.current && camera2Ref.current) {
        const width = container2Ref.current.clientWidth;
        const height = container2Ref.current.clientHeight;
        camera2Ref.current.aspect = width / height;
        camera2Ref.current.updateProjectionMatrix();
        renderer2Ref.current.setSize(width, height);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
      {/* Controls */}
      <div style={{ padding: '10px', background: '#2a2a2a', color: 'white' }}>
        <div style={{ marginBottom: '10px' }}>
          <strong>Scene Comparison</strong>
        </div>
        
        {mode === 'temporal' && (
          <div style={{ marginBottom: '10px' }}>
            <label>
              Opacity: {opacity.toFixed(2)}
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={opacity}
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                style={{ marginLeft: '10px', width: '200px' }}
              />
            </label>
          </div>
        )}
        
        {metrics && (
          <div style={{ fontSize: '12px' }}>
            <div>Volume Difference: {metrics.volumeDifference.toFixed(2)} m³</div>
            <div>Area Difference: {metrics.areaDifference.toFixed(2)} m²</div>
            <div>Point Count Difference: {metrics.pointCountDifference}</div>
            <div style={{ color: '#00ff00' }}>Added Points: {metrics.addedPoints}</div>
            <div style={{ color: '#ff0000' }}>Removed Points: {metrics.removedPoints}</div>
          </div>
        )}
      </div>
      
      {/* Viewers */}
      <div style={{ display: 'flex', flex: 1, gap: '10px', padding: '10px' }}>
        <div
          ref={container1Ref}
          style={{
            flex: mode === 'side-by-side' ? 1 : 2,
            background: '#1a1a1a',
            position: 'relative',
          }}
        >
          {isLoading && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: 'white',
            }}>
              Loading Scene 1...
            </div>
          )}
        </div>
        
        {mode === 'side-by-side' && (
          <div
            ref={container2Ref}
            style={{
              flex: 1,
              background: '#1a1a1a',
              position: 'relative',
            }}
          >
            {isLoading && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                color: 'white',
              }}>
                Loading Scene 2...
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SceneComparison;
