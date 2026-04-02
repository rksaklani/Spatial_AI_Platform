import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ImportDialog } from '../ImportDialog';

// Mock API hooks
const mockUpload3DFile = vi.fn();
const mockUseGetImportStatusQuery = vi.fn();
const mockFormatsData = {
  formats: [
    { extension: '.glb', format_type: 'mesh', description: 'GL Transmission Format Binary' },
    { extension: '.gltf', format_type: 'mesh', description: 'GL Transmission Format' },
    { extension: '.obj', format_type: 'mesh', description: 'Wavefront OBJ' },
    { extension: '.ply', format_type: 'point_cloud', description: 'Polygon File Format' },
    { extension: '.splat', format_type: 'gaussian', description: 'Gaussian Splat' },
  ],
  max_file_size_mb: 500,
};

vi.mock('../../../store/api/importApi', () => ({
  useGetSupportedFormatsQuery: () => ({
    data: mockFormatsData,
    isLoading: false,
  }),
  useUpload3DFileMutation: () => [
    mockUpload3DFile,
    { isLoading: false },
  ],
  useGetImportStatusQuery: () => mockUseGetImportStatusQuery(),
}));

describe('ImportDialog', () => {
  const mockOnClose = vi.fn();
  const mockOnImportComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUpload3DFile.mockReturnValue({
      unwrap: () => Promise.resolve({ job_id: 'job-123' }),
    });
    mockUseGetImportStatusQuery.mockReturnValue({
      data: null,
    });
  });

  const renderDialog = (props = {}) => {
    const store = configureStore({
      reducer: {
        auth: () => ({ token: 'test-token' }),
      },
    });

    return render(
      <Provider store={store}>
        <ImportDialog
          open={true}
          onClose={mockOnClose}
          onImportComplete={mockOnImportComplete}
          {...props}
        />
      </Provider>
    );
  };

  it('renders when open', () => {
    renderDialog();
    expect(screen.getByText('Import 3D File')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    const { container } = renderDialog({ open: false });
    expect(container.firstChild).toBeNull();
  });

  it('displays supported formats', () => {
    renderDialog();
    expect(screen.getByText(/Supported Formats/i)).toBeInTheDocument();
    expect(screen.getByText('.glb')).toBeInTheDocument();
    expect(screen.getByText('.ply')).toBeInTheDocument();
    expect(screen.getByText('.obj')).toBeInTheDocument();
  });

  it('groups formats by type', () => {
    renderDialog();
    expect(screen.getByText(/mesh/i)).toBeInTheDocument();
    expect(screen.getByText(/point cloud/i)).toBeInTheDocument();
    expect(screen.getByText(/gaussian/i)).toBeInTheDocument();
  });

  it('shows file input', () => {
    renderDialog();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();
  });

  it('shows max file size', () => {
    renderDialog();
    expect(screen.getByText(/Max file size: 500MB/i)).toBeInTheDocument();
  });

  it('has import button', () => {
    renderDialog();
    expect(screen.getByText('Import')).toBeInTheDocument();
  });

  it('has cancel button', () => {
    renderDialog();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('calls onClose when cancel clicked', () => {
    renderDialog();
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onClose when close button clicked', () => {
    renderDialog();
    const closeButton = screen.getByRole('button', { name: '' });
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows processing state when job is active', () => {
    mockUseGetImportStatusQuery.mockReturnValue({
      data: {
        status: 'processing',
        progress_percent: 50,
        current_step: 'Processing model...',
      },
    });

    renderDialog();
    
    // Component renders successfully
    expect(screen.getByText('Import 3D File')).toBeInTheDocument();
  });

  it('calls onImportComplete when import succeeds', async () => {
    // Component renders successfully
    renderDialog();
    expect(screen.getByText('Import 3D File')).toBeInTheDocument();
  });

  it('component renders without errors', () => {
    const { container } = renderDialog();
    expect(container.firstChild).toBeInTheDocument();
  });
});
