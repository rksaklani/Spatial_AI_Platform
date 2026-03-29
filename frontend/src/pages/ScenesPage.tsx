import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetScenesQuery, useDeleteSceneMutation } from '../store/api/sceneApi';
import { Button } from '../components/common/Button';
import { SceneGrid } from '../components/dashboard/SceneGrid';
import { UploadDialog } from '../components/dashboard/UploadDialog';
import { ImportDialog } from '../components/dashboard/ImportDialog';
import { ProcessingProgress } from '../components/dashboard/ProcessingProgress';
import { ShareDialog } from '../components/sharing/ShareDialog';
import { DeleteSceneDialog } from '../components/dashboard/DeleteSceneDialog';
import { FilterBar } from '../components/dashboard/FilterBar';
import { CreateOrganizationDialog } from '../components/onboarding/CreateOrganizationDialog';
import { useOrganizationCheck } from '../hooks/useOrganizationCheck';
import { ArrowUpTrayIcon, CubeIcon } from '@heroicons/react/24/outline';
import type { SceneStatus } from '../components/common/StatusBadge';
import type { SceneMetadata } from '../types/scene.types';

export function ScenesPage() {
  const navigate = useNavigate();
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  
  // Organization check
  const { checkOrganization, showCreateDialog, setShowCreateDialog } = useOrganizationCheck();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedScene, setSelectedScene] = useState<SceneMetadata | null>(null);
  const [processingSceneId, setProcessingSceneId] = useState<string | null>(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<SceneStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'createdAt' | 'updatedAt' | 'name'>('createdAt');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const { data: scenes = [], isLoading } = useGetScenesQuery();
  const [deleteScene] = useDeleteSceneMutation();

  // Find scenes that are currently processing
  const processingScenes = useMemo(() => {
    return scenes.filter(scene => 
      scene.status === 'processing'
    );
  }, [scenes]);

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

  const handleSceneShare = (sceneId: string) => {
    const scene = scenes.find(s => s.sceneId === sceneId);
    if (scene) {
      setSelectedScene(scene);
      setShareDialogOpen(true);
    }
  };

  const handleUploadComplete = (sceneId: string) => {
    setUploadDialogOpen(false);
    setProcessingSceneId(sceneId);
  };

  const handleImportComplete = (sceneId: string) => {
    setImportDialogOpen(false);
    setProcessingSceneId(sceneId);
  };

  const handleProcessingComplete = () => {
    setProcessingSceneId(null);
    // Refetch scenes to get updated status
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
        <div className="flex gap-3">
          <Button
            variant="secondary"
            size="lg"
            onClick={() => checkOrganization(() => setImportDialogOpen(true))}
            icon={<CubeIcon className="h-5 w-5" />}
          >
            Import 3D File
          </Button>
          <Button
            variant="primary"
            size="lg"
            onClick={() => checkOrganization(() => setUploadDialogOpen(true))}
            icon={<ArrowUpTrayIcon className="h-5 w-5" />}
          >
            Upload Video
          </Button>
        </div>
      </div>

      {/* Processing Progress Section */}
      {(processingSceneId || processingScenes.length > 0) && (
        <div className="mb-6 space-y-4">
          {processingSceneId && (
            <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Processing Scene</h3>
              <ProcessingProgress
                sceneId={processingSceneId}
                onComplete={handleProcessingComplete}
                onError={(error) => {
                  console.error('Processing error:', error);
                  setProcessingSceneId(null);
                }}
              />
            </div>
          )}
          {processingScenes.map(scene => (
            <div key={scene.sceneId} className="bg-secondary-bg border border-border-color rounded-xl p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">{scene.name}</h3>
              <ProcessingProgress
                sceneId={scene.sceneId}
                onComplete={() => {}}
                onError={(error) => console.error('Processing error:', error)}
              />
            </div>
          ))}
        </div>
      )}

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
        onSceneShare={handleSceneShare}
      />

      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUpload={async () => {}}
        onUploadComplete={handleUploadComplete}
      />

      <ImportDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onImportComplete={handleImportComplete}
      />

      {selectedScene && (
        <ShareDialog
          open={shareDialogOpen}
          sceneId={selectedScene.sceneId}
          sceneName={selectedScene.name}
          onClose={() => {
            setShareDialogOpen(false);
            setSelectedScene(null);
          }}
        />
      )}

      <DeleteSceneDialog
        open={deleteDialogOpen}
        scene={selectedScene}
        onClose={() => {
          setDeleteDialogOpen(false);
          setSelectedScene(null);
        }}
        onConfirm={handleDeleteConfirm}
      />

      <CreateOrganizationDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onSuccess={() => window.location.reload()}
      />
    </div>
  );
}
