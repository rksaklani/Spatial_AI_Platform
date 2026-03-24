import React, { useState, useEffect, useCallback } from 'react';
import type { SceneStatus } from '../common/StatusBadge';

export interface FilterBarProps {
  onSearchChange: (query: string) => void;
  onStatusChange: (status: SceneStatus | 'all') => void;
  onSortChange: (sort: 'createdAt' | 'updatedAt' | 'name') => void;
  onViewModeChange: (mode: 'grid' | 'list') => void;
  currentStatus?: SceneStatus | 'all';
  currentSort?: 'createdAt' | 'updatedAt' | 'name';
  currentViewMode?: 'grid' | 'list';
  activeFilterCount?: number;
}

/**
 * FilterBar component - provides search, filtering, sorting, and view mode controls
 * 
 * Features:
 * - Debounced search input (300ms)
 * - Status filter dropdown (all, uploaded, processing, completed, failed)
 * - Sort dropdown (date created, date updated, name)
 * - View mode toggle (grid/list)
 * - Active filter count badge
 * 
 * Requirements: 4.3, 4.4, 26.1, 32.2, 32.3, 32.5
 */
export const FilterBar: React.FC<FilterBarProps> = ({
  onSearchChange,
  onStatusChange,
  onSortChange,
  onViewModeChange,
  currentStatus = 'all',
  currentSort = 'createdAt',
  currentViewMode = 'grid',
  activeFilterCount = 0,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Debounced search with 300ms delay
  useEffect(() => {
    setIsSearching(true);
    const timer = setTimeout(() => {
      onSearchChange(searchQuery);
      setIsSearching(false);
    }, 300);

    return () => {
      clearTimeout(timer);
      setIsSearching(false);
    };
  }, [searchQuery, onSearchChange]);

  const handleSearchInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  }, []);

  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  return (
    <div className="bg-secondary-bg border border-border-color rounded-xl p-4 mb-6">
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Search Input */}
        <div className="flex-1 relative">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              {isSearching ? (
                <svg
                  className="h-5 w-5 text-text-muted animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : (
                <svg
                  className="h-5 w-5 text-text-muted"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              )}
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchInput}
              placeholder="Search scenes by name or description..."
              className="w-full pl-10 pr-10 py-2.5 bg-primary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent transition-all duration-200"
            />
            {searchQuery && (
              <button
                onClick={handleClearSearch}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-text-primary transition-colors"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap gap-3">
          {/* Status Filter */}
          <div className="relative">
            <select
              value={currentStatus}
              onChange={(e) => onStatusChange(e.target.value as SceneStatus | 'all')}
              className="appearance-none pl-4 pr-10 py-2.5 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent transition-all duration-200 cursor-pointer hover:border-accent-primary"
            >
              <option value="all">All Status</option>
              <option value="uploaded">Uploaded</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <svg
                className="h-4 w-4 text-text-muted"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={currentSort}
              onChange={(e) => onSortChange(e.target.value as 'createdAt' | 'updatedAt' | 'name')}
              className="appearance-none pl-4 pr-10 py-2.5 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent transition-all duration-200 cursor-pointer hover:border-accent-primary"
            >
              <option value="createdAt">Date Created</option>
              <option value="updatedAt">Date Updated</option>
              <option value="name">Name</option>
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <svg
                className="h-4 w-4 text-text-muted"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </div>

          {/* View Mode Toggle */}
          <div className="flex bg-primary-bg border border-border-color rounded-lg overflow-hidden">
            <button
              onClick={() => onViewModeChange('grid')}
              className={`px-4 py-2.5 transition-all duration-200 ${
                currentViewMode === 'grid'
                  ? 'bg-accent-primary text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-hover-bg'
              }`}
              title="Grid view"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                />
              </svg>
            </button>
            <button
              onClick={() => onViewModeChange('list')}
              className={`px-4 py-2.5 transition-all duration-200 border-l border-border-color ${
                currentViewMode === 'list'
                  ? 'bg-accent-primary text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-hover-bg'
              }`}
              title="List view"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>

          {/* Active Filter Count Badge */}
          {activeFilterCount > 0 && (
            <div className="flex items-center px-3 py-2 bg-accent-primary/20 border border-accent-primary/30 rounded-lg">
              <span className="text-sm font-medium text-accent-primary">
                {activeFilterCount} {activeFilterCount === 1 ? 'filter' : 'filters'} active
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
