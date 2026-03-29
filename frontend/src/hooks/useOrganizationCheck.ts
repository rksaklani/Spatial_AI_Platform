/**
 * Hook to check if user has an organization and prompt creation if needed
 */

import { useState, useCallback } from 'react';
import { useGetCurrentOrganizationQuery } from '../store/api/organizationApi';

export const useOrganizationCheck = () => {
  const { data: currentOrg, isLoading } = useGetCurrentOrganizationQuery();
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const checkOrganization = useCallback((onSuccess: () => void) => {
    if (!currentOrg) {
      setShowCreateDialog(true);
      return false;
    }
    onSuccess();
    return true;
  }, [currentOrg]);

  return {
    currentOrg,
    isLoading,
    hasOrganization: !!currentOrg,
    showCreateDialog,
    setShowCreateDialog,
    checkOrganization,
  };
};
