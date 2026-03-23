import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { NavigationBar } from './NavigationBar';

// Wrapper component to provide router context
const RouterWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('NavigationBar', () => {
  it('renders organization name', () => {
    render(
      <RouterWrapper>
        <NavigationBar organizationName="Test Organization" />
      </RouterWrapper>
    );
    
    expect(screen.getByText('Test Organization')).toBeInTheDocument();
  });

  it('displays notification badge when count > 0', () => {
    render(
      <RouterWrapper>
        <NavigationBar notificationCount={5} />
      </RouterWrapper>
    );
    
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays 9+ for notification count > 9', () => {
    render(
      <RouterWrapper>
        <NavigationBar notificationCount={15} />
      </RouterWrapper>
    );
    
    expect(screen.getByText('9+')).toBeInTheDocument();
  });

  it('calls onThemeToggle when theme button is clicked', () => {
    const handleThemeToggle = vi.fn();
    
    render(
      <RouterWrapper>
        <NavigationBar onThemeToggle={handleThemeToggle} />
      </RouterWrapper>
    );
    
    const themeButton = screen.getByLabelText(/switch to light mode/i);
    fireEvent.click(themeButton);
    
    expect(handleThemeToggle).toHaveBeenCalledTimes(1);
  });

  it('opens user menu when user icon is clicked', () => {
    render(
      <RouterWrapper>
        <NavigationBar userName="John Doe" />
      </RouterWrapper>
    );
    
    const userButton = screen.getByLabelText('User menu');
    fireEvent.click(userButton);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('calls onLogout when logout button is clicked', () => {
    const handleLogout = vi.fn();
    
    render(
      <RouterWrapper>
        <NavigationBar onLogout={handleLogout} />
      </RouterWrapper>
    );
    
    // Open user menu
    const userButton = screen.getByLabelText('User menu');
    fireEvent.click(userButton);
    
    // Click logout
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);
    
    expect(handleLogout).toHaveBeenCalledTimes(1);
  });

  it('closes user menu when backdrop is clicked', () => {
    render(
      <RouterWrapper>
        <NavigationBar userName="John Doe" />
      </RouterWrapper>
    );
    
    // Open user menu
    const userButton = screen.getByLabelText('User menu');
    fireEvent.click(userButton);
    
    expect(screen.getByText('Profile')).toBeInTheDocument();
    
    // Click backdrop
    const backdrop = document.querySelector('.fixed.inset-0');
    if (backdrop) {
      fireEvent.click(backdrop);
    }
    
    // Menu should be closed (Profile link should not be visible)
    expect(screen.queryByText('Profile')).not.toBeInTheDocument();
  });

  it('renders all navigation links', () => {
    render(
      <RouterWrapper>
        <NavigationBar />
      </RouterWrapper>
    );
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Scenes')).toBeInTheDocument();
    expect(screen.getByText('Photos')).toBeInTheDocument();
    expect(screen.getByText('Help')).toBeInTheDocument();
  });

  it('displays correct theme icon based on isDarkMode prop', () => {
    const { rerender } = render(
      <RouterWrapper>
        <NavigationBar isDarkMode={true} />
      </RouterWrapper>
    );
    
    expect(screen.getByLabelText('Switch to light mode')).toBeInTheDocument();
    
    rerender(
      <RouterWrapper>
        <NavigationBar isDarkMode={false} />
      </RouterWrapper>
    );
    
    expect(screen.getByLabelText('Switch to dark mode')).toBeInTheDocument();
  });
});
