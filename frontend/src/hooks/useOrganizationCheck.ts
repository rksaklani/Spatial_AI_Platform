/**
 * Hook to check if user has an organization and prompt creation if needed
 */

import { useState, useCallback } from 'react';
import { useGetCurrentOrganizationQuery } from '../store/api/organizationApi';

export const useOrganizationCheck = () => {
  const { data: currentOrg, isLoading } = useGetCurrentOrganizationQuery();
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const checkOrganization = useCallback((onSuccess: () => void) => {
    if (!currentOrg && !isLoading) {
      setShowCreateDialog(true);
      return false;
    }
    if (currentOrg) {
      onSuccess();
    }
    return true;
  }, [currentOrg, isLoading]);

  return {
    currentOrg,
    isLoading,
    hasOrganization: !!currentOrg,
    showCreateDialog,
    setShowCreateDialog,
    checkOrganization,
  };
};
