import { NavLink } from 'react-router-dom';
import { useState, useRef, KeyboardEvent } from 'react';
import { useAppDispatch } from '../../store/hooks';
import { logout } from '../../store/slices/authSlice';
import {
  HomeIcon,
  CubeIcon,
  PhotoIcon,
  MapIcon,
  DocumentTextIcon,
  UsersIcon,
  BellIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

/**
 * Sidebar navigation component for authenticated pages
 * 
 * Features:
 * - Navigation links with icons and active state
 * - Collapse/expand functionality with toggle button
 * - Keyboard navigation support (Tab, Enter, Arrow keys)
 * - Hidden on mobile (bottom nav shown instead)
 * 
 * Requirements: 24.2, 24.3, 20.2, 18.2
 */
export function Sidebar({ isCollapsed = false, onToggle }: SidebarProps) {
  const dispatch = useAppDispatch();
  const [notificationCount] = useState(3);
  const navItemsRef = useRef<(HTMLAnchorElement | HTMLButtonElement | null)[]>([]);

  const navItems = [
    { to: '/dashboard', icon: HomeIcon, label: 'Dashboard' },
    { to: '/scenes', icon: CubeIcon, label: '3D Scenes' },
    { to: '/photos', icon: PhotoIcon, label: 'Photos' },
    { to: '/geospatial', icon: MapIcon, label: 'Geospatial' },
    { to: '/reports', icon: DocumentTextIcon, label: 'Reports' },
    { to: '/collaboration', icon: UsersIcon, label: 'Collaboration' },
  ];

  const handleLogout = () => {
    dispatch(logout());
  };

  // Keyboard navigation handler for arrow keys
  const handleKeyDown = (e: KeyboardEvent<HTMLElement>, index: number) => {
    const totalItems = navItemsRef.current.filter(Boolean).length;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = (index + 1) % totalItems;
        navItemsRef.current[nextIndex]?.focus();
        break;
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = (index - 1 + totalItems) % totalItems;
        navItemsRef.current[prevIndex]?.focus();
        break;
      case 'Home':
        e.preventDefault();
        navItemsRef.current[0]?.focus();
        break;
      case 'End':
        e.preventDefault();
        const lastIndex = totalItems - 1;
        navItemsRef.current[lastIndex]?.focus();
        break;
    }
  };

  // Handle toggle button keyboard activation
  const handleToggleKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggle?.();
    }
  };

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-secondary-bg/90 backdrop-blur-md border-r border-white/10 shadow-glass transition-all duration-300 z-30 flex flex-col ${
        isCollapsed ? 'w-16' : 'w-64'
      } hidden md:flex`}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Logo Section with Collapse Toggle */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-lg flex items-center justify-center shadow-glow flex-shrink-0">
            <span className="text-white font-bold text-xl">S</span>
          </div>
          {!isCollapsed && (
            <span className="text-text-primary font-display font-bold text-lg truncate">
              Spatial AI
            </span>
          )}
        </div>
        
        {/* Collapse/Expand Toggle Button */}
        {onToggle && (
          <button
            onClick={onToggle}
            onKeyDown={handleToggleKeyDown}
            className="p-1.5 rounded-lg text-text-secondary hover:bg-white/5 hover:text-text-primary transition-all flex-shrink-0"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!isCollapsed}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRightIcon className="w-5 h-5" />
            ) : (
              <ChevronLeftIcon className="w-5 h-5" />
            )}
          </button>
        )}
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 flex flex-col gap-1 p-3 overflow-y-auto" role="menu">
        {navItems.map((item, index) => (
          <NavLink
            key={item.to}
            to={item.to}
            ref={(el) => (navItemsRef.current[index] = el)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-secondary-bg ${
                isActive
                  ? 'bg-accent-primary/20 text-accent-primary shadow-inner-glow'
                  : 'text-text-secondary hover:bg-accent-primary/5 hover:text-accent-primary'
              }`
            }
            role="menuitem"
            aria-label={item.label}
            title={isCollapsed ? item.label : undefined}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
            {!isCollapsed && (
              <span className="text-sm font-medium">{item.label}</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom Section - User Actions */}
      <div className="border-t border-white/10 p-3 space-y-1">
        {/* Notifications */}
        <button
          ref={(el) => (navItemsRef.current[navItems.length] = el)}
          onKeyDown={(e) => handleKeyDown(e, navItems.length)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary hover:bg-accent-primary/5 hover:text-accent-primary transition-all relative focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-secondary-bg"
          aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount} unread)` : ''}`}
          title={isCollapsed ? 'Notifications' : undefined}
        >
          <BellIcon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          {!isCollapsed && (
            <span className="text-sm font-medium">Notifications</span>
          )}
          {notificationCount > 0 && (
            <span 
              className="absolute top-2 left-8 w-4 h-4 bg-accent-primary text-white text-xs font-bold rounded-full flex items-center justify-center"
              aria-label={`${notificationCount} unread notifications`}
            >
              {notificationCount > 9 ? '9+' : notificationCount}
            </span>
          )}
        </button>

        {/* Settings */}
        <NavLink
          ref={(el) => (navItemsRef.current[navItems.length + 1] = el)}
          onKeyDown={(e) => handleKeyDown(e, navItems.length + 1)}
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-secondary-bg ${
              isActive
                ? 'bg-accent-primary/20 text-accent-primary shadow-inner-glow'
                : 'text-text-secondary hover:bg-accent-primary/5 hover:text-accent-primary'
            }`
          }
          aria-label="Settings"
          title={isCollapsed ? 'Settings' : undefined}
        >
          <Cog6ToothIcon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          {!isCollapsed && (
            <span className="text-sm font-medium">Settings</span>
          )}
        </NavLink>

        {/* User Profile */}
        <div className="pt-2 border-t border-white/10">
          <div 
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary"
            role="status"
            aria-label="Current user"
          >
            <UserCircleIcon className="w-8 h-8 flex-shrink-0" aria-hidden="true" />
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">User</p>
                <p className="text-xs text-text-muted truncate">user@example.com</p>
              </div>
            )}
          </div>
        </div>

        {/* Logout */}
        <button
          ref={(el) => (navItemsRef.current[navItems.length + 2] = el)}
          onKeyDown={(e) => handleKeyDown(e, navItems.length + 2)}
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary hover:bg-red-500/10 hover:text-red-400 transition-all focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2 focus:ring-offset-secondary-bg"
          aria-label="Logout"
          title={isCollapsed ? 'Logout' : undefined}
        >
          <ArrowRightOnRectangleIcon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          {!isCollapsed && (
            <span className="text-sm font-medium">Logout</span>
          )}
        </button>
      </div>
    </aside>
  );
}
