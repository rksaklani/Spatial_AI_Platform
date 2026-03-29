import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { Sidebar } from './Sidebar';
import authReducer from '../../store/slices/authSlice';

// Mock store setup
const createMockStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
    },
    preloadedState: {
      auth: {
        user: { id: '1', name: 'Test User', email: 'test@example.com', organizationId: 'test-org' },
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        tokenExpiresAt: Date.now() + 900000,
        isAuthenticated: true,
        loading: false,
        error: null,
        refreshing: false,
        refreshRetryCount: 0,
      },
    },
  });
};

const renderSidebar = (props = {}) => {
  const store = createMockStore();
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <Sidebar {...props} />
      </BrowserRouter>
    </Provider>
  );
};

describe('Sidebar', () => {
  it('renders navigation links', () => {
    renderSidebar();
    
    expect(screen.getByRole('menuitem', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /3d scenes/i })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /photos/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();
  });

  it('shows full labels when expanded', () => {
    renderSidebar({ isCollapsed: false });
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('3D Scenes')).toBeInTheDocument();
    expect(screen.getByText('Photos')).toBeInTheDocument();
  });

  it('hides labels when collapsed', () => {
    renderSidebar({ isCollapsed: true });
    
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.queryByText('3D Scenes')).not.toBeInTheDocument();
  });

  it('calls onToggle when collapse button is clicked', () => {
    const onToggle = vi.fn();
    renderSidebar({ isCollapsed: false, onToggle });
    
    const toggleButton = screen.getByRole('button', { name: /collapse sidebar/i });
    fireEvent.click(toggleButton);
    
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('supports keyboard navigation with arrow keys', () => {
    renderSidebar();
    
    const dashboardLink = screen.getByRole('menuitem', { name: /dashboard/i });
    const scenesLink = screen.getByRole('menuitem', { name: /3d scenes/i });
    
    dashboardLink.focus();
    expect(document.activeElement).toBe(dashboardLink);
    
    // Press ArrowDown to move to next item
    fireEvent.keyDown(dashboardLink, { key: 'ArrowDown' });
    expect(document.activeElement).toBe(scenesLink);
  });

  it('supports keyboard activation of toggle button', () => {
    const onToggle = vi.fn();
    renderSidebar({ isCollapsed: false, onToggle });
    
    const toggleButton = screen.getByRole('button', { name: /collapse sidebar/i });
    
    // Press Enter
    fireEvent.keyDown(toggleButton, { key: 'Enter' });
    expect(onToggle).toHaveBeenCalledTimes(1);
    
    // Press Space
    fireEvent.keyDown(toggleButton, { key: ' ' });
    expect(onToggle).toHaveBeenCalledTimes(2);
  });

  it('displays notification badge when there are notifications', () => {
    renderSidebar();
    
    const notificationButton = screen.getByRole('button', { name: /notifications/i });
    expect(notificationButton).toBeInTheDocument();
    
    // Check for badge (the component has 3 notifications by default)
    const badge = screen.getByText('3');
    expect(badge).toBeInTheDocument();
  });

  it('has proper ARIA labels for accessibility', () => {
    renderSidebar();
    
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('applies focus styles for keyboard navigation', () => {
    renderSidebar();
    
    const dashboardLink = screen.getByRole('menuitem', { name: /dashboard/i });
    expect(dashboardLink).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-accent-primary');
  });
});
