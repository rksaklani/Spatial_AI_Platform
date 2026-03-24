import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetScenesQuery, useDeleteSceneMutation } from '../store/api/sceneApi';
import { Button } from '../components/common/Button';
import { SceneGrid } from '../components/dashboard/SceneGrid';
import { UploadDialog } from '../components/dashboard/UploadDialog';
import { DeleteSceneDialog } from '../components/dashboard/DeleteSceneDialog';
import { FilterBar } from '../components/dashboard/FilterBar';
import type { SceneStatus } from '../components/common/StatusBadge';
import type { SceneMetadata } from '../types/scene.types';

export function ScenesPage() {
  const navigate = useNavigate();
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedScene, setSelectedScene] = useState<SceneMetadata | null>(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<SceneStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'createdAt' | 'updatedAt' | 'name'>('createdAt');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const { data: scenes = [], isLoading } = useGetScenesQuery();
  const [deleteScene] = useDeleteSceneMutation();

  const filteredScenes = useMemo(() => {
    let filtered = [...scenes];

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (scene) =>
          scene.name.toLowerCase().includes(query) ||
          scene.sceneId.toLowerCase().includes(query)
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((scene) => scene.status === statusFilter);
    }

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

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (searchQuery.trim()) count++;
    if (statusFilter !== 'all') count++;
    return count;
  }, [searchQuery, statusFilter]);

  const handleSceneClick = (sceneId: string) => {
    navigate(`/scenes/${sceneId}`);
  };

  const handleSceneDelete = async (sceneId: string) => {
    const scene = scenes.find(s => s.sceneId === sceneId);
    if (scene) {
      setSelectedScene(scene);
      setDeleteDialogOpen(true);
    }
  };

  const handleDeleteConfirm = async (sceneId: string) => {
    try {
      await deleteScene(sceneId).unwrap();
      setDeleteDialogOpen(false);
      setSelectedScene(null);
    } catch (error) {
      console.error('Delete failed:', error);
      throw error;
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-text-primary mb-2">3D Scenes</h1>
          <p className="text-text-secondary">Manage and view all your 3D reconstructions</p>
        </div>
        <Button
          variant="primary"
          size="lg"
          onClick={() => setUploadDialogOpen(true)}
          icon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          }
        >
          Upload Scene
        </Button>
      </div>

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
        onSceneEdit={() => {}}
      />

      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUpload={async () => {}}
        onUploadComplete={() => setUploadDialogOpen(false)}
      />

      <DeleteSceneDialog
        open={deleteDialogOpen}
        scene={selectedScene}
        onClose={() => {
          setDeleteDialogOpen(false);
          setSelectedScene(null);
        }}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
}
