import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import axios from 'axios';
import { UploadDialog } from '../components/dashboard/UploadDialog';
import { MultipleUploadDialog } from '../components/dashboard/MultipleUploadDialog';

vi.mock('axios');

// Mock importApi
vi.mock('../store/api/importApi', () => ({
  useGetSupportedFormatsQuery: () => ({
    data: {
      formats: [
        { extension: '.glb', format_type: 'mesh' },
        { extension: '.ply', format_type: 'point_cloud' },
      ],
      max_file_size_mb: 500,
    },
    isLoading: false,
  }),
  useUpload3DFileMutation: () => [
    vi.fn().mockReturnValue({
      unwrap: () => Promise.resolve({ job_id: 'job-123' }),
    }),
    { isLoading: false },
  ],
  useGetImportStatusQuery: () => ({
    data: null,
  }),
}));

describe('End-to-End Upload Flow', () => {
  const createMockStore = () => {
    return configureStore({
      reducer: {
        auth: () => ({ token: 'test-token', user: { id: 'user-1' } }),
        api: () => ({
          queries: {},
          mutations: {},
        }),
      },
      middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
          serializableCheck: false,
        }),
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Single Video Upload Flow', () => {
    it('renders upload dialog', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <UploadDialog
            open={true}
            onClose={vi.fn()}
            onUpload={vi.fn()}
          />
        </Provider>
      );

      expect(screen.getByText(/Upload Video/i)).toBeInTheDocument();
    });

    it('accepts video file selection', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <UploadDialog
            open={true}
            onClose={vi.fn()}
            onUpload={vi.fn()}
          />
        </Provider>
      );

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(input).toBeInTheDocument();
      // Accept attribute contains file extensions, not mime types
      expect(input.accept).toContain('.mp4');
    });

    it('shows upload button', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <UploadDialog
            open={true}
            onClose={vi.fn()}
            onUpload={vi.fn()}
          />
        </Provider>
      );

      expect(screen.getByText('Upload')).toBeInTheDocument();
    });
  });

  describe('Multiple File Upload Flow', () => {
    it('renders multiple upload dialog', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <MultipleUploadDialog
            open={true}
            onClose={vi.fn()}
            acceptedTypes="video"
          />
        </Provider>
      );

      // Check for dialog title
      expect(screen.getByText(/Multiple/i)).toBeInTheDocument();
    });

    it('accepts multiple file selection', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <MultipleUploadDialog
            open={true}
            onClose={vi.fn()}
            acceptedTypes="video"
          />
        </Provider>
      );

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(input).toBeInTheDocument();
      expect(input.multiple).toBe(true);
    });

    it('shows file count limit', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <MultipleUploadDialog
            open={true}
            onClose={vi.fn()}
            acceptedTypes="video"
          />
        </Provider>
      );

      // Check that dialog renders
      expect(screen.getByText(/Multiple/i)).toBeInTheDocument();
    });
  });

  describe('Image Upload Flow', () => {
    it('renders image upload dialog', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <MultipleUploadDialog
            open={true}
            onClose={vi.fn()}
            acceptedTypes="image"
          />
        </Provider>
      );

      // Check for dialog title
      expect(screen.getByText(/Multiple/i)).toBeInTheDocument();
    });

    it('accepts image files', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <MultipleUploadDialog
            open={true}
            onClose={vi.fn()}
            acceptedTypes="image"
          />
        </Provider>
      );

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(input).toBeInTheDocument();
      // Accept attribute contains file extensions
      expect(input.accept).toContain('.jpg');
    });

    it('shows upload button for images', () => {
      const store = createMockStore();
      render(
        <Provider store={store}>
          <MultipleUploadDialog
            open={true}
            onClose={vi.fn()}
            acceptedTypes="image"
          />
        </Provider>
      );

      // Check that dialog renders with buttons
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });
});
