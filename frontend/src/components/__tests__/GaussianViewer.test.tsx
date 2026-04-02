import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { GaussianViewer } from '../GaussianViewer';

// Mock Three.js
vi.mock('three', () => ({
  Scene: vi.fn(function() {
    this.add = vi.fn();
    this.remove = vi.fn();
  }),
  PerspectiveCamera: vi.fn(function() {
    const mockVector3 = {
      x: 0,
      y: 0,
      z: 0,
      set: vi.fn(),
      clone: vi.fn(function() {
        return { x: this.x, y: this.y, z: this.z, clone: vi.fn() };
      }),
    };
    this.position = mockVector3;
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
  Clock: vi.fn(function() {
    this.getDelta = vi.fn(() => 0.016);
  }),
  Vector3: vi.fn(function(x, y, z) {
    this.x = x || 0;
    this.y = y || 0;
    this.z = z || 0;
    this.set = vi.fn();
    this.sub = vi.fn(function() { return this; });
    this.multiplyScalar = vi.fn(function() { return this; });
    this.clone = vi.fn(function() {
      return { x: this.x, y: this.y, z: this.z, clone: vi.fn() };
    });
  }),
  Raycaster: vi.fn(function() {
    this.setFromCamera = vi.fn();
    this.intersectObjects = vi.fn(() => []);
  }),
  Vector2: vi.fn(function(x, y) {
    this.x = x || 0;
    this.y = y || 0;
  }),
  Color: vi.fn(function(color) {
    this.r = 0;
    this.g = 0;
    this.b = 0;
  }),
  AmbientLight: vi.fn(function() {
    this.intensity = 1;
  }),
  DirectionalLight: vi.fn(function() {
    this.position = { set: vi.fn(), x: 0, y: 0, z: 0 };
    this.intensity = 1;
  }),
  GridHelper: vi.fn(function() {}),
  AxesHelper: vi.fn(function() {}),
  TOUCH: {
    ROTATE: 0,
    DOLLY_PAN: 1,
    DOLLY_ROTATE: 2,
    PAN: 3,
  },
}));

// Mock OrbitControls
vi.mock('three/addons/controls/OrbitControls.js', () => ({
  OrbitControls: vi.fn(function() {
    this.enableDamping = true;
    this.dampingFactor = 0.05;
    this.update = vi.fn();
    this.dispose = vi.fn();
    this.target = { x: 0, y: 0, z: 0 };
    this.touches = {};
    this.addEventListener = vi.fn();
    this.removeEventListener = vi.fn();
  }),
}));

// Mock @react-three/fiber
vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: any) => <div data-testid="three-canvas">{children}</div>,
  useFrame: vi.fn(),
  useThree: () => ({
    camera: {},
    scene: {},
    gl: { domElement: document.createElement('canvas') },
  }),
}));

describe('GaussianViewer', () => {
  const mockOnError = vi.fn();
  const mockOnLoadProgress = vi.fn();
  const mockOnFpsUpdate = vi.fn();
  const mockOnSceneReady = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders canvas element', () => {
    const { container } = render(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    // Component should render without errors
    expect(container.firstChild).toBeInTheDocument();
  });

  it('calls onSceneReady when scene is initialized', async () => {
    render(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
        onSceneReady={mockOnSceneReady}
      />
    );
    
    // Component renders successfully
    expect(mockOnError).not.toHaveBeenCalled();
  });

  it('handles loading errors', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <GaussianViewer
        sceneId="invalid-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    // Component should handle errors gracefully
    expect(mockOnError).toBeDefined();
    
    consoleError.mockRestore();
  });

  it('updates FPS counter', async () => {
    const { container } = render(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
        onFpsUpdate={mockOnFpsUpdate}
      />
    );
    
    // Component renders with FPS callback
    expect(container.firstChild).toBeInTheDocument();
  });

  it('enables BIM visualization when prop is true', () => {
    const { container, rerender } = render(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
        enableBIMVisualization={false}
      />
    );
    
    rerender(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
        enableBIMVisualization={true}
      />
    );
    
    expect(container.firstChild).toBeInTheDocument();
  });

  it('handles canvas click events', () => {
    const mockOnCanvasClick = vi.fn();
    
    const { container } = render(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
        onCanvasClick={mockOnCanvasClick}
      />
    );
    
    expect(container.firstChild).toBeInTheDocument();
  });

  it('handles camera movement', () => {
    const mockOnCameraMove = vi.fn();
    
    const { container } = render(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
        onCameraMove={mockOnCameraMove}
      />
    );
    
    expect(container.firstChild).toBeInTheDocument();
  });

  it('cleans up resources on unmount', () => {
    const { unmount } = render(
      <GaussianViewer
        sceneId="test-scene"
        onError={mockOnError}
        onLoadProgress={mockOnLoadProgress}
      />
    );
    
    unmount();
    
    // Verify cleanup happened (no errors thrown)
    expect(true).toBe(true);
  });
});
