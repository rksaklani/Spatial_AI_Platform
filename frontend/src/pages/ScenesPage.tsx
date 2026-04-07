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
  const { checkOrganization, showCreateDialog, setShowCreateDialog, currentOrg, isLoading: orgLoading } = useOrganizationCheck();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedScene, setSelectedScene] = useState<SceneMetadata | null>(null);
  const [processingSceneId, setProcessingSceneId] = useState<string | null>(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<SceneStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'createdAt' | 'updatedAt' | 'name'>('createdAt');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const { data: scenes = [], isLoading, refetch } = useGetScenesQuery();
  const [deleteScene] = useDeleteSceneMutation();

  // Find scenes that are currently processing
  const processingScenes = useMemo(() => {
    const processingStatuses = [
      'uploaded',
      'processing', 
      'extracting_frames', 
      'estimating_poses', 
      'generating_depth', 
      'reconstructing', 
      'tiling'
    ];
    return scenes.filter(scene => 
      processingStatuses.includes(scene.status)
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

  // Separate scenes by type
  const videoScenes = useMemo(() => {
    return filteredScenes.filter(scene => scene.sourceType === 'video');
  }, [filteredScenes]);

  const modelScenes = useMemo(() => {
    return filteredScenes.filter(scene => scene.sourceType === 'import');
  }, [filteredScenes]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (searchQuery.trim()) count++;
    if (statusFilter !== 'all') count++;
    return count;
  }, [searchQuery, statusFilter]);

  const handleSceneClick = (sceneId: string) => {
    const scene = scenes.find(s => s.sceneId === sceneId);
    
    // Only navigate to viewer if scene is ready or completed
    if (scene && (scene.status === 'ready' || scene.status === 'completed')) {
      navigate(`/scenes/${sceneId}`);
    } else {
      // Scene is still processing or failed - show a message
      console.log('Scene not ready for viewing:', scene?.status);
      // Optionally show a toast notification
    }
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
    // Don't set processingSceneId for imports - they don't have a processing pipeline
    // Just refetch to show the new scene in the list
    refetch();
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
            onClick={() => {
              if (currentOrg || !orgLoading) {
                setImportDialogOpen(true);
              } else {
                checkOrganization(() => setImportDialogOpen(true));
              }
            }}
            icon={<CubeIcon className="h-5 w-5" />}
          >
            Import 3D File
          </Button>
          <Button
            variant="primary"
            size="lg"
            onClick={() => {
              if (currentOrg || !orgLoading) {
                setUploadDialogOpen(true);
              } else {
                checkOrganization(() => setUploadDialogOpen(true));
              }
            }}
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

      {/* Video Scenes Section */}
      {videoScenes.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <svg className="h-6 w-6 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <h2 className="text-xl font-semibold text-text-primary">Video Reconstructions</h2>
            <span className="text-sm text-text-muted">({videoScenes.length})</span>
          </div>
          <SceneGrid
            scenes={videoScenes}
            loading={isLoading}
            onSceneClick={handleSceneClick}
            onSceneDelete={handleSceneDelete}
            onSceneEdit={() => {}}
            onSceneShare={handleSceneShare}
          />
        </div>
      )}

      {/* Model Scenes Section */}
      {modelScenes.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <svg className="h-6 w-6 text-accent-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <h2 className="text-xl font-semibold text-text-primary">Imported 3D Models</h2>
            <span className="text-sm text-text-muted">({modelScenes.length})</span>
          </div>
          <SceneGrid
            scenes={modelScenes}
            loading={isLoading}
            onSceneClick={handleSceneClick}
            onSceneDelete={handleSceneDelete}
            onSceneEdit={() => {}}
            onSceneShare={handleSceneShare}
          />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && videoScenes.length === 0 && modelScenes.length === 0 && (
        <div className="text-center py-12">
          <svg className="h-16 w-16 text-text-muted mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p className="text-lg text-text-secondary mb-2">No scenes yet</p>
          <p className="text-sm text-text-muted">Upload a video or import a 3D model to get started</p>
        </div>
      )}

      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUpload={async () => {}}
        onUploadComplete={handleUploadComplete}
        onRefresh={refetch}
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
