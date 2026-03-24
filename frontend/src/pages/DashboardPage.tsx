import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { SceneGrid } from '../components/dashboard/SceneGrid';
import { UploadDialog } from '../components/dashboard/UploadDialog';
import { FilterBar } from '../components/dashboard/FilterBar';
import { useGetScenesQuery, useUploadVideoMutation, useDeleteSceneMutation } from '../store/api/sceneApi';
import type { SceneStatus } from '../components/common/StatusBadge';
import type { SceneMetadata } from '../types/scene.types';

/**
 * Dashboard page component - main landing page after login
 * Shows hero section, scene grid, upload controls, and filtering options
 * 
 * Features:
 * - Hero section with upload CTA
 * - Scene grid with cards
 * - Upload dialog
 * - Scene navigation
 * 
 * Requirements: 4.1, 4.6, 4.8
 */
export function DashboardPage() {
  const navigate = useNavigate();
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<SceneStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'createdAt' | 'updatedAt' | 'name'>('createdAt');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Fetch scenes
  const { data: scenes = [], isLoading } = useGetScenesQuery();
  const [uploadVideo] = useUploadVideoMutation();
  const [deleteScene] = useDeleteSceneMutation();

  // Filter and sort scenes
  const filteredScenes = useMemo(() => {
    let filtered = [...scenes];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (scene) =>
          scene.name.toLowerCase().includes(query) ||
          scene.sceneId.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((scene) => scene.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'createdAt') {
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      } else if (sortBy === 'updatedAt') {
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      }
      return 0;
    });

    return filtered;
  }, [scenes, searchQuery, statusFilter, sortBy]);

  // Calculate active filter count
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (searchQuery.trim()) count++;
    if (statusFilter !== 'all') count++;
    return count;
  }, [searchQuery, statusFilter]);

  const handleUpload = async (file: File) => {
    try {
      // TODO: Get organizationId from auth state
      const organizationId = 'default-org';
      await uploadVideo({ file, organizationId }).unwrap();
      // Success - the scene list will automatically refresh via RTK Query
    } catch (error) {
      console.error('Upload failed:', error);
      // TODO: Show error toast
    }
  };

  const handleSceneClick = (sceneId: string) => {
    navigate(`/app/viewer/${sceneId}`);
  };

  const handleSceneDelete = async (sceneId: string) => {
    try {
      await deleteScene(sceneId).unwrap();
      // Success - the scene list will automatically refresh via RTK Query
    } catch (error) {
      console.error('Delete failed:', error);
      // TODO: Show error toast
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-secondary-bg to-primary-bg border-b border-border-color mb-8">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-text-primary mb-2">
                Welcome back! 👋
              </h1>
              <p className="text-text-secondary text-lg">
                Manage your 3D scenes and spatial reconstructions
              </p>
            </div>
            <Button
              variant="primary"
              size="lg"
              onClick={() => setUploadDialogOpen(true)}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              }
            >
              New Scene
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="px-8 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-muted text-sm mb-1">Total Scenes</p>
                <p className="text-3xl font-bold text-text-primary">{scenes.length}</p>
              </div>
              <div className="w-12 h-12 bg-accent-coral/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-accent-coral" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-muted text-sm mb-1">Processing</p>
                <p className="text-3xl font-bold text-text-primary">
                  {scenes.filter(s => s.status === 'processing').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-muted text-sm mb-1">Completed</p>
                <p className="text-3xl font-bold text-text-primary">
                  {scenes.filter(s => s.status === 'completed').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scene Grid Section */}
      <div className="px-8 py-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-text-primary">Recent Scenes</h2>
        </div>

        {/* Filter Bar */}
        <FilterBar
          onSearchChange={setSearchQuery}
          onStatusChange={setStatusFilter}
          onSortChange={setSortBy}
          onViewModeChange={setViewMode}
          currentStatus={statusFilter}
          currentSort={sortBy}
          currentViewMode={viewMode}
          activeFilterCount={activeFilterCount}
        />

        <SceneGrid
          scenes={filteredScenes}
          loading={isLoading}
          onSceneClick={handleSceneClick}
          onSceneDelete={handleSceneDelete}
        />
      </div>

      {/* Upload Dialog */}
      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUpload={handleUpload}
      />
    </div>
  );
}
