/**
 * Universal 3D Model Viewer
 * Supports: GLB, GLTF, OBJ, PLY, STL, FBX, DAE, and Gaussian Splatting
 * Point Clouds: PLY, LAS, LAZ, E57
 * BIM: IFC
 */

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { MTLLoader } from 'three/addons/loaders/MTLLoader.js';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { ColladaLoader } from 'three/addons/loaders/ColladaLoader.js';

interface ModelViewerProps {
  sceneId: string;
  modelUrl: string;
  modelType: 'glb' | 'gltf' | 'obj' | 'ply' | 'stl' | 'fbx' | 'dae' | 'splat' | 'las' | 'laz' | 'e57' | 'ifc';
  token?: string | null;
  onError?: (error: Error) => void;
  onLoadProgress?: (progress: number) => void;
  onSceneReady?: (scene: THREE.Scene, camera: THREE.Camera, domElement: HTMLElement, controls?: any) => void;
  // Annotation props
  annotationMode?: 'view' | 'create' | 'edit';
  selectedAnnotationType?: 'point' | 'line' | 'area' | 'text' | 'slope' | 'volume' | null;
  annotationColor?: string;
  onAnnotationModeChange?: (mode: 'view' | 'create' | 'edit') => void;
  onAnnotationTypeSelect?: (type: 'point' | 'line' | 'area' | 'text' | 'slope' | 'volume') => void;
  onAnnotationColorChange?: (color: string) => void;
  // Collaboration props
  connectionStatus?: 'connected' | 'disconnected' | 'connecting';
  activeUsers?: Array<{ userId: string; userName: string; cursorPosition?: [number, number, number] }>;
}

export const ModelViewer: React.FC<ModelViewerProps> = ({
  sceneId,
  modelUrl,
  modelType,
  token,
  onError,
  onLoadProgress,
  onSceneReady,
  annotationMode = 'view',
  selectedAnnotationType = null,
  annotationColor = '#FF6B6B',
  onAnnotationModeChange,
  onAnnotationTypeSelect,
  onAnnotationColorChange,
  connectionStatus = 'disconnected',
  activeUsers = [],
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const modelRef = useRef<THREE.Object3D | null>(null);
  const gridHelperRef = useRef<THREE.GridHelper | null>(null);
  const ambientLightRef = useRef<THREE.AmbientLight | null>(null);
  const directionalLightRef = useRef<THREE.DirectionalLight | null>(null);
  const fpsStatsRef = useRef<{ frames: number; lastTime: number; fps: number }>({ frames: 0, lastTime: performance.now(), fps: 0 });
  const dragRef = useRef<{ isDragging: boolean; startX: number; startY: number; startLeft: number; startTop: number }>({
    isDragging: false,
    startX: 0,
    startY: 0,
    startLeft: 0,
    startTop: 0
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showControls, setShowControls] = useState(false); // Start minimized
  const [panelPosition, setPanelPosition] = useState({ left: 16, top: 16 });
  
  // Section collapse states - all start collapsed
  const [displayExpanded, setDisplayExpanded] = useState(false);
  const [lightingExpanded, setLightingExpanded] = useState(false);
  const [performanceExpanded, setPerformanceExpanded] = useState(false);
  const [controlsExpanded, setControlsExpanded] = useState(false);
  const [annotationsExpanded, setAnnotationsExpanded] = useState(false);
  const [collaborationExpanded, setCollaborationExpanded] = useState(false);
  
  // Toolbar controls
  const [renderMode, setRenderMode] = useState<'client' | 'server'>('client');
  const [showFpsCounter, setShowFpsCounter] = useState(true);
  const [showMap, setShowMap] = useState(false);
  const [cameraMode, setCameraMode] = useState<'orbit' | 'fly' | 'first-person'>('orbit');
  
  // Display settings
  const [showBackground, setShowBackground] = useState(true);
  const [autoRotate, setAutoRotate] = useState(false);
  const [wireframe, setWireframe] = useState(false);
  const [showSkeleton, setShowSkeleton] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [pointSize, setPointSize] = useState(1);
  const [bgColor, setBgColor] = useState('#191919');
  
  // Lighting settings
  const [environment, setEnvironment] = useState('Neutral');
  const [toneMapping, setToneMapping] = useState('Linear');
  const [exposure, setExposure] = useState(1.0);
  const [punctualLights, setPunctualLights] = useState(true);
  const [ambientIntensity, setAmbientIntensity] = useState(0.6);
  const [ambientColor, setAmbientColor] = useState('#ffffff');
  const [directIntensity, setDirectIntensity] = useState(0.8);
  const [directColor, setDirectColor] = useState('#ffffff');
  
  // Performance stats
  const [fps, setFps] = useState(0);
  const [memory, setMemory] = useState(0);
  const [drawCalls, setDrawCalls] = useState(0);

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
    cameraRef.current = camera;

    // Create renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Create controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controlsRef.current = controls;

    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    ambientLightRef.current = ambientLight;

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 10);
    scene.add(directionalLight);
    directionalLightRef.current = directionalLight;

    // Add grid
    const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
    scene.add(gridHelper);
    gridHelperRef.current = gridHelper;

    // Load model
    loadModel(modelUrl, modelType, scene, camera);

    // Notify parent that scene is ready
    if (onSceneReady) {
      onSceneReady(scene, camera, renderer.domElement, controls);
    }

    // Animation loop
    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);
      
      // Auto-rotate model
      if (autoRotate && modelRef.current) {
        modelRef.current.rotation.y += 0.005;
      }
      
      // Update FPS
      fpsStatsRef.current.frames++;
      const currentTime = performance.now();
      if (currentTime >= fpsStatsRef.current.lastTime + 1000) {
        setFps(fpsStatsRef.current.frames);
        fpsStatsRef.current.frames = 0;
        fpsStatsRef.current.lastTime = currentTime;
      }
      
      controls.update();
      renderer.render(scene, camera);
      
      // Update draw calls
      setDrawCalls(renderer.info.render.calls);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!container || !camera || !renderer) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      controls.dispose();
      renderer.dispose();
      if (container && renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [sceneId, modelUrl, modelType]);

  // Handle background color change
  useEffect(() => {
    if (sceneRef.current) {
      if (showBackground) {
        sceneRef.current.background = new THREE.Color(bgColor);
      } else {
        sceneRef.current.background = null;
      }
    }
  }, [showBackground, bgColor]);

  // Handle grid visibility
  useEffect(() => {
    if (gridHelperRef.current) {
      gridHelperRef.current.visible = showGrid;
    }
  }, [showGrid]);

  // Handle wireframe mode
  useEffect(() => {
    if (modelRef.current) {
      modelRef.current.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach(mat => {
              mat.wireframe = wireframe;
            });
          } else {
            mesh.material.wireframe = wireframe;
          }
        }
      });
    }
  }, [wireframe]);

  // Handle point size (for point clouds)
  useEffect(() => {
    if (modelRef.current) {
      modelRef.current.traverse((child) => {
        if ((child as THREE.Points).isPoints) {
          const points = child as THREE.Points;
          if (points.material && 'size' in points.material) {
            (points.material as any).size = pointSize;
          }
        }
      });
    }
  }, [pointSize]);

  // Handle lighting changes
  useEffect(() => {
    if (ambientLightRef.current) {
      ambientLightRef.current.intensity = ambientIntensity;
      ambientLightRef.current.color = new THREE.Color(ambientColor);
      ambientLightRef.current.visible = punctualLights;
    }
    if (directionalLightRef.current) {
      directionalLightRef.current.intensity = directIntensity;
      directionalLightRef.current.color = new THREE.Color(directColor);
      directionalLightRef.current.visible = punctualLights;
    }
  }, [ambientIntensity, ambientColor, directIntensity, directColor, punctualLights]);

  // Handle exposure
  useEffect(() => {
    if (rendererRef.current) {
      rendererRef.current.toneMappingExposure = exposure;
    }
  }, [exposure]);

  // Handle tone mapping
  useEffect(() => {
    if (rendererRef.current) {
      switch (toneMapping) {
        case 'Linear':
          rendererRef.current.toneMapping = THREE.LinearToneMapping;
          break;
        case 'Reinhard':
          rendererRef.current.toneMapping = THREE.ReinhardToneMapping;
          break;
        case 'Cineon':
          rendererRef.current.toneMapping = THREE.CineonToneMapping;
          break;
        case 'ACESFilmic':
          rendererRef.current.toneMapping = THREE.ACESFilmicToneMapping;
          break;
        default:
          rendererRef.current.toneMapping = THREE.NoToneMapping;
      }
    }
  }, [toneMapping]);

  // Handle drag functionality
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.drag-handle')) {
      dragRef.current = {
        isDragging: true,
        startX: e.clientX,
        startY: e.clientY,
        startLeft: panelPosition.left,
        startTop: panelPosition.top
      };
    }
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (dragRef.current.isDragging) {
      const deltaX = e.clientX - dragRef.current.startX;
      const deltaY = e.clientY - dragRef.current.startY;
      
      setPanelPosition({
        left: Math.max(0, dragRef.current.startLeft + deltaX),
        top: Math.max(0, dragRef.current.startTop + deltaY)
      });
    }
  };

  const handleMouseUp = () => {
    dragRef.current.isDragging = false;
  };

  useEffect(() => {
    if (showControls) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [showControls, panelPosition]);

  // Camera control functions
  const handleResetCamera = () => {
    if (cameraRef.current && modelRef.current) {
      cameraRef.current.position.set(5, 5, 5);
      cameraRef.current.lookAt(0, 0, 0);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    }
  };

  const handleFullscreen = () => {
    if (containerRef.current) {
      if (!document.fullscreenElement) {
        containerRef.current.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
    }
  };

  const handleFitToView = () => {
    if (cameraRef.current && sceneRef.current && modelRef.current) {
      const box = new THREE.Box3().setFromObject(modelRef.current);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      
      const maxDim = Math.max(size.x, size.y, size.z);
      const fov = (cameraRef.current as THREE.PerspectiveCamera).fov * (Math.PI / 180);
      let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
      cameraZ *= 1.5;
      
      cameraRef.current.position.set(center.x, center.y, center.z + cameraZ);
      cameraRef.current.lookAt(center);
      
      if (controlsRef.current) {
        controlsRef.current.target.copy(center);
        controlsRef.current.update();
      }
    }
  };

  const loadModel = async (
    url: string,
    type: string,
    scene: THREE.Scene,
    camera: THREE.PerspectiveCamera
  ) => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('Loading model:', { url, type });

      let model: THREE.Object3D | null = null;

      // Fetch the file with authentication headers
      const response = await fetch(url, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (!response.ok) {
        throw new Error(`Failed to load model: ${response.statusText}`);
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      
      console.log('Model blob created:', { size: blob.size, type: blob.type });

      if (type === 'glb' || type === 'gltf') {
        const loader = new GLTFLoader();
        const gltf = await new Promise<any>((resolve, reject) => {
          loader.load(
            blobUrl,
            (gltf) => resolve(gltf),
            (progress) => {
              const percent = (progress.loaded / progress.total) * 100;
              onLoadProgress?.(percent);
            },
            (error) => reject(error)
          );
        });
        model = gltf.scene;
      } else if (type === 'obj') {
        // Try to load MTL file first (if it exists)
        const objLoader = new OBJLoader();
        
        // Check if there's a corresponding .mtl file
        const mtlUrl = url.replace(/\.obj$/i, '.mtl');
        let materialsLoaded = false;
        
        try {
          // Attempt to load MTL file
          const mtlResponse = await fetch(mtlUrl, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
          });
          
          if (mtlResponse.ok) {
            const mtlBlob = await mtlResponse.blob();
            const mtlBlobUrl = URL.createObjectURL(mtlBlob);
            
            const mtlLoader = new MTLLoader();
            const materials = await new Promise<any>((resolve, reject) => {
              mtlLoader.load(
                mtlBlobUrl,
                (materials) => resolve(materials),
                undefined,
                (error) => reject(error)
              );
            });
            
            materials.preload();
            objLoader.setMaterials(materials);
            materialsLoaded = true;
            URL.revokeObjectURL(mtlBlobUrl);
            console.log('MTL file loaded successfully');
          }
        } catch (error) {
          console.log('No MTL file found or failed to load, using default material');
        }
        
        // Load OBJ file
        model = await new Promise<THREE.Object3D>((resolve, reject) => {
          objLoader.load(
            blobUrl,
            (obj) => {
              // If no materials were loaded, apply a default material
              if (!materialsLoaded) {
                obj.traverse((child) => {
                  if ((child as THREE.Mesh).isMesh) {
                    const mesh = child as THREE.Mesh;
                    // Apply a default gray material with lighting
                    mesh.material = new THREE.MeshStandardMaterial({
                      color: 0x808080,
                      roughness: 0.7,
                      metalness: 0.3,
                      side: THREE.DoubleSide, // Render both sides
                    });
                  }
                });
              }
              resolve(obj);
            },
            (progress) => {
              const percent = (progress.loaded / progress.total) * 100;
              onLoadProgress?.(percent);
            },
            (error) => reject(error)
          );
        });
      } else if (type === 'ply') {
        const loader = new PLYLoader();
        const geometry = await new Promise<THREE.BufferGeometry>((resolve, reject) => {
          loader.load(
            blobUrl,
            (geometry) => resolve(geometry),
            (progress) => {
              const percent = (progress.loaded / progress.total) * 100;
              onLoadProgress?.(percent);
            },
            (error) => reject(error)
          );
        });
        // Compute normals if not present
        if (!geometry.attributes.normal) {
          geometry.computeVertexNormals();
        }
        const material = new THREE.MeshStandardMaterial({ 
          vertexColors: geometry.attributes.color ? true : false,
          color: geometry.attributes.color ? undefined : 0x808080,
          side: THREE.DoubleSide
        });
        model = new THREE.Mesh(geometry, material);
      } else if (type === 'stl') {
        const loader = new STLLoader();
        const geometry = await new Promise<THREE.BufferGeometry>((resolve, reject) => {
          loader.load(
            blobUrl,
            (geometry) => resolve(geometry),
            (progress) => {
              const percent = (progress.loaded / progress.total) * 100;
              onLoadProgress?.(percent);
            },
            (error) => reject(error)
          );
        });
        // STL files don't have normals, compute them
        geometry.computeVertexNormals();
        const material = new THREE.MeshStandardMaterial({ 
          color: 0x808080,
          roughness: 0.7,
          metalness: 0.3,
          side: THREE.DoubleSide
        });
        model = new THREE.Mesh(geometry, material);
      } else if (type === 'fbx') {
        const loader = new FBXLoader();
        model = await new Promise<THREE.Object3D>((resolve, reject) => {
          loader.load(
            blobUrl,
            (fbx) => resolve(fbx),
            (progress) => {
              const percent = (progress.loaded / progress.total) * 100;
              onLoadProgress?.(percent);
            },
            (error) => reject(error)
          );
        });
      } else if (type === 'dae') {
        const loader = new ColladaLoader();
        const collada = await new Promise<any>((resolve, reject) => {
          loader.load(
            blobUrl,
            (collada) => resolve(collada),
            (progress) => {
              const percent = (progress.loaded / progress.total) * 100;
              onLoadProgress?.(percent);
            },
            (error) => reject(error)
          );
        });
        model = collada.scene;
      } else if (type === 'las' || type === 'laz' || type === 'e57') {
        // Point cloud formats - these require special processing
        // For now, show a message that they need backend processing
        throw new Error(`${type.toUpperCase()} files require backend processing. Please wait for the scene to be processed.`);
      } else if (type === 'ifc') {
        // BIM format - requires special IFC loader
        throw new Error('IFC files require backend processing. Please wait for the scene to be processed.');
      } else if (type === 'splat') {
        // Gaussian Splatting format - should use GaussianViewer instead
        throw new Error('Gaussian Splatting files should be viewed with the GaussianViewer.');
      } else {
        throw new Error(`Unsupported format: ${type}`);
      }

      // Clean up blob URL
      URL.revokeObjectURL(blobUrl);

      if (model) {
        console.log('Model loaded successfully, processing...');
        
        // Center and scale model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 5 / maxDim;

        console.log('Model bounds:', { center, size, maxDim, scale });

        model.position.sub(center);
        model.scale.multiplyScalar(scale);

        scene.add(model);
        modelRef.current = model;

        // Position camera
        camera.position.set(5, 5, 5);
        camera.lookAt(0, 0, 0);

        console.log('Model added to scene successfully');
        setIsLoading(false);
        onLoadProgress?.(100);
      } else {
        throw new Error('Failed to load model: model is null');
      }
    } catch (err) {
      const error = err as Error;
      console.error('Model loading error:', error);
      setError(error.message);
      setIsLoading(false);
      onError?.(error);
    }
  };

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      
      {/* Minimize/Maximize Toggle Button */}
      {!showControls && (
        <button
          onClick={() => setShowControls(true)}
          className="absolute top-4 left-4 bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg p-3 shadow-lg hover:bg-surface-elevated transition-colors z-20"
          title="Show Display Controls"
        >
          <svg className="w-5 h-5 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      )}
      
      {/* Controls Panel - Show when expanded */}
      {showControls && (
        <div 
          className="absolute w-96 bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg shadow-2xl overflow-hidden z-20"
          style={{ left: `${panelPosition.left}px`, top: `${panelPosition.top}px` }}
          onMouseDown={handleMouseDown}
        >
          {/* Draggable Header */}
          <div className="drag-handle bg-surface-base border-b border-border-subtle px-4 py-3 cursor-move flex items-center justify-between">
            <h2 className="text-sm font-semibold text-text-primary">⚙️ Display Controls</h2>
            <button
              onClick={() => setShowControls(false)}
              className="text-text-secondary hover:text-text-primary transition-colors"
              title="Minimize"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
          </div>

        <div className="max-h-[70vh] overflow-y-auto">
          {/* Display Section */}
          <div className="border-b border-border-subtle">
            <button
                onClick={() => setDisplayExpanded(!displayExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-base transition-colors"
              >
                <h3 className="text-sm font-semibold text-text-primary">
                  {displayExpanded ? '▼' : '▶'} Display
                </h3>
              </button>
              
              {displayExpanded && (
                <div className="px-4 pb-4 space-y-2">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">background</span>
                    <input
                      type="checkbox"
                      checked={showBackground}
                      onChange={(e) => setShowBackground(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">autoRotate</span>
                    <input
                      type="checkbox"
                      checked={autoRotate}
                      onChange={(e) => setAutoRotate(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">wireframe</span>
                    <input
                      type="checkbox"
                      checked={wireframe}
                      onChange={(e) => setWireframe(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">skeleton</span>
                    <input
                      type="checkbox"
                      checked={showSkeleton}
                      onChange={(e) => setShowSkeleton(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">grid</span>
                    <input
                      type="checkbox"
                      checked={showGrid}
                      onChange={(e) => setShowGrid(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </label>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">pointSize</span>
                    <div className="flex items-center gap-2">
                      <input
                        type="range"
                        min="0.1"
                        max="5"
                        step="0.1"
                        value={pointSize}
                        onChange={(e) => setPointSize(parseFloat(e.target.value))}
                        className="w-32"
                      />
                      <span className="text-xs text-accent-primary w-8">{pointSize.toFixed(1)}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">bgColor</span>
                    <input
                      type="color"
                      value={bgColor}
                      onChange={(e) => setBgColor(e.target.value)}
                      className="w-20 h-8 rounded cursor-pointer"
                    />
                  </div>
              </div>
            )}
          </div>

          {/* Controls Section */}
          <div className="border-b border-border-subtle">
            <button
                onClick={() => setControlsExpanded(!controlsExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-base transition-colors"
              >
                <h3 className="text-sm font-semibold text-text-primary">
                  {controlsExpanded ? '▼' : '▶'} Controls
                </h3>
              </button>
              
              {controlsExpanded && (
                <div className="px-4 pb-4 space-y-3">
                  {/* Camera Controls */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase">Camera</span>
                    <div className="flex gap-2">
                      <button
                        onClick={handleResetCamera}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-surface-base hover:bg-surface-elevated border border-border-subtle rounded transition-colors"
                        title="Reset Camera"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span className="text-xs text-text-primary">Reset</span>
                      </button>
                      
                      <button
                        onClick={handleFullscreen}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-surface-base hover:bg-surface-elevated border border-border-subtle rounded transition-colors"
                        title="Fullscreen"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                        </svg>
                        <span className="text-xs text-text-primary">Fullscreen</span>
                      </button>
                      
                      <button
                        onClick={handleFitToView}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-surface-base hover:bg-surface-elevated border border-border-subtle rounded transition-colors"
                        title="Fit to View"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        <span className="text-xs text-text-primary">Fit</span>
                      </button>
                    </div>
                  </div>

                  {/* Camera Mode */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">Camera Mode</span>
                    <select
                      value={cameraMode}
                      onChange={(e) => setCameraMode(e.target.value as any)}
                      className="bg-surface-base border border-border-subtle rounded px-2 py-1 text-sm text-text-primary"
                    >
                      <option value="orbit">Orbit</option>
                      <option value="fly">Fly</option>
                      <option value="first-person">First Person</option>
                    </select>
                  </div>

                  {/* Render Mode */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase">Rendering</span>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Render Mode</span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setRenderMode('client')}
                          className={`px-3 py-1 text-xs rounded transition-colors ${
                            renderMode === 'client'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                            Client
                          </span>
                        </button>
                        <button
                          onClick={() => setRenderMode('server')}
                          className={`px-3 py-1 text-xs rounded transition-colors ${
                            renderMode === 'server'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                            </svg>
                            Server
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Display Options */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase">Display</span>
                    
                    <label className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Show FPS Counter</span>
                      <input
                        type="checkbox"
                        checked={showFpsCounter}
                        onChange={(e) => setShowFpsCounter(e.target.checked)}
                        className="w-4 h-4"
                      />
                    </label>
                    
                    <label className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Show Mini Map</span>
                      <input
                        type="checkbox"
                        checked={showMap}
                        onChange={(e) => setShowMap(e.target.checked)}
                        className="w-4 h-4"
                      />
                    </label>
                  </div>

                  {/* FPS Display */}
                  {showFpsCounter && (
                    <div className="p-3 bg-surface-base rounded border border-border-subtle">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-text-secondary">Current FPS</span>
                        <span className="text-lg font-mono font-bold text-green-400">{fps}</span>
                      </div>
                      <div className="mt-2 h-1 bg-surface-elevated rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-green-400 transition-all duration-300"
                          style={{ width: `${Math.min((fps / 60) * 100, 100)}%` }}
                        />
                      </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Annotations Section */}
          <div className="border-b border-border-subtle">
            <button
                onClick={() => setAnnotationsExpanded(!annotationsExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-base transition-colors"
              >
                <h3 className="text-sm font-semibold text-text-primary">
                  {annotationsExpanded ? '▼' : '▶'} Annotations
                </h3>
              </button>
              
              {annotationsExpanded && (
                <div className="px-4 pb-4 space-y-3">
                  {/* Annotation Mode */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase">Mode</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => onAnnotationModeChange?.('view')}
                        className={`flex-1 px-3 py-2 text-xs rounded transition-colors ${
                          annotationMode === 'view'
                            ? 'bg-accent-primary text-white'
                            : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                        }`}
                      >
                        👁 View
                      </button>
                      <button
                        onClick={() => onAnnotationModeChange?.('create')}
                        className={`flex-1 px-3 py-2 text-xs rounded transition-colors ${
                          annotationMode === 'create'
                            ? 'bg-accent-primary text-white'
                            : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                        }`}
                      >
                        ✏️ Create
                      </button>
                      <button
                        onClick={() => onAnnotationModeChange?.('edit')}
                        className={`flex-1 px-3 py-2 text-xs rounded transition-colors ${
                          annotationMode === 'edit'
                            ? 'bg-accent-primary text-white'
                            : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                        }`}
                      >
                        ✎ Edit
                      </button>
                    </div>
                  </div>

                  {/* Annotation Types */}
                  {annotationMode === 'create' && (
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-text-secondary uppercase">Type</span>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          onClick={() => onAnnotationTypeSelect?.('point')}
                          className={`px-3 py-2 text-xs rounded transition-colors flex flex-col items-center gap-1 ${
                            selectedAnnotationType === 'point'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="text-lg">📍</span>
                          <span>Point</span>
                        </button>
                        <button
                          onClick={() => onAnnotationTypeSelect?.('line')}
                          className={`px-3 py-2 text-xs rounded transition-colors flex flex-col items-center gap-1 ${
                            selectedAnnotationType === 'line'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="text-lg">📏</span>
                          <span>Line</span>
                        </button>
                        <button
                          onClick={() => onAnnotationTypeSelect?.('area')}
                          className={`px-3 py-2 text-xs rounded transition-colors flex flex-col items-center gap-1 ${
                            selectedAnnotationType === 'area'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="text-lg">⬜</span>
                          <span>Area</span>
                        </button>
                        <button
                          onClick={() => onAnnotationTypeSelect?.('text')}
                          className={`px-3 py-2 text-xs rounded transition-colors flex flex-col items-center gap-1 ${
                            selectedAnnotationType === 'text'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="text-lg">📝</span>
                          <span>Text</span>
                        </button>
                        <button
                          onClick={() => onAnnotationTypeSelect?.('slope')}
                          className={`px-3 py-2 text-xs rounded transition-colors flex flex-col items-center gap-1 ${
                            selectedAnnotationType === 'slope'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="text-lg">📐</span>
                          <span>Slope</span>
                        </button>
                        <button
                          onClick={() => onAnnotationTypeSelect?.('volume')}
                          className={`px-3 py-2 text-xs rounded transition-colors flex flex-col items-center gap-1 ${
                            selectedAnnotationType === 'volume'
                              ? 'bg-accent-primary text-white'
                              : 'bg-surface-base text-text-secondary hover:bg-surface-elevated'
                          }`}
                        >
                          <span className="text-lg">📦</span>
                          <span>Volume</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Annotation Color */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">Color</span>
                    <input
                      type="color"
                      value={annotationColor}
                      onChange={(e) => onAnnotationColorChange?.(e.target.value)}
                      className="w-20 h-8 rounded cursor-pointer"
                    />
                  </div>

                  {/* Instructions */}
                  {annotationMode === 'create' && selectedAnnotationType && (
                    <div className="p-3 bg-surface-base rounded border border-border-subtle">
                      <p className="text-xs text-text-secondary">
                        {selectedAnnotationType === 'point' && 'Click on the model to place a point annotation.'}
                        {selectedAnnotationType === 'line' && 'Click two points to measure distance.'}
                        {selectedAnnotationType === 'area' && 'Click multiple points to define an area. Double-click to finish.'}
                        {selectedAnnotationType === 'text' && 'Click on the model to add a text note.'}
                        {selectedAnnotationType === 'slope' && 'Click two points to measure slope.'}
                        {selectedAnnotationType === 'volume' && 'Click multiple points to calculate volume. Double-click to finish.'}
                      </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Collaboration Section */}
          <div className="border-b border-border-subtle">
            <button
              onClick={() => setCollaborationExpanded(!collaborationExpanded)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-base transition-colors"
            >
              <h3 className="text-sm font-semibold text-text-primary">
                {collaborationExpanded ? '▼' : '▶'} Collaboration
              </h3>
            </button>
            
            {collaborationExpanded && (
              <div className="px-4 pb-4 space-y-3">
                {/* Connection Status */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-text-secondary uppercase">Connection</span>
                  <div className="flex items-center justify-between p-3 bg-surface-base rounded border border-border-subtle">
                    <span className="text-sm text-text-secondary">Status</span>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        connectionStatus === 'connected' ? 'bg-green-400' :
                        connectionStatus === 'connecting' ? 'bg-yellow-400' :
                        'bg-red-400'
                      }`} />
                      <span className={`text-xs font-medium ${
                        connectionStatus === 'connected' ? 'text-green-400' :
                        connectionStatus === 'connecting' ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {connectionStatus === 'connected' ? 'Connected' :
                         connectionStatus === 'connecting' ? 'Connecting...' :
                         'Disconnected'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Active Users */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-secondary uppercase">Active Users</span>
                    <span className="text-xs text-accent-primary font-medium">{activeUsers.length}</span>
                  </div>
                  
                  {activeUsers.length > 0 ? (
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {activeUsers.map((user) => (
                        <div
                          key={user.userId}
                          className="flex items-center gap-2 p-2 bg-surface-base rounded border border-border-subtle"
                        >
                          <div className="w-8 h-8 rounded-full bg-accent-primary/20 flex items-center justify-center">
                            <span className="text-xs font-medium text-accent-primary">
                              {user.userName.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-text-primary truncate">{user.userName}</p>
                            <p className="text-xs text-text-secondary">Viewing scene</p>
                          </div>
                          <div className="w-2 h-2 rounded-full bg-green-400" />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 bg-surface-base rounded border border-border-subtle text-center">
                      <p className="text-xs text-text-secondary">No other users online</p>
                    </div>
                  )}
                </div>

                {/* Collaboration Features */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-text-secondary uppercase">Features</span>
                  <div className="space-y-1 text-xs text-text-secondary">
                    <div className="flex items-center gap-2">
                      <span className="text-green-400">✓</span>
                      <span>Real-time cursor tracking</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-green-400">✓</span>
                      <span>Live annotation sync</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-green-400">✓</span>
                      <span>User presence indicators</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Lighting Section */}
          <div className="border-b border-border-subtle">
            <button
                onClick={() => setLightingExpanded(!lightingExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-base transition-colors"
              >
                <h3 className="text-sm font-semibold text-text-primary">
                  {lightingExpanded ? '▼' : '▶'} Lighting
                </h3>
              </button>
              
              {lightingExpanded && (
                <div className="px-4 pb-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">environment</span>
                    <select
                      value={environment}
                      onChange={(e) => setEnvironment(e.target.value)}
                      className="bg-surface-base border border-border-subtle rounded px-2 py-1 text-sm text-text-primary"
                    >
                      <option>Neutral</option>
                      <option>Studio</option>
                      <option>Outdoor</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">toneMapping</span>
                    <select
                      value={toneMapping}
                      onChange={(e) => setToneMapping(e.target.value)}
                      className="bg-surface-base border border-border-subtle rounded px-2 py-1 text-sm text-text-primary"
                    >
                      <option>Linear</option>
                      <option>Reinhard</option>
                      <option>Cineon</option>
                      <option>ACESFilmic</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">exposure</span>
                    <div className="flex items-center gap-2">
                      <input
                        type="range"
                        min="0"
                        max="3"
                        step="0.1"
                        value={exposure}
                        onChange={(e) => setExposure(parseFloat(e.target.value))}
                        className="w-32"
                      />
                      <span className="text-xs text-accent-primary w-8">{exposure.toFixed(1)}</span>
                    </div>
                  </div>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">punctualLights</span>
                    <input
                      type="checkbox"
                      checked={punctualLights}
                      onChange={(e) => setPunctualLights(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </label>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">ambientIntensity</span>
                    <div className="flex items-center gap-2">
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={ambientIntensity}
                        onChange={(e) => setAmbientIntensity(parseFloat(e.target.value))}
                        className="w-32"
                      />
                      <span className="text-xs text-accent-primary w-8">{ambientIntensity.toFixed(1)}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">ambientColor</span>
                    <input
                      type="color"
                      value={ambientColor}
                      onChange={(e) => setAmbientColor(e.target.value)}
                      className="w-20 h-8 rounded cursor-pointer"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">directIntensity</span>
                    <div className="flex items-center gap-2">
                      <input
                        type="range"
                        min="0"
                        max="5"
                        step="0.1"
                        value={directIntensity}
                        onChange={(e) => setDirectIntensity(parseFloat(e.target.value))}
                        className="w-32"
                      />
                      <span className="text-xs text-accent-primary w-8">{directIntensity.toFixed(1)}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">directColor</span>
                    <input
                      type="color"
                      value={directColor}
                      onChange={(e) => setDirectColor(e.target.value)}
                    className="w-20 h-8 rounded cursor-pointer"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Performance Section */}
          <div>
            <button
                onClick={() => setPerformanceExpanded(!performanceExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-base transition-colors"
              >
                <h3 className="text-sm font-semibold text-text-primary">
                  {performanceExpanded ? '▼' : '▶'} Performance
                </h3>
              </button>
              
              {performanceExpanded && (
                <div className="px-4 pb-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-mono text-cyan-400">{fps} FPS (0-60)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-mono text-green-400">{drawCalls} Draw Calls</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-mono text-purple-400">{memory} MB Memory</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      )}
      
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <div className="text-white">Loading model...</div>
        </div>
      )}
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <div className="text-red-500">Error: {error}</div>
        </div>
      )}
    </div>
  );
};
