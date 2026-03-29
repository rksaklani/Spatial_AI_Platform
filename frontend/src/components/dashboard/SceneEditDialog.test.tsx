import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { SceneEditDialog } from './SceneEditDialog';
import { baseApi } from '../../store/api/baseApi';
import type { SceneMetadata } from '../../types/scene.types';

// Mock scene data
const mockScene: SceneMetadata = {
  sceneId: 'test-scene-123',
  organizationId: 'org-123',
  userId: 'user-123',
  name: 'Test Scene',
  sourceType: 'video',
  sourceFormat: 'mp4',
  status: 'completed',
  bounds: {
    min: [0, 0, 0],
    max: [10, 10, 10],
  },
  tileCount: 100,
  gaussianCount: 1000000,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

// Create a mock store
const createMockStore = () => {
  return configureStore({
    reducer: {
      [baseApi.reducerPath]: baseApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware),
  });
};

describe('SceneEditDialog', () => {
  let mockStore: ReturnType<typeof createMockStore>;
  let mockOnClose: ReturnType<typeof vi.fn>;
  let mockOnSuccess: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockStore = createMockStore();
    mockOnClose = vi.fn();
    mockOnSuccess = vi.fn();
  });

  it('should not render when open is false', () => {
    const { container } = render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={false}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    expect(container.firstChild).toBeNull();
  });

  it('should render when open is true', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    expect(screen.getByText('Edit Scene')).toBeInTheDocument();
    expect(screen.getByLabelText(/Scene Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
  });

  it('should initialize form with scene data', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const nameInput = screen.getByLabelText(/Scene Name/i) as HTMLInputElement;
    expect(nameInput.value).toBe('Test Scene');
  });

  it('should show validation error for empty name', async () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const nameInput = screen.getByLabelText(/Scene Name/i);
    const submitButton = screen.getByRole('button', { name: /Save Changes/i });

    // Clear the name input
    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Scene name is required')).toBeInTheDocument();
    });
  });

  it('should show validation error for name exceeding max length', async () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const nameInput = screen.getByLabelText(/Scene Name/i);
    const submitButton = screen.getByRole('button', { name: /Save Changes/i });

    // Enter a name that's too long
    const longName = 'a'.repeat(256);
    fireEvent.change(nameInput, { target: { value: longName } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Scene name must be less than 255 characters')).toBeInTheDocument();
    });
  });

  it('should show character count for name field', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    expect(screen.getByText('10/255 characters')).toBeInTheDocument();
  });

  it('should show character count for description field', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    expect(screen.getByText('0/1000 characters')).toBeInTheDocument();
  });

  it('should call onClose when cancel button is clicked', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when close icon is clicked', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const closeButton = screen.getByLabelText('Close dialog');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when backdrop is clicked', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const backdrop = screen.getByText('Edit Scene').parentElement?.parentElement?.previousSibling;
    if (backdrop) {
      fireEvent.click(backdrop);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    }
  });

  it('should toggle public/private status', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const publicToggle = screen.getByText('Make scene public').closest('label');
    expect(publicToggle).toBeInTheDocument();

    if (publicToggle) {
      const checkbox = publicToggle.querySelector('input[type="checkbox"]') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);

      fireEvent.click(publicToggle);
      expect(checkbox.checked).toBe(true);
    }
  });

  it('should update character count when typing in name field', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const nameInput = screen.getByLabelText(/Scene Name/i);
    fireEvent.change(nameInput, { target: { value: 'New Scene Name' } });

    expect(screen.getByText('14/255 characters')).toBeInTheDocument();
  });

  it('should update character count when typing in description field', () => {
    render(
      <Provider store={mockStore}>
        <SceneEditDialog
          open={true}
          scene={mockScene}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      </Provider>
    );

    const descriptionInput = screen.getByLabelText(/Description/i);
    fireEvent.change(descriptionInput, { target: { value: 'Test description' } });

    expect(screen.getByText('16/1000 characters')).toBeInTheDocument();
  });
});
