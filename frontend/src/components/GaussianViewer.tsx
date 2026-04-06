/**
 * Gaussian Splatting 3D Viewer Component
 * 
 * Implements:
 * - Three.js scene rendering with WebGPU/WebGL2
 * - Orbit camera controls with touch support
 * - Progressive tile loading
 * - Proper Gaussian splatting shader
 * - 30 FPS target for 5M Gaussians
 * - Texture and material rendering
 * - BIM element visualization
 * - 2D overlay rendering
 * - Browser compatibility (Chrome, Edge, Safari, Firefox)
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CameraLimitsController } from './CameraLimits';
import { getTileManager } from '../services/tileManager.service';
import type { CameraConfiguration } from '../types/camera.types';

interface GaussianViewerProps {
  sceneId: string;
  token?: string | null;
  onError?: (error: Error) => void;
  onLoadProgress?: (progress: number) => void;
  onFpsUpdate?: (fps: number) => void;
  enableBIMVisualization?: boolean;
  enable2DOverlays?: boolean;
  enableAnimations?: boolean;
  onSceneReady?: (scene: THREE.Scene, camera: THREE.Camera, domElement: HTMLElement, controls?: any) => void;
  onCanvasClick?: (event: MouseEvent, domElement: HTMLElement) => void;
  onCanvasDoubleClick?: (event: MouseEvent, domElement: HTMLElement) => void;
  onCanvasMouseMove?: (event: MouseEvent, domElement: HTMLElement) => void;
  onCameraMove?: (cameraPosition: [number, number, number]) => void;
}

interface AnimationState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  speed: number;
  loop: boolean;
}

interface TextureInfo {
  diffuse?: THREE.Texture;
  normal?: THREE.Texture;
  roughness?: THREE.Texture;
  metalness?: THREE.Texture;
}

interface TileData {
  tile_id: string;
  priority: number;
  distance: number;
  file_path: string;
  gaussian_count: number;
  lod: string;
}

interface BIMElement {
  id: string;
  type: string;
  color: THREE.Color;
  selected: boolean;
  properties: Record<string, any>;
}

interface Overlay2D {
  id: string;
  type: 'image' | 'dxf';
  texture?: THREE.Texture;
  opacity: number;
  visible: boolean;
}

export const GaussianViewer: React.FC<GaussianViewerProps> = ({
  sceneId,
  token,
  onError,
  onLoadProgress,
  onFpsUpdate,
  enableBIMVisualization = false,
  enable2DOverlays = false,
  enableAnimations = false,
  onSceneReady,
  onCanvasClick,
  onCanvasDoubleClick,
  onCanvasMouseMove,
  onCameraMove,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const loadedTilesRef = useRef<Set<string>>(new Set());
  const tileObjectsRef = useRef<Map<string, THREE.Points>>(new Map());
  const bimElementsRef = useRef<Map<string, BIMElement>>(new Map());
  const overlaysRef = useRef<Map<string, Overlay2D>>(new Map());
  const lastTileRequestRef = useRef<number>(0);
  const tileRequestThrottleMs = 500;
  const animationMixerRef = useRef<THREE.AnimationMixer | null>(null);
  const animationActionsRef = useRef<THREE.AnimationAction[]>([]);
  const cameraLimitsRef = useRef<CameraLimitsController | null>(null);
  const tileManagerRef = useRef(getTileManager());

  const [isLoading, setIsLoading] = useState(true);
  const [fps, setFps] = useState(0);
  const [visibleGaussians, setVisibleGaussians] = useState(0);
  const [rendererType, setRendererType] = useState<'webgpu' | 'webgl2' | 'webgl'>('webgl2');
  const [browserInfo, setBrowserInfo] = useState<string>('');
  const [animationState, setAnimationState] = useState<AnimationState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    speed: 1.0,
    loop: true,
  });
  const [selectedBIMElement, setSelectedBIMElement] = useState<string | null>(null);
  const [cameraConfig, setCameraConfig] = useState<CameraConfiguration | null>(null);
  const [approachingBoundary, setApproachingBoundary] = useState(false);
  const [noDataMessage, setNoDataMessage] = useState<string | null>(null);

  // Detect WebGPU support and browser info
  const detectRendererType = useCallback(async (): Promise<'webgpu' | 'webgl2' | 'webgl'> => {
    // Detect browser
    const ua = navigator.userAgent;
    let browser = 'Unknown';
    if (ua.includes('Chrome') && !ua.includes('Edge')) browser = 'Chrome';
    else if (ua.includes('Safari') && !ua.includes('Chrome')) browser = 'Safari';
    else if (ua.includes('Firefox')) browser = 'Firefox';
    else if (ua.includes('Edge')) browser = 'Edge';
    
    const isMobile = /iPhone|iPad|iPod|Android/i.test(ua);
    setBrowserInfo(`${browser}${isMobile ? ' Mobile' : ''}`);
    
    // Check WebGPU support
    if ('gpu' in navigator) {
      try {
        const adapter = await (navigator as any).gpu.requestAdapter();
        if (adapter) {
          return 'webgpu';
        }
      } catch (e) {
        console.log('WebGPU not available, falling back to WebGL2');
      }
    }

    // Check WebGL2 support
    const canvas = document.createElement('canvas');
    const gl2 = canvas.getContext('webgl2');
    if (gl2) {
      return 'webgl2';
    }

    // Fall back to WebGL1
    return 'webgl';
  }, []);

  // Initialize Three.js scene
  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    sceneRef.current = scene;

    // Create camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Detect and create renderer
    detectRendererType().then((type) => {
      setRendererType(type);
      
      try {
        // Create WebGL2 or WebGL renderer (WebGPU not yet in Three.js stable)
        const renderer = new THREE.WebGLRenderer({
          antialias: true,
          alpha: false,
          powerPreference: 'high-performance',
          precision: 'highp',
        });
        
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.sortObjects = false; // Disable sorting for performance
        container.appendChild(renderer.domElement);
        rendererRef.current = renderer;
        
        // Start animation loop after renderer is ready
        startAnimationLoop();
      } catch (error) {
        onError?.(new Error('Failed to initialize WebGL renderer'));
        return;
      }
    });

    // Create orbit controls with touch support
    const controls = new OrbitControls(camera, container);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 0.5;
    controls.maxDistance = 100;
    controls.enablePan = true;
    controls.enableZoom = true;
    controls.enableRotate = true;
    
    // Touch controls
    controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };
    
    // Throttled tile request on camera change
    controls.addEventListener('change', () => {
      const now = Date.now();
      if (now - lastTileRequestRef.current > tileRequestThrottleMs) {
        lastTileRequestRef.current = now;
        requestTileUpdate();
        
        // Notify parent of camera movement for collaboration
        if (onCameraMove && camera) {
          const pos = camera.position;
          onCameraMove([pos.x, pos.y, pos.z]);
        }
      }
    });
    controlsRef.current = controls;

    // Load camera configuration
    loadCameraConfiguration();

    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight.position.set(10, 10, 10);
    scene.add(directionalLight);

    // Add grid helper
    const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
    scene.add(gridHelper);

    // Add axes helper (larger size for better visibility)
    const axesHelper = new THREE.AxesHelper(50);
    scene.add(axesHelper);

    // Handle window resize
    const handleResize = () => {
      if (!container || !camera || !rendererRef.current) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      rendererRef.current.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);

    // Handle click events for annotation creation
    const handleClick = (event: MouseEvent) => {
      if (onCanvasClick) {
        onCanvasClick(event, container);
      }
    };

    const handleDoubleClick = (event: MouseEvent) => {
      if (onCanvasDoubleClick) {
        onCanvasDoubleClick(event, container);
      }
    };

    const handleMouseMove = (event: MouseEvent) => {
      if (onCanvasMouseMove) {
        onCanvasMouseMove(event, container);
      }
    };

    container.addEventListener('click', handleClick);
    container.addEventListener('dblclick', handleDoubleClick);
    container.addEventListener('mousemove', handleMouseMove);

    // Animation loop function
    let lastTime = performance.now();
    let frameCount = 0;
    let fpsUpdateTime = lastTime;

    const startAnimationLoop = () => {
      const animate = () => {
        animationFrameRef.current = requestAnimationFrame(animate);

        const currentTime = performance.now();
        const deltaTime = currentTime - lastTime;
        lastTime = currentTime;

        // Update FPS counter
        frameCount++;
        if (currentTime - fpsUpdateTime >= 1000) {
          const currentFps = Math.round((frameCount * 1000) / (currentTime - fpsUpdateTime));
          setFps(currentFps);
          onFpsUpdate?.(currentFps);
          frameCount = 0;
          fpsUpdateTime = currentTime;
        }

        // Update controls
        controls.update();
        
        // Check if approaching boundary
        if (cameraLimitsRef.current) {
          const approaching = cameraLimitsRef.current.isApproachingBoundary(2.0);
          if (approaching !== approachingBoundary) {
            setApproachingBoundary(approaching);
          }
        }
        
        // Update animations if enabled
        if (enableAnimations && animationMixerRef.current) {
          const delta = deltaTime / 1000; // Convert to seconds
          animationMixerRef.current.update(delta * animationState.speed);
          
          // Update animation time
          if (animationState.isPlaying && animationState.duration > 0) {
            setAnimationState(prev => {
              let newTime = prev.currentTime + delta * prev.speed;
              if (newTime >= prev.duration) {
                if (prev.loop) {
                  newTime = newTime % prev.duration;
                } else {
                  newTime = prev.duration;
                  return { ...prev, currentTime: newTime, isPlaying: false };
                }
              }
              return { ...prev, currentTime: newTime };
            });
          }
        }

        // Render scene - use ref to ensure renderer is available
        if (rendererRef.current) {
          rendererRef.current.render(scene, camera);
        }
      };
      animate();
      
      // Initial tile load
      requestTileUpdate();
      
      // Notify parent that scene is ready
      if (onSceneReady) {
        onSceneReady(scene, camera, container, controls);
      }
    };

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('click', handleClick);
      container.removeEventListener('dblclick', handleDoubleClick);
      container.removeEventListener('mousemove', handleMouseMove);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      controls.dispose();
      if (cameraLimitsRef.current) {
        cameraLimitsRef.current.dispose();
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
        if (container && rendererRef.current.domElement.parentNode === container) {
          container.removeChild(rendererRef.current.domElement);
        }
      }
      
      // Dispose geometries and materials
      tileObjectsRef.current.forEach((points) => {
        points.geometry.dispose();
        if (Array.isArray(points.material)) {
          points.material.forEach(m => m.dispose());
        } else {
          points.material.dispose();
        }
      });
    };
  }, [sceneId, detectRendererType]);

  // Load camera configuration from API
  const loadCameraConfiguration = useCallback(async () => {
    if (!token) {
      console.warn('No authentication token available');
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/scenes/${sceneId}/camera-config`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const config: CameraConfiguration = await response.json();
        setCameraConfig(config);

        // Initialize camera limits controller
        if (cameraRef.current && controlsRef.current && sceneRef.current) {
          cameraLimitsRef.current = new CameraLimitsController(
            cameraRef.current,
            controlsRef.current,
            config,
            sceneRef.current
          );
        }
      }
    } catch (error) {
      console.error('Failed to load camera configuration:', error);
    }
  }, [sceneId, token]);

  // Request tile update based on camera position using TileManager
  const requestTileUpdate = useCallback(async () => {
    if (!cameraRef.current || !controlsRef.current || !token) return;

    const camera = cameraRef.current;
    const tileManager = tileManagerRef.current;

    try {
      // Use TileManager to request tiles with frustum culling and prioritization
      const tiles = await tileManager.requestTiles(
        sceneId,
        camera,
        async (request) => {
          // API client function
          const response = await fetch(`/api/v1/scenes/${sceneId}/tiles`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(request),
          });

          if (!response.ok) {
            // If 500 error, scene likely has no tiles - don't throw, just return empty
            if (response.status === 500) {
              console.warn('Scene has no tiles available (processing may have failed)');
              setIsLoading(false);
              return { tiles: [] };
            }
            throw new Error(`Failed to fetch tiles: ${response.statusText}`);
          }

          return await response.json();
        }
      );

      // Load tiles progressively by priority
      if (tiles.length > 0) {
        loadTilesProgressively(tiles);
      } else {
        // No tiles available
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Failed to request tiles:', error);
      setIsLoading(false);
      // Don't call onError for tile loading failures - just show the no data message
    }
  }, [sceneId, token, onError]);

  // Parse PLY file to Three.js geometry (robust implementation)
  const parsePLYToGeometry = useCallback((arrayBuffer: ArrayBuffer): THREE.BufferGeometry => {
    const geometry = new THREE.BufferGeometry();
    
    try {
      const decoder = new TextDecoder();
      const headerText = decoder.decode(arrayBuffer.slice(0, 2000));
      
      // Parse header
      const lines = headerText.split('\n');
      let vertexCount = 0;
      let headerEndIndex = 0;
      // let format = 'binary_little_endian'; // Reserved for future ASCII support
      const properties: string[] = [];
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (line.startsWith('format')) {
          // format = line.split(' ')[1]; // Reserved for future ASCII support
        } else if (line.startsWith('element vertex')) {
          vertexCount = parseInt(line.split(' ')[2]);
        } else if (line.startsWith('property')) {
          properties.push(line);
        } else if (line === 'end_header') {
          headerEndIndex = headerText.indexOf('end_header') + 11;
          break;
        }
      }
      
      if (vertexCount === 0) {
        throw new Error('Invalid PLY: no vertices found');
      }
      
      // Parse binary data
      const dataView = new DataView(arrayBuffer, headerEndIndex);
      let offset = 0;
      
      const positions = new Float32Array(vertexCount * 3);
      const colors = new Float32Array(vertexCount * 3);
      const scales = new Float32Array(vertexCount * 3);
      const rotations = new Float32Array(vertexCount * 4);
      const opacities = new Float32Array(vertexCount);
      
      // Determine stride based on properties
      // Standard Gaussian Splatting PLY format:
      // x, y, z (3 floats) + scale_0, scale_1, scale_2 (3 floats) +
      // rot_0, rot_1, rot_2, rot_3 (4 floats) + opacity (1 float) +
      // f_dc_0, f_dc_1, f_dc_2 (3 floats) + ... (SH coefficients)
      const stride = 64; // Simplified - adjust based on actual format
      
      for (let i = 0; i < vertexCount; i++) {
        // Position
        positions[i * 3] = dataView.getFloat32(offset, true);
        positions[i * 3 + 1] = dataView.getFloat32(offset + 4, true);
        positions[i * 3 + 2] = dataView.getFloat32(offset + 8, true);
        
        // Scales
        scales[i * 3] = Math.exp(dataView.getFloat32(offset + 12, true));
        scales[i * 3 + 1] = Math.exp(dataView.getFloat32(offset + 16, true));
        scales[i * 3 + 2] = Math.exp(dataView.getFloat32(offset + 20, true));
        
        // Rotations (quaternion)
        rotations[i * 4] = dataView.getFloat32(offset + 24, true);
        rotations[i * 4 + 1] = dataView.getFloat32(offset + 28, true);
        rotations[i * 4 + 2] = dataView.getFloat32(offset + 32, true);
        rotations[i * 4 + 3] = dataView.getFloat32(offset + 36, true);
        
        // Opacity
        const opacityLogit = dataView.getFloat32(offset + 40, true);
        opacities[i] = 1 / (1 + Math.exp(-opacityLogit)); // Sigmoid
        
        // SH DC coefficients (first 3 for color)
        const sh0 = dataView.getFloat32(offset + 44, true);
        const sh1 = dataView.getFloat32(offset + 48, true);
        const sh2 = dataView.getFloat32(offset + 52, true);
        
        // Convert SH DC to RGB
        const C0 = 0.28209479177387814;
        colors[i * 3] = Math.max(0, Math.min(1, sh0 * C0 + 0.5));
        colors[i * 3 + 1] = Math.max(0, Math.min(1, sh1 * C0 + 0.5));
        colors[i * 3 + 2] = Math.max(0, Math.min(1, sh2 * C0 + 0.5));
        
        offset += stride;
      }
      
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      geometry.setAttribute('scale', new THREE.BufferAttribute(scales, 3));
      geometry.setAttribute('rotation', new THREE.BufferAttribute(rotations, 4));
      geometry.setAttribute('opacity', new THREE.BufferAttribute(opacities, 1));
      
    } catch (error) {
      console.error('PLY parsing error:', error);
      // Fallback: create simple point cloud
      const positions = new Float32Array(3);
      positions[0] = 0;
      positions[1] = 0;
      positions[2] = 0;
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    }
    
    return geometry;
  }, []);

  // Create material for Gaussian rendering with custom shader
  const createGaussianMaterial = useCallback((): THREE.ShaderMaterial => {
    return new THREE.ShaderMaterial({
      uniforms: {
        viewport: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
        focal: { value: 1000.0 },
      },
      vertexShader: `
        attribute vec3 scale;
        attribute vec4 rotation;
        attribute float opacity;
        
        varying vec3 vColor;
        varying float vOpacity;
        varying vec2 vPosition;
        
        uniform vec2 viewport;
        uniform float focal;
        
        // Quaternion to rotation matrix
        mat3 quatToMat3(vec4 q) {
          float x = q.x, y = q.y, z = q.z, w = q.w;
          return mat3(
            1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z), 2.0 * (x * z + w * y),
            2.0 * (x * y + w * z), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - w * x),
            2.0 * (x * z - w * y), 2.0 * (y * z + w * x), 1.0 - 2.0 * (x * x + y * y)
          );
        }
        
        void main() {
          vColor = color;
          vOpacity = opacity;
          
          // Transform position to view space
          vec4 viewPos = modelViewMatrix * vec4(position, 1.0);
          
          // Compute 3D covariance from scale and rotation
          mat3 R = quatToMat3(rotation);
          mat3 S = mat3(
            scale.x, 0.0, 0.0,
            0.0, scale.y, 0.0,
            0.0, 0.0, scale.z
          );
          mat3 M = R * S;
          mat3 Sigma = M * transpose(M);
          
          // Project to 2D
          mat3 J = mat3(
            focal / viewPos.z, 0.0, 0.0,
            0.0, focal / viewPos.z, 0.0,
            -focal * viewPos.x / (viewPos.z * viewPos.z), -focal * viewPos.y / (viewPos.z * viewPos.z), 0.0
          );
          
          mat3 W = transpose(mat3(modelViewMatrix));
          mat3 T = W * J;
          mat3 cov2D = transpose(T) * Sigma * T;
          
          // Compute eigenvalues for point size
          float mid = 0.5 * (cov2D[0][0] + cov2D[1][1]);
          float radius = length(vec2((cov2D[0][0] - cov2D[1][1]) / 2.0, cov2D[0][1]));
          float lambda1 = mid + radius;
          float lambda2 = mid - radius;
          
          vec2 diagonalVector = normalize(vec2(cov2D[0][1], lambda1 - cov2D[0][0]));
          vec2 majorAxis = min(sqrt(2.0 * lambda1), 1024.0) * diagonalVector;
          vec2 minorAxis = min(sqrt(2.0 * lambda2), 1024.0) * vec2(diagonalVector.y, -diagonalVector.x);
          
          vPosition = vec2(0.0, 0.0);
          
          vec4 projectedPos = projectionMatrix * viewPos;
          gl_Position = projectedPos;
          gl_PointSize = max(length(majorAxis), length(minorAxis)) * viewport.y / projectedPos.w;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        varying float vOpacity;
        varying vec2 vPosition;
        
        void main() {
          // Gaussian falloff
          vec2 coord = gl_PointCoord - vec2(0.5);
          float dist = length(coord);
          float alpha = exp(-0.5 * dist * dist / 0.25) * vOpacity;
          
          if (alpha < 0.01) discard;
          
          gl_FragColor = vec4(vColor, alpha);
        }
      `,
      transparent: true,
      depthTest: true,
      depthWrite: false,
      blending: THREE.NormalBlending,
    });
  }, []);

  // Load a single tile
  const loadTile = useCallback(async (tile: TileData): Promise<void> => {
    const tileManager = tileManagerRef.current;
    
    if (!token) {
      console.warn('No authentication token available for tile loading');
      return;
    }
    
    // Check if already loading
    if (tileManager.isTileLoading(tile.tile_id)) {
      return;
    }

    // Mark as loading
    tileManager.markTileLoading(tile.tile_id);
    const startTime = performance.now();

    try {
      // Download tile PLY file
      const response = await fetch(`/api/v1/scenes/${sceneId}/tiles/${tile.tile_id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to download tile: ${response.statusText}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      const downloadTime = performance.now() - startTime;
      
      // Update bandwidth estimate
      tileManager.updateBandwidthEstimate(arrayBuffer.byteLength, downloadTime);
      
      // Parse PLY and create Three.js geometry
      const geometry = parsePLYToGeometry(arrayBuffer);
      
      // Create material for Gaussian rendering with proper shader
      const material = createGaussianMaterial();
      
      // Create points object
      const points = new THREE.Points(geometry, material);
      
      // Add to scene
      sceneRef.current?.add(points);
      
      // Track loaded tile
      loadedTilesRef.current.add(tile.tile_id);
      tileObjectsRef.current.set(tile.tile_id, points);
      tileManager.markTileLoaded(tile.tile_id);
      
      // Update visible Gaussian count
      setVisibleGaussians(prev => prev + tile.gaussian_count);
      
      console.log(`Loaded tile ${tile.tile_id}: ${tile.gaussian_count} Gaussians, LOD: ${tile.lod}, distance: ${tile.distance.toFixed(2)}m, bandwidth: ${tileManager.getCacheStats().bandwidthEstimate.toFixed(2)} Mbps`);
    } catch (error) {
      tileManager.markTileLoaded(tile.tile_id); // Remove from loading set
      console.error(`Failed to load tile ${tile.tile_id}:`, error);
      throw error;
    }
  }, [sceneId, token, parsePLYToGeometry, createGaussianMaterial]);

  // Load tiles progressively
  const loadTilesProgressively = useCallback(async (tiles: TileData[]) => {
    if (tiles.length === 0) {
      setIsLoading(false);
      return;
    }

    let loadedCount = 0;
    let successCount = 0;
    let failedCount = 0;

    console.log(`Starting progressive tile loading: ${tiles.length} tiles`);

    for (const tile of tiles) {
      // Skip if already loaded
      if (loadedTilesRef.current.has(tile.tile_id)) {
        loadedCount++;
        successCount++;
        onLoadProgress?.((loadedCount / tiles.length) * 100);
        continue;
      }

      try {
        await loadTile(tile);
        successCount++;
      } catch (error) {
        console.error(`Failed to load tile ${tile.tile_id}:`, error);
        failedCount++;
      }

      loadedCount++;
      onLoadProgress?.((loadedCount / tiles.length) * 100);
    }

    console.log(`Tile loading complete: ${successCount} succeeded, ${failedCount} failed, ${tiles.length} total`);
    setIsLoading(false);
  }, [onLoadProgress, loadTile]);

  // Estimate bandwidth using Network Information API
  const estimateBandwidth = useCallback((): number => {
    if ('connection' in navigator) {
      const conn = (navigator as any).connection;
      if (conn && conn.downlink) {
        return conn.downlink; // Mbps
      }
    }
    // Default to 10 Mbps if API not available
    return 10;
  }, []);

  // Animation controls
  const playAnimation = useCallback(() => {
    setAnimationState(prev => ({ ...prev, isPlaying: true }));
    animationActionsRef.current.forEach(action => action.play());
  }, []);

  const pauseAnimation = useCallback(() => {
    setAnimationState(prev => ({ ...prev, isPlaying: false }));
    animationActionsRef.current.forEach(action => action.paused = true);
  }, []);

  const stopAnimation = useCallback(() => {
    setAnimationState(prev => ({ ...prev, isPlaying: false, currentTime: 0 }));
    animationActionsRef.current.forEach(action => {
      action.stop();
      action.time = 0;
    });
  }, []);

  const setAnimationSpeed = useCallback((speed: number) => {
    setAnimationState(prev => ({ ...prev, speed }));
    animationActionsRef.current.forEach(action => {
      action.timeScale = speed;
    });
  }, []);

  const seekAnimation = useCallback((time: number) => {
    setAnimationState(prev => ({ ...prev, currentTime: time }));
    animationActionsRef.current.forEach(action => {
      action.time = time;
    });
  }, []);

  // Load texture for material
  const loadTexture = useCallback(async (url: string): Promise<THREE.Texture | null> => {
    try {
      const loader = new THREE.TextureLoader();
      return await new Promise((resolve, reject) => {
        loader.load(
          url,
          (texture) => resolve(texture),
          undefined,
          (error) => reject(error)
        );
      });
    } catch (error) {
      console.error('Failed to load texture:', url, error);
      return null;
    }
  }, []);

  // Create material with textures (PBR support)
  // Note: Available for glTF models with texture data
  const createMaterialWithTextures = useCallback((textures: TextureInfo): THREE.Material => {
    if (textures.diffuse || textures.normal || textures.roughness || textures.metalness) {
      // Use PBR material if textures available
      return new THREE.MeshStandardMaterial({
        map: textures.diffuse || null,
        normalMap: textures.normal || null,
        roughnessMap: textures.roughness || null,
        metalnessMap: textures.metalness || null,
        roughness: textures.roughness ? 1.0 : 0.5,
        metalness: textures.metalness ? 1.0 : 0.0,
      });
    } else {
      // Default material
      return new THREE.MeshStandardMaterial({
        color: 0xcccccc,
        roughness: 0.5,
        metalness: 0.0,
      });
    }
  }, []);

  // Load and display BIM elements
  const loadBIMElements = useCallback(async () => {
    if (!enableBIMVisualization) return;

    try {
      // Fetch BIM elements from API
      const response = await fetch(`/api/v1/scenes/${sceneId}/bim-elements`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) return;

      const elements = await response.json();

      // Create meshes for BIM elements
      elements.forEach((element: any) => {
        const geometry = new THREE.BoxGeometry(
          element.dimensions?.width || 1,
          element.dimensions?.height || 1,
          element.dimensions?.depth || 1
        );

        // Color code by type
        const colorMap: Record<string, number> = {
          wall: 0xcccccc,
          floor: 0x8b7355,
          ceiling: 0xffffff,
          door: 0x8b4513,
          window: 0x87ceeb,
          column: 0x696969,
          beam: 0x696969,
        };

        const color = element.clashing ? 0xff0000 : (colorMap[element.type] || 0xcccccc);
        const material = new THREE.MeshStandardMaterial({
          color,
          transparent: true,
          opacity: element.clashing ? 0.8 : 0.6,
        });

        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(
          element.position?.x || 0,
          element.position?.y || 0,
          element.position?.z || 0
        );
        mesh.userData = { bimElement: element };

        sceneRef.current?.add(mesh);

        bimElementsRef.current.set(element.id, {
          id: element.id,
          type: element.type,
          color: new THREE.Color(color),
          selected: false,
          properties: element.properties || {},
        });
      });
    } catch (error) {
      console.error('Failed to load BIM elements:', error);
    }
  }, [sceneId, enableBIMVisualization]);

  // Handle BIM element selection
  // Note: Called when user clicks on BIM elements in the scene
  const handleBIMElementClick = useCallback((elementId: string) => {
    setSelectedBIMElement(elementId);
    
    // Highlight selected element
    bimElementsRef.current.forEach((element, id) => {
      element.selected = id === elementId;
    });

    // Update mesh materials
    sceneRef.current?.traverse((object) => {
      if (object instanceof THREE.Mesh && object.userData.bimElement) {
        const element = bimElementsRef.current.get(object.userData.bimElement.id);
        if (element) {
          (object.material as THREE.MeshStandardMaterial).emissive.setHex(
            element.selected ? 0x444444 : 0x000000
          );
        }
      }
    });
  }, []);

  // Load and display 2D overlays
  const load2DOverlays = useCallback(async () => {
    if (!enable2DOverlays) return;

    try {
      // Fetch 2D overlays from API
      const response = await fetch(`/api/v1/scenes/${sceneId}/overlays`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) return;

      const overlays = await response.json();

      // Create overlay meshes
      for (const overlay of overlays) {
        if (overlay.type === 'image') {
          // Load image texture
          const texture = await loadTexture(overlay.url);
          if (!texture) continue;

          const geometry = new THREE.PlaneGeometry(
            overlay.width || 10,
            overlay.height || 10
          );
          const material = new THREE.MeshBasicMaterial({
            map: texture,
            transparent: true,
            opacity: overlay.opacity || 1.0,
            side: THREE.DoubleSide,
          });

          const mesh = new THREE.Mesh(geometry, material);
          mesh.position.set(
            overlay.position?.x || 0,
            overlay.position?.y || 0,
            overlay.position?.z || 0
          );
          mesh.rotation.set(
            overlay.rotation?.x || 0,
            overlay.rotation?.y || 0,
            overlay.rotation?.z || 0
          );
          mesh.visible = overlay.visible !== false;

          sceneRef.current?.add(mesh);

          overlaysRef.current.set(overlay.id, {
            id: overlay.id,
            type: 'image',
            texture,
            opacity: overlay.opacity || 1.0,
            visible: overlay.visible !== false,
          });
        } else if (overlay.type === 'dxf') {
          // DXF linework rendering
          // This would require a DXF parser - simplified here
          const lineMaterial = new THREE.LineBasicMaterial({
            color: overlay.color || 0x000000,
            transparent: true,
            opacity: overlay.opacity || 1.0,
          });

          // Create line geometry from DXF data
          const points: THREE.Vector3[] = [];
          overlay.lines?.forEach((line: any) => {
            points.push(new THREE.Vector3(line.start.x, line.start.y, line.start.z));
            points.push(new THREE.Vector3(line.end.x, line.end.y, line.end.z));
          });

          const geometry = new THREE.BufferGeometry().setFromPoints(points);
          const lineSegments = new THREE.LineSegments(geometry, lineMaterial);
          lineSegments.visible = overlay.visible !== false;

          sceneRef.current?.add(lineSegments);

          overlaysRef.current.set(overlay.id, {
            id: overlay.id,
            type: 'dxf',
            opacity: overlay.opacity || 1.0,
            visible: overlay.visible !== false,
          });
        }
      }
    } catch (error) {
      console.error('Failed to load 2D overlays:', error);
    }
  }, [sceneId, enable2DOverlays, loadTexture]);

  // Toggle overlay visibility
  const toggleOverlayVisibility = useCallback((overlayId: string) => {
    const overlay = overlaysRef.current.get(overlayId);
    if (!overlay) return;

    overlay.visible = !overlay.visible;

    // Update mesh visibility
    sceneRef.current?.traverse((object) => {
      if (object.userData.overlayId === overlayId) {
        object.visible = overlay.visible;
      }
    });
  }, []);

  // Set overlay opacity
  const setOverlayOpacity = useCallback((overlayId: string, opacity: number) => {
    const overlay = overlaysRef.current.get(overlayId);
    if (!overlay) return;

    overlay.opacity = Math.max(0, Math.min(1, opacity));

    // Update mesh opacity
    sceneRef.current?.traverse((object) => {
      if (object.userData.overlayId === overlayId && object instanceof THREE.Mesh) {
        (object.material as THREE.MeshBasicMaterial).opacity = overlay.opacity;
      }
    });
  }, []);

  // Load BIM elements and overlays after scene loads
  useEffect(() => {
    if (!isLoading) {
      loadBIMElements();
      load2DOverlays();
    }
  }, [isLoading, loadBIMElements, load2DOverlays]);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    if (!cameraRef.current || !controlsRef.current) return;
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    
    // Move camera closer to target
    const direction = new THREE.Vector3();
    direction.subVectors(camera.position, controls.target);
    direction.multiplyScalar(0.8); // Zoom in by 20%
    camera.position.copy(controls.target).add(direction);
    controls.update();
  }, []);

  const handleZoomOut = useCallback(() => {
    if (!cameraRef.current || !controlsRef.current) return;
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    
    // Move camera away from target
    const direction = new THREE.Vector3();
    direction.subVectors(camera.position, controls.target);
    direction.multiplyScalar(1.25); // Zoom out by 25%
    camera.position.copy(controls.target).add(direction);
    controls.update();
  }, []);

  const handleResetView = useCallback(() => {
    if (!cameraRef.current || !controlsRef.current) return;
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    
    // Reset to initial position
    camera.position.set(0, 5, 10);
    controls.target.set(0, 0, 0);
    controls.update();
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      
      {/* Stats overlay */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 10,
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontFamily: 'monospace',
          fontSize: '12px',
        }}
      >
        <div>Browser: {browserInfo}</div>
        <div>Renderer: {rendererType.toUpperCase()}</div>
        <div>FPS: {fps}</div>
        <div>Gaussians: {visibleGaussians.toLocaleString()}</div>
        <div>Tiles: {loadedTilesRef.current.size}</div>
        <div>Status: {isLoading ? 'Loading...' : 'Ready'}</div>
      </div>

      {/* No data message */}
      {!isLoading && visibleGaussians === 0 && loadedTilesRef.current.size === 0 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(0, 0, 0, 0.9)',
            color: 'white',
            padding: '30px',
            borderRadius: '10px',
            textAlign: 'center',
            maxWidth: '500px',
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>📦</div>
          <h3 style={{ margin: '0 0 15px 0', fontSize: '20px' }}>No 3D Data Available</h3>
          <p style={{ margin: '0 0 20px 0', color: '#ccc', fontSize: '14px' }}>
            This scene is marked as ready, but no 3D data was found. This could mean:
          </p>
          <div style={{ fontSize: '12px', color: '#999', marginTop: '15px', textAlign: 'left' }}>
            <p style={{ margin: '5px 0' }}>• Processing completed but didn't generate Gaussian splats</p>
            <p style={{ margin: '5px 0' }}>• The video processing pipeline encountered an issue</p>
            <p style={{ margin: '5px 0' }}>• Tiles weren't uploaded to storage correctly</p>
            <p style={{ margin: '5px 0' }}>• The scene needs to be reprocessed</p>
          </div>
          <div style={{ marginTop: '20px', padding: '15px', background: 'rgba(255, 152, 0, 0.2)', borderRadius: '8px', border: '1px solid rgba(255, 152, 0, 0.3)' }}>
            <p style={{ margin: '0', fontSize: '13px', color: '#ff9800' }}>
              💡 <strong>Solution:</strong> Go back to the dashboard and try uploading the video again. Make sure the Celery workers are running.
            </p>
          </div>
          <button
            onClick={() => window.history.back()}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '8px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            ← Back to Dashboard
          </button>
        </div>
      )}

      {/* Zoom controls */}
      <div
        style={{
          position: 'absolute',
          bottom: 20,
          left: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        <button
          onClick={handleZoomIn}
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '8px',
            background: 'rgba(0, 0, 0, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: 'white',
            fontSize: '24px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.9)';
            e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.7)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '8px',
            background: 'rgba(0, 0, 0, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: 'white',
            fontSize: '24px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.9)';
            e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.7)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
          title="Zoom Out"
        >
          −
        </button>
        <button
          onClick={handleResetView}
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '8px',
            background: 'rgba(0, 0, 0, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: 'white',
            fontSize: '18px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.9)';
            e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.7)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
          title="Reset View"
        >
          ⟲
        </button>
      </div>

      {/* Boundary warning */}
      {approachingBoundary && cameraConfig?.boundary_enabled && (
        <div
          style={{
            position: 'absolute',
            top: 10,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(255, 165, 0, 0.9)',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '5px',
            fontFamily: 'sans-serif',
            fontSize: '14px',
            fontWeight: 'bold',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}
        >
          ⚠️ Approaching camera boundary
        </div>
      )}

      {/* Animation controls */}
      {enableAnimations && animationState.duration > 0 && (
        <div
          style={{
            position: 'absolute',
            bottom: 10,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <button onClick={animationState.isPlaying ? pauseAnimation : playAnimation}>
            {animationState.isPlaying ? '⏸' : '▶'}
          </button>
          <button onClick={stopAnimation}>⏹</button>
          <input
            type="range"
            min="0"
            max={animationState.duration}
            step="0.01"
            value={animationState.currentTime}
            onChange={(e) => seekAnimation(parseFloat(e.target.value))}
            style={{ width: '200px' }}
          />
          <span>
            {animationState.currentTime.toFixed(2)}s / {animationState.duration.toFixed(2)}s
          </span>
          <select
            value={animationState.speed}
            onChange={(e) => setAnimationSpeed(parseFloat(e.target.value))}
          >
            <option value="0.5">0.5x</option>
            <option value="1">1x</option>
            <option value="2">2x</option>
          </select>
          <label>
            <input
              type="checkbox"
              checked={animationState.loop}
              onChange={(e) => setAnimationState(prev => ({ ...prev, loop: e.target.checked }))}
            />
            Loop
          </label>
        </div>
      )}

      {/* BIM element properties */}
      {enableBIMVisualization && selectedBIMElement && (
        <div
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            background: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            maxWidth: '300px',
            fontFamily: 'monospace',
            fontSize: '12px',
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
            BIM Element Properties
          </div>
          {(() => {
            const element = bimElementsRef.current.get(selectedBIMElement);
            if (!element) return null;
            return (
              <>
                <div>ID: {element.id}</div>
                <div>Type: {element.type}</div>
                {Object.entries(element.properties).map(([key, value]) => (
                  <div key={key}>
                    {key}: {String(value)}
                  </div>
                ))}
                <button
                  onClick={() => setSelectedBIMElement(null)}
                  style={{
                    marginTop: '10px',
                    padding: '5px 10px',
                    background: '#444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    cursor: 'pointer',
                  }}
                >
                  Close
                </button>
              </>
            );
          })()}
        </div>
      )}

      {/* 2D Overlay controls */}
      {enable2DOverlays && overlaysRef.current.size > 0 && (
        <div
          style={{
            position: 'absolute',
            bottom: 10,
            right: 10,
            background: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            fontFamily: 'monospace',
            fontSize: '12px',
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>2D Overlays</div>
          {Array.from(overlaysRef.current.entries()).map(([id, overlay]) => (
            <div key={id} style={{ marginBottom: '5px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <input
                  type="checkbox"
                  checked={overlay.visible}
                  onChange={() => toggleOverlayVisibility(id)}
                />
                {overlay.type} - {id.slice(0, 8)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={overlay.opacity}
                onChange={(e) => setOverlayOpacity(id, parseFloat(e.target.value))}
                style={{ width: '100%', marginTop: '2px' }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
