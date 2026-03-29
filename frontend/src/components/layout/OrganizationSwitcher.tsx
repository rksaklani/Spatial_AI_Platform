import { useState, useRef, useEffect } from 'react';
import { useGetOrganizationsQuery, useSwitchOrganizationMutation } from '../../store/api/organizationApi';
import { useAppSelector } from '../../store/hooks';
import { BuildingOfficeIcon, CheckIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

export function OrganizationSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const currentOrgId = useAppSelector(state => state.auth.user?.organizationId);
  const { data: organizations = [] } = useGetOrganizationsQuery();
  const [switchOrg, { isLoading }] = useSwitchOrganizationMutation();

  const currentOrg = organizations.find(org => org.id === currentOrgId);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleSwitch = async (orgId: string) => {
    if (orgId === currentOrgId) {
      setIsOpen(false);
      return;
    }

    try {
      await switchOrg(orgId).unwrap();
      setIsOpen(false);
      // Reload page to refresh all data with new org context
      window.location.reload();
    } catch (error) {
      console.error('Failed to switch organization:', error);
    }
  };

  if (organizations.length <= 1) {
    // Don't show switcher if user only has one org
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary-bg/70 backdrop-blur-sm border border-border-color hover:border-accent-primary hover:shadow-glow transition-all duration-200"
        disabled={isLoading}
      >
        <BuildingOfficeIcon className="w-5 h-5 text-accent-primary" />
        <span className="text-sm font-medium text-text-primary">
          {currentOrg?.name || 'Select Organization'}
        </span>
        <ChevronDownIcon
          className={`w-4 h-4 text-accent-primary transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          
          {/* Dropdown Menu */}
          <div className="absolute top-full left-0 mt-2 w-72 sm:w-80 bg-secondary-bg/95 backdrop-blur-xl rounded-2xl border border-accent-primary/30 shadow-glow-lg z-50 overflow-hidden animate-slide-down">
            <div className="p-3 bg-gradient-to-br from-accent-primary/10 to-accent-secondary/10 border-b border-accent-primary/20">
              <p className="text-xs text-text-muted font-medium">Switch Organization</p>
            </div>
            
            <div className="max-h-64 overflow-y-auto p-2">
              {organizations.map(org => (
                <button
                  key={org.id}
                  onClick={() => handleSwitch(org.id)}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-accent-primary/10 transition-all duration-200 text-left group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-primary/20 to-accent-secondary/20 flex items-center justify-center group-hover:shadow-glow transition-all duration-200">
                      <BuildingOfficeIcon className="w-5 h-5 text-accent-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-text-primary truncate">{org.name}</p>
                      <p className="text-xs text-text-muted">{org.memberCount} members</p>
                    </div>
                  </div>
                  
                  {org.id === currentOrgId && (
                    <CheckIcon className="w-5 h-5 text-accent-primary flex-shrink-0" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
