import { Outlet, NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  HomeIcon,
  CubeIcon,
  PhotoIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { NavigationBar } from './NavigationBar';
import { Sidebar } from './Sidebar';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { logout } from '../../store/slices/authSlice';
import { useIsMobile } from '../../hooks/useMediaQuery';

/**
 * Main application layout component
 * Provides the shell for authenticated pages with:
 * - Top navigation bar with logo, links, notifications, user menu
 * - Responsive sidebar (collapsible on mobile, bottom nav on mobile)
 * - Main content area with proper spacing
 * 
 * Requirements: 18.2, 18.3, 24.1, 24.2
 */
export function AppLayout() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user);
  const theme = useAppSelector((state) => state.preferences.theme);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  
  const isMobile = useIsMobile();

  // Apply theme to document
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const handleLogout = () => {
    dispatch(logout());
  };

  // On mobile, sidebar is hidden by default
  const shouldShowSidebar = !isMobile;

  return (
    <div className="min-h-screen bg-primary-bg">
      {/* Top Navigation Bar - Fixed at top */}
      <NavigationBar
        organizationName="Spatial AI Platform"
        userName={user?.name || 'User'}
        notificationCount={0}
        onLogout={handleLogout}
      />

      {/* Sidebar - Fixed on left (hidden on mobile) */}
      {shouldShowSidebar && (
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />
      )}

      {/* Main content area - Offset by navbar and sidebar */}
      <main
        className={`transition-all duration-300 pt-20 ${
          shouldShowSidebar
            ? isSidebarCollapsed
              ? 'ml-16'
              : 'ml-64'
            : 'ml-0'
        } ${isMobile ? 'pb-20' : ''}`}
      >
        <div className="p-4 md:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Mobile Bottom Navigation - Only visible on mobile */}
      {isMobile && <MobileBottomNav />}
    </div>
  );
}

/**
 * Mobile bottom navigation component
 * Displays navigation links at the bottom of the screen on mobile devices
 * Uses 44px minimum touch targets for accessibility
 * 
 * Requirements: 18.2, 24.2, 24.5
 */
function MobileBottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-secondary-bg/95 backdrop-blur-xl border-t border-border-color safe-area-inset-bottom">
      <div className="flex items-center justify-around px-2 py-2">
        <MobileNavButton
          to="/app/dashboard"
          icon={<HomeIcon className="w-6 h-6" />}
          label="Home"
        />
        <MobileNavButton
          to="/app/scenes"
          icon={<CubeIcon className="w-6 h-6" />}
          label="Scenes"
        />
        <MobileNavButton
          to="/app/photos"
          icon={<PhotoIcon className="w-6 h-6" />}
          label="Photos"
        />
        <MobileNavButton
          to="/app/settings"
          icon={<Cog6ToothIcon className="w-6 h-6" />}
          label="Settings"
        />
      </div>
    </nav>
  );
}

/**
 * Mobile navigation button component
 * Ensures 44px minimum touch target for accessibility
 */
interface MobileNavButtonProps {
  to: string;
  icon: React.ReactNode;
  label: string;
}

function MobileNavButton({ to, icon, label }: MobileNavButtonProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex flex-col items-center justify-center min-w-[44px] min-h-[44px] px-3 py-2 rounded-lg transition-colors duration-200 ${
          isActive
            ? 'text-accent-primary'
            : 'text-text-secondary hover:text-text-primary'
        }`
      }
    >
      {icon}
      <span className="text-xs font-medium mt-1">{label}</span>
    </NavLink>
  );
}
