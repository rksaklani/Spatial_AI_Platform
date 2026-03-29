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
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary-bg border border-border-color hover:border-accent-primary transition-colors"
        disabled={isLoading}
      >
        <BuildingOfficeIcon className="w-5 h-5 text-text-secondary" />
        <span className="text-sm font-medium text-text-primary">
          {currentOrg?.name || 'Select Organization'}
        </span>
        <ChevronDownIcon
          className={`w-4 h-4 text-text-secondary transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-64 bg-secondary-bg border border-border-color rounded-lg shadow-xl z-50 overflow-hidden">
          <div className="p-2 border-b border-border-color">
            <p className="text-xs text-text-muted px-2 py-1">Switch Organization</p>
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {organizations.map(org => (
              <button
                key={org.id}
                onClick={() => handleSwitch(org.id)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-primary-bg transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-accent-primary/20 flex items-center justify-center">
                    <BuildingOfficeIcon className="w-5 h-5 text-accent-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">{org.name}</p>
                    <p className="text-xs text-text-muted">{org.memberCount} members</p>
                  </div>
                </div>
                
                {org.id === currentOrgId && (
                  <CheckIcon className="w-5 h-5 text-accent-primary" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
