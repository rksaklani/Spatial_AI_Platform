import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { ViewerPage } from '../ViewerPage';

// Mock baseApi
vi.mock('../../store/api/baseApi', () => ({
  baseApi: {
    reducerPath: 'api',
    reducer: () => ({}),
    middleware: () => (next: any) => (action: any) => next(action),
    endpoints: {},
    injectEndpoints: vi.fn(),
  },
}));

// Mock sceneApi
const mockUseGetSceneByIdQuery = vi.fn();
vi.mock('../../store/api/sceneApi', () => ({
  useGetSceneByIdQuery: () => mockUseGetSceneByIdQuery(),
}));

// Mock components
vi.mock('../../components/GaussianViewer', () => ({
  GaussianViewer: ({ sceneId }: any) => <div data-testid="gaussian-viewer">Gaussian Viewer: {sceneId}</div>,
}));

vi.mock('../../components/ModelViewer', () => ({
  ModelViewer: ({ sceneId, modelType }: any) => (
    <div data-testid="model-viewer">Model Viewer: {sceneId} ({modelType})</div>
  ),
}));

vi.mock('../../components/viewer', () => ({
  ViewerToolbar: () => <div data-testid="viewer-toolbar">Toolbar</div>,
  AnnotationToolbar: () => <div data-testid="annotation-toolbar">Annotations</div>,
  AnnotationPreview: () => <div data-testid="annotation-preview">Preview</div>,
}));

vi.mock('../../components/CollaborationOverlay', () => ({
  CollaborationOverlay: () => <div data-testid="collaboration-overlay">Collaboration</div>,
}));

vi.mock('../../components/collaboration/CollaborationPanel', () => ({
  CollaborationPanel: () => <div data-testid="collaboration-panel">Panel</div>,
}));

vi.mock('../../components/sharing/ShareDialog', () => ({
  ShareDialog: () => <div data-testid="share-dialog">Share</div>,
}));

// Mock hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ sceneId: 'test-scene-123' }),
  };
});

vi.mock('../../hooks/useAnnotationCreation', () => ({
  useAnnotationCreation: () => ({
    points: [],
    previewPoints: [],
    handleClick: vi.fn(),
    handleDoubleClick: vi.fn(),
    handleMouseMove: vi.fn(),
    cancelCreation: vi.fn(),
    cleanup: vi.fn(),
  }),
}));

vi.mock('../../hooks/useCollaboration', () => ({
  useCollaboration: () => ({
    connectionStatus: 'connected',
    activeUsers: [],
    sendCursorPosition: vi.fn(),
    broadcastAnnotationCreated: vi.fn(),
  }),
}));

vi.mock('../../services/websocket.service', () => ({
  websocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
  },
}));

describe('ViewerPage', () => {
  const createMockStore = () => {
    return configureStore({
      reducer: {
        auth: () => ({ token: 'test-token', user: null }),
        api: () => ({ queries: {} }),
      },
      middleware: (getDefaultMiddleware) => 
        getDefaultMiddleware().concat(() => (next: any) => (action: any) => next(action)),
    });
  };

  const renderViewer = () => {
    const store = createMockStore();
    return render(
      <Provider store={store}>
        <BrowserRouter>
          <ViewerPage />
        </BrowserRouter>
      </Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock return value
    mockUseGetSceneByIdQuery.mockReturnValue({
      data: { _id: 'test-scene-123', name: 'Test Scene', format: 'splat', status: 'completed' },
      isLoading: false,
      error: null,
    });
  });

  it('renders Gaussian viewer for splat format', () => {
    mockUseGetSceneByIdQuery.mockReturnValue({
      data: { _id: 'test-scene-123', format: 'splat', name: 'Test Scene', status: 'completed' },
      isLoading: false,
      error: null,
    });
    
    renderViewer();
    expect(screen.getByTestId('gaussian-viewer')).toBeInTheDocument();
  });

  it('renders Model viewer for GLB format', () => {
    mockUseGetSceneByIdQuery.mockReturnValue({
      data: { _id: 'test-scene-123', format: 'glb', name: 'Test Scene', fileUrl: '/test.glb', status: 'completed' },
      isLoading: false,
      error: null,
    });
    
    renderViewer();
    expect(screen.getByTestId('model-viewer')).toBeInTheDocument();
    expect(screen.getByText(/glb/i)).toBeInTheDocument();
  });

  it('renders Model viewer for GLTF format', () => {
    mockUseGetSceneByIdQuery.mockReturnValue({
      data: { _id: 'test-scene-123', format: 'gltf', name: 'Test Scene', fileUrl: '/test.gltf', status: 'completed' },
      isLoading: false,
      error: null,
    });
    
    renderViewer();
    expect(screen.getByTestId('model-viewer')).toBeInTheDocument();
  });

  it('renders Model viewer for OBJ format', () => {
    mockUseGetSceneByIdQuery.mockReturnValue({
      data: { _id: 'test-scene-123', format: 'obj', name: 'Test Scene', fileUrl: '/test.obj', status: 'completed' },
      isLoading: false,
      error: null,
    });
    
    renderViewer();
    expect(screen.getByTestId('model-viewer')).toBeInTheDocument();
  });

  it('renders Model viewer for PLY format', () => {
    mockUseGetSceneByIdQuery.mockReturnValue({
      data: { _id: 'test-scene-123', format: 'ply', name: 'Test Scene', fileUrl: '/test.ply', status: 'completed' },
      isLoading: false,
      error: null,
    });
    
    renderViewer();
    expect(screen.getByTestId('model-viewer')).toBeInTheDocument();
  });

  it('renders viewer toolbar', () => {
    renderViewer();
    expect(screen.getByTestId('viewer-toolbar')).toBeInTheDocument();
  });

  it('renders annotation toolbar', () => {
    renderViewer();
    expect(screen.getByTestId('annotation-toolbar')).toBeInTheDocument();
  });

  it('renders collaboration overlay', () => {
    renderViewer();
    expect(screen.getByTestId('collaboration-overlay')).toBeInTheDocument();
  });

  it('renders collaboration panel', () => {
    renderViewer();
    expect(screen.getByTestId('collaboration-panel')).toBeInTheDocument();
  });

  it('renders share button', () => {
    renderViewer();
    expect(screen.getByTitle('Share scene')).toBeInTheDocument();
  });
});
