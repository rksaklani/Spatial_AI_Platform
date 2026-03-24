/**
 * OrganizationSwitcher Component
 * 
 * Dropdown for switching between organizations
 * Requirements: 2.1, 2.2, 2.3
 */

import { useState } from 'react';
import { useGetOrganizationsQuery, useSwitchOrganizationMutation } from '../../store/api/organizationApi';
import { useAppSelector } from '../../store/hooks';

export function OrganizationSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const currentOrgId = useAppSelector((state) => state.auth.user?.organizationId);
  
  const { data: organizations, isLoading } = useGetOrganizationsQuery();
  const [switchOrg, { isLoading: isSwitching }] = useSwitchOrganizationMutation();

  const currentOrg = organizations?.find((org) => org.id === currentOrgId);

  const handleSwitch = async (orgId: string) => {
    if (orgId === currentOrgId) {
      setIsOpen(false);
      return;
    }

    try {
      await switchOrg(orgId).unwrap();
      setIsOpen(false);
      // Reload page to refresh all data
      window.location.reload();
    } catch (error) {
      console.error('Failed to switch organization:', error);
    }
  };

  if (isLoading || !organizations || organizations.length <= 1) {
    return null;
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-base transition-colors"
        aria-label="Switch organization"
      >
        <svg className="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span className="text-sm font-medium text-text-primary">
          {currentOrg?.name || 'Select Organization'}
        </span>
        <svg className={`w-4 h-4 text-text-secondary transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 left-0 w-64 bg-surface-elevated border border-border-subtle rounded-lg shadow-lg z-20 overflow-hidden">
            <div className="py-1">
              {organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => handleSwitch(org.id)}
                  disabled={isSwitching}
                  className={`w-full px-4 py-2 text-left text-sm hover:bg-surface-base transition-colors ${
                    org.id === currentOrgId ? 'bg-accent-primary/10 text-accent-primary' : 'text-text-primary'
                  } ${isSwitching ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <span>{org.name}</span>
                    {org.id === currentOrgId && (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
