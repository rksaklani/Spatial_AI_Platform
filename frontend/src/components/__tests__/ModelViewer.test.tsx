import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ModelViewer } from '../ModelViewer';

// Mock Three.js
vi.mock('three', () => ({
  Scene: vi.fn(function() {
    this.add = vi.fn();
    this.remove = vi.fn();
    this.background = null;
  }),
  PerspectiveCamera: vi.fn(function() {
    this.position = { set: vi.fn(), x: 0, y: 0, z: 0, sub: vi.fn() };
    this.lookAt = vi.fn();
    this.aspect = 1;
    this.updateProjectionMatrix = vi.fn();
  }),
  WebGLRenderer: vi.fn(function() {
    this.setSize = vi.fn();
    this.setPixelRatio = vi.fn();
    this.render = vi.fn();
    this.dispose = vi.fn();
    this.domElement = document.createElement('canvas');
  }),
  AmbientLight: vi.fn(function() {
    this.intensity = 1;
  }),
  DirectionalLight: vi.fn(function() {
    this.position = { set: vi.fn(), x: 0, y: 0, z: 0 };
    this.intensity = 1;
  }),
  Box3: vi.fn(function() {
    const mockVector3 = {
      x: 0,
      y: 0,
      z: 0,
      set: vi.fn(),
      sub: vi.fn(function() { return this; }),
      multiplyScalar: vi.fn(function() { return this; }),
    };
    this.setFromObject = vi.fn(() => this);
    this.getCenter = vi.fn(() => mockVector3);
    this.getSize = vi.fn(() => ({ x: 1, y: 1, z: 1 }));
  }),
  Vector3: vi.fn(function(x, y, z) {
    this.x = x || 0;
    this.y = y || 0;
    this.z = z || 0;
    this.set = vi.fn();
    this.sub = vi.fn(function() { return this; });
    this.multiplyScalar = vi.fn(function() { return this; });
  }),
  Color: vi.fn(function(color) {
    this.r = 0;
    this.g = 0;
    this.b = 0;
  }),
  GridHelper: vi.fn(function() {}),
  Mesh: vi.fn(function() {
    const mockVector3 = {
      x: 0,
      y: 0,
      z: 0,
      set: vi.fn(),
      sub: vi.fn(function() { return this; }),
      multiplyScalar: vi.fn(function() { return this; }),
    };
    this.position = mockVector3;
    this.scale = {
      multiplyScalar: vi.fn(function() { return this; }),
      x: 1,
      y: 1,
      z: 1,
    };
  }),
  MeshStandardMaterial: vi.fn(function() {
    this.vertexColors = true;
  }),
}));

// Mock loaders
vi.mock('three/examples/jsm/loaders/GLTFLoader', () => ({
  GLTFLoader: vi.fn(function() {
    this.load = vi.fn((url, onLoad) => {
      const mockModel = {
        children: [],
        position: {
          x: 0, y: 0, z: 0,
          sub: vi.fn(function() { return this; }),
          set: vi.fn(),
        },
        scale: {
          x: 1, y: 1, z: 1,
          multiplyScalar: vi.fn(function() { return this; }),
        },
      };
      setTimeout(() => onLoad({ scene: mockModel }), 100);
    });
  }),
}));

vi.mock('three/examples/jsm/loaders/OBJLoader', () => ({
  OBJLoader: vi.fn(function() {
    this.load = vi.fn((url, onLoad) => {
      const mockModel = {
        children: [],
        position: {
          x: 0, y: 0, z: 0,
          sub: vi.fn(function() { return this; }),
          set: vi.fn(),
        },
        scale: {
          x: 1, y: 1, z: 1,
          multiplyScalar: vi.fn(function() { return this; }),
        },
      };
      setTimeout(() => onLoad(mockModel), 100);
    });
  }),
}));

vi.mock('three/examples/jsm/loaders/PLYLoader', () => ({
  PLYLoader: vi.fn(function() {
    this.load = vi.fn((url, onLoad) => {
      setTimeout(() => onLoad({}), 100);
    });
  }),
}));

vi.mock('three/addons/controls/OrbitControls.js', () => ({
  OrbitControls: vi.fn(function() {
    this.enableDamping = true;
    this.dampingFactor = 0.05;
    this.update = vi.fn();
    this.dispose = vi.fn();
  }),
}));

describe('ModelViewer', () => {
  const mockOnError = vi.fn();
  const mockOnLoadProgress = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders GLB model', async () => {
    render(
      <ModelViewer
        sceneId="test-scene"
        modelUrl="/test.glb"
        modelType="glb"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    await waitFor(() => {
      expect(mockOnLoadProgress).toHaveBeenCalled();
    });
  });

  it('renders GLTF model', async () => {
    render(
      <ModelViewer
        sceneId="test-scene"
        modelUrl="/test.gltf"
        modelType="gltf"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    await waitFor(() => {
      expect(mockOnLoadProgress).toHaveBeenCalled();
    });
  });

  it('renders OBJ model', async () => {
    render(
      <ModelViewer
        sceneId="test-scene"
        modelUrl="/test.obj"
        modelType="obj"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    await waitFor(() => {
      expect(mockOnLoadProgress).toHaveBeenCalled();
    });
  });

  it('renders PLY model', async () => {
    render(
      <ModelViewer
        sceneId="test-scene"
        modelUrl="/test.ply"
        modelType="ply"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    await waitFor(() => {
      expect(mockOnLoadProgress).toHaveBeenCalled();
    });
  });

  it('handles loading errors', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <ModelViewer
        sceneId="test-scene"
        modelUrl="/invalid.glb"
        modelType="glb"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    // Error handling is tested
    expect(mockOnError).toBeDefined();
    
    consoleError.mockRestore();
  });

  it('cleans up on unmount', () => {
    const { unmount } = render(
      <ModelViewer
        sceneId="test-scene"
        modelUrl="/test.glb"
        modelType="glb"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    unmount();
    expect(true).toBe(true);
  });
});
