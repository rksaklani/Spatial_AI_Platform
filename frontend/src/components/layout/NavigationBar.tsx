import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BellIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common/Button';
import { OrganizationSwitcher } from './OrganizationSwitcher';

interface NavigationBarProps {
  organizationName?: string;
  userName?: string;
  notificationCount?: number;
  onLogout?: () => void;
}

/**
 * NavigationBar component - Top horizontal navigation bar
 * 
 * Features:
 * - Logo and organization name display
 * - Main navigation links
 * - Notification bell with badge
 * - User menu dropdown
 * 
 * Requirements: 30.1, 30.4, 43.1
 * Design Reference: ui-design-guide.md - Navigation Structure
 */
export function NavigationBar({
  organizationName = 'Spatial AI Platform',
  userName = 'User',
  notificationCount = 0,
  onLogout,
}: NavigationBarProps) {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const handleLogout = () => {
    setIsUserMenuOpen(false);
    onLogout?.();
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-secondary-bg/90 backdrop-blur-md border-b border-border-color shadow-glass">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Logo and Organization Name */}
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-3 group">
              {/* Logo */}
              <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-lg flex items-center justify-center shadow-glow group-hover:shadow-glow-lg transition-all duration-200">
                <span className="text-white font-bold text-xl">S</span>
              </div>
              {/* Organization Name */}
              <span className="text-text-primary font-display font-bold text-xl group-hover:text-accent-primary transition-colors duration-200">
                {organizationName}
              </span>
            </Link>
          </div>

          {/* Center: Main Navigation Links */}
          {/* <div className="hidden md:flex items-center space-x-8">
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/scenes">Scenes</NavLink>
            <NavLink to="/photos">Photos</NavLink>
            <NavLink to="/help">Help</NavLink>
          </div> */}

          {/* Right: Actions and User Menu */}
          <div className="flex items-center space-x-3">
            {/* Organization Switcher */}
            <OrganizationSwitcher />

            {/* Notification Bell */}
            <div className="relative">
              <Button
                variant="icon"
                icon={<BellIcon className="w-6 h-6" />}
                aria-label="Notifications"
                className="relative"
              />
              {notificationCount > 0 && (
                <span className="absolute top-1 right-1 w-5 h-5 bg-accent-primary text-white text-xs font-bold rounded-full flex items-center justify-center animate-pulse">
                  {notificationCount > 9 ? '9+' : notificationCount}
                </span>
              )}
            </div>

            {/* User Menu */}
            <div className="relative">
              <Button
                variant="icon"
                icon={<UserCircleIcon className="w-8 h-8" />}
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                aria-label="User menu"
                aria-expanded={isUserMenuOpen}
              />

              {/* User Menu Dropdown */}
              {isUserMenuOpen && (
                <>
                  {/* Backdrop */}
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsUserMenuOpen(false)}
                  />

                  {/* Menu */}
                  <div className="absolute right-0 mt-2 w-64 bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-glass z-50 animate-slide-down">
                    {/* User Info */}
                    <div className="px-4 py-3 border-b border-border-color">
                      <p className="text-text-primary font-medium">{userName}</p>
                      <p className="text-text-muted text-sm">{organizationName}</p>
                    </div>

                    {/* Menu Items */}
                    <div className="py-2">
                      <UserMenuItem
                        icon={<UserCircleIcon className="w-5 h-5" />}
                        label="Profile"
                        to="/settings/profile"
                        onClick={() => setIsUserMenuOpen(false)}
                      />
                      <UserMenuItem
                        icon={<Cog6ToothIcon className="w-5 h-5" />}
                        label="Settings"
                        to="/settings"
                        onClick={() => setIsUserMenuOpen(false)}
                      />
                    </div>

                    {/* Logout */}
                    <div className="border-t border-border-color py-2">
                      <button
                        onClick={handleLogout}
                        className="w-full px-4 py-2 text-left text-text-secondary hover:text-accent-primary hover:bg-hover-bg transition-colors duration-200 flex items-center space-x-3"
                      >
                        <ArrowRightOnRectangleIcon className="w-5 h-5" />
                        <span>Logout</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

/**
 * UserMenuItem component for dropdown menu items
 */
interface UserMenuItemProps {
  icon: React.ReactNode;
  label: string;
  to: string;
  onClick?: () => void;
}

function UserMenuItem({ icon, label, to, onClick }: UserMenuItemProps) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="w-full px-4 py-2 text-text-secondary hover:text-text-primary hover:bg-hover-bg transition-colors duration-200 flex items-center space-x-3"
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
}
