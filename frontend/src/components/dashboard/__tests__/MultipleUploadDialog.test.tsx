import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MultipleUploadDialog } from '../MultipleUploadDialog';
import axios from 'axios';

vi.mock('axios');

describe('MultipleUploadDialog', () => {
  const mockOnClose = vi.fn();
  const mockOnUploadComplete = vi.fn();
  
  const createMockStore = () => {
    return configureStore({
      reducer: {
        auth: () => ({ token: 'test-token', user: null }),
      },
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderDialog = (props = {}) => {
    const store = createMockStore();
    return render(
      <Provider store={store}>
        <MultipleUploadDialog
          open={true}
          onClose={mockOnClose}
          onUploadComplete={mockOnUploadComplete}
          {...props}
        />
      </Provider>
    );
  };

  it('renders when open', () => {
    renderDialog();
    expect(screen.getByText(/Upload Multiple/i)).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    const { container } = renderDialog({ open: false });
    expect(container.firstChild).toBeNull();
  });

  it('accepts multiple file selection', () => {
    renderDialog();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toHaveAttribute('multiple');
  });

  it('displays selected files', () => {
    renderDialog();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const file1 = new File(['video1'], 'test1.mp4', { type: 'video/mp4' });
    const file2 = new File(['video2'], 'test2.mp4', { type: 'video/mp4' });
    
    fireEvent.change(input, { target: { files: [file1, file2] } });
    
    expect(screen.getByText('test1.mp4')).toBeInTheDocument();
    expect(screen.getByText('test2.mp4')).toBeInTheDocument();
  });

  it('validates file types for video mode', () => {
    renderDialog({ acceptedTypes: 'video' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Verify accept attribute only allows videos
    expect(input.accept).toBe('.mp4,.mov,.avi,.webm,.mkv');
  });

  it('validates file types for image mode', () => {
    renderDialog({ acceptedTypes: 'image' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Verify accept attribute only allows images
    expect(input.accept).toBe('.jpg,.jpeg,.png,.webp,.tiff');
  });

  it('enforces maximum file count', () => {
    renderDialog();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const files = Array.from({ length: 25 }, (_, i) => 
      new File(['video'], `test${i}.mp4`, { type: 'video/mp4' })
    );
    
    fireEvent.change(input, { target: { files } });
    
    expect(screen.getByText(/Maximum.*files allowed/i)).toBeInTheDocument();
  });

  it('allows removing files before upload', () => {
    renderDialog();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const file = new File(['video'], 'test.mp4', { type: 'video/mp4' });
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(screen.getByText('test.mp4')).toBeInTheDocument();
    
    const removeButton = screen.getByTitle('Remove file');
    fireEvent.click(removeButton);
    
    expect(screen.queryByText('test.mp4')).not.toBeInTheDocument();
  });

  it('shows upload progress for each file', async () => {
    const mockPost = vi.fn(() => 
      new Promise((resolve) => {
        setTimeout(() => resolve({ data: { sceneId: 'test-scene' } }), 100);
      })
    );
    (axios.post as any) = mockPost;
    (axios.CancelToken as any) = { source: () => ({ token: 'test-token', cancel: vi.fn() }) };

    renderDialog();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const file = new File(['video'], 'test.mp4', { type: 'video/mp4' });
    fireEvent.change(input, { target: { files: [file] } });
    
    const uploadButton = screen.getByRole('button', { name: /Upload.*Files/i });
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('⬆️')).toBeInTheDocument();
    });
  });

  it('calls onUploadComplete with all scene IDs', async () => {
    const mockPost = vi.fn(() => 
      Promise.resolve({ data: { sceneId: 'test-scene' } })
    );
    (axios.post as any) = mockPost;
    (axios.CancelToken as any) = { source: () => ({ token: 'test-token', cancel: vi.fn() }) };

    renderDialog();
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const file = new File(['video'], 'test.mp4', { type: 'video/mp4' });
    fireEvent.change(input, { target: { files: [file] } });
    
    const uploadButton = screen.getByRole('button', { name: /Upload.*Files/i });
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(mockOnUploadComplete).toHaveBeenCalledWith(['test-scene']);
    }, { timeout: 3000 });
  });
});
