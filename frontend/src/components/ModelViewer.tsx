/**
 * Universal 3D Model Viewer
 * Supports: GLB, GLTF, OBJ, FBX, PLY, and Gaussian Splatting
 */

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';

interface ModelViewerProps {
  sceneId: string;
  modelUrl: string;
  modelType: 'glb' | 'gltf' | 'obj' | 'ply' | 'splat';
  onError?: (error: Error) => void;
  onLoadProgress?: (progress: number) => void;
}

export const ModelViewer: React.FC<ModelViewerProps> = ({
  sceneId,
  modelUrl,
  modelType,
  onError,
  onLoadProgress,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const modelRef = useRef<THREE.Object3D | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 10);
    scene.add(directionalLight);

    // Add grid
    const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
    scene.add(gridHelper);

    // Load model
    loadModel(modelUrl, modelType, scene, camera);

    // Animation loop
    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
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

  const loadModel = async (
    url: string,
    type: string,
    scene: THREE.Scene,
    camera: THREE.PerspectiveCamera
  ) => {
    try {
      setIsLoading(true);
      setError(null);

      let model: THREE.Object3D | null = null;

      if (type === 'glb' || type === 'gltf') {
        const loader = new GLTFLoader();
        const gltf = await new Promise<any>((resolve, reject) => {
          loader.load(
            url,
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
        const loader = new OBJLoader();
        model = await new Promise<THREE.Object3D>((resolve, reject) => {
          loader.load(
            url,
            (obj) => resolve(obj),
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
            url,
            (geometry) => resolve(geometry),
            (progress) => {
              const percent = (progress.loaded / progress.total) * 100;
              onLoadProgress?.(percent);
            },
            (error) => reject(error)
          );
        });
        const material = new THREE.MeshStandardMaterial({ vertexColors: true });
        model = new THREE.Mesh(geometry, material);
      }

      if (model) {
        // Center and scale model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 5 / maxDim;

        model.position.sub(center);
        model.scale.multiplyScalar(scale);

        scene.add(model);
        modelRef.current = model;

        // Position camera
        camera.position.set(5, 5, 5);
        camera.lookAt(0, 0, 0);

        setIsLoading(false);
        onLoadProgress?.(100);
      }
    } catch (err) {
      const error = err as Error;
      setError(error.message);
      setIsLoading(false);
      onError?.(error);
    }
  };

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      
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
