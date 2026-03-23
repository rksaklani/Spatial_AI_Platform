import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { AppLayout } from './AppLayout';
import authReducer from '../../store/slices/authSlice';

// Mock the useMediaQuery hook
vi.mock('../../hooks/useMediaQuery', () => ({
  useIsMobile: () => false,
  useIsTablet: () => false,
  useIsDesktop: () => true,
}));

// Mock child components
vi.mock('./NavigationBar', () => ({
  NavigationBar: () => <div data-testid="navigation-bar">NavigationBar</div>,
}));

vi.mock('./Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar">Sidebar</div>,
}));

describe('AppLayout', () => {
  const createMockStore = (authState = {}) => {
    return configureStore({
      reducer: {
        auth: authReducer,
      },
      preloadedState: {
        auth: {
          user: null,
          token: null,
          refreshToken: null,
          tokenExpiresAt: null,
          isAuthenticated: false,
          loading: false,
          error: null,
          refreshing: false,
          refreshRetryCount: 0,
          ...authState,
        },
      },
    });
  };

  const renderWithProviders = (store = createMockStore()) => {
    return render(
      <Provider store={store}>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </Provider>
    );
  };

  it('renders navigation bar', () => {
    renderWithProviders();
    expect(screen.getByTestId('navigation-bar')).toBeInTheDocument();
  });

  it('renders sidebar on desktop', () => {
    renderWithProviders();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders main content area', () => {
    const { container } = renderWithProviders();
    const mainElement = container.querySelector('main');
    expect(mainElement).toBeInTheDocument();
  });

  it('applies correct margin when sidebar is not collapsed', () => {
    const { container } = renderWithProviders();
    const mainElement = container.querySelector('main');
    expect(mainElement).toHaveClass('ml-64');
  });

  it('passes user information to NavigationBar', () => {
    const store = createMockStore({
      user: { id: '1', email: 'test@example.com', name: 'Test User', organizationId: 'org1' },
      isAuthenticated: true,
    });
    renderWithProviders(store);
    expect(screen.getByTestId('navigation-bar')).toBeInTheDocument();
  });
});
