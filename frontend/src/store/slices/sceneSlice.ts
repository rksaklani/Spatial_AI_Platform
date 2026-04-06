/**
 * Scene slice for managing 3D scene state
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { SceneMetadata, SceneTile } from '../../types/scene.types';

export type SceneStatus =
  | 'uploaded'
  | 'uploading'
  | 'processing'
  | 'extracting_frames'
  | 'estimating_poses'
  | 'generating_depth'
  | 'reconstructing'
  | 'tiling'
  | 'ready'
  | 'completed'
  | 'failed';

export interface SceneFilters {
  status?: SceneStatus[];
  dateRange?: { start: string; end: string };
  searchQuery?: string;
}

interface SceneState {
  currentScene: SceneMetadata | null;
  scenes: SceneMetadata[];
  tiles: SceneTile[];
  loadedTiles: Set<string>;
  loading: boolean;
  error: string | null;
  cameraPosition: [number, number, number];
  cameraDirection: [number, number, number];
  selectedObjects: string[];
  // New state for filtering and UI
  filters: SceneFilters;
  sortBy: 'createdAt' | 'updatedAt' | 'name';
  sortOrder: 'asc' | 'desc';
  selectedScenes: string[];
  viewMode: 'grid' | 'list';
}

const initialState: SceneState = {
  currentScene: null,
  scenes: [],
  tiles: [],
  loadedTiles: new Set(),
  loading: false,
  error: null,
  cameraPosition: [0, 0, 5],
  cameraDirection: [0, 0, -1],
  selectedObjects: [],
  // New initial state
  filters: {},
  sortBy: 'createdAt',
  sortOrder: 'desc',
  selectedScenes: [],
  viewMode: 'grid',
};

const sceneSlice = createSlice({
  name: 'scene',
  initialState,
  reducers: {
    setCurrentScene: (state, action: PayloadAction<SceneMetadata>) => {
      state.currentScene = action.payload;
      state.error = null;
    },
    setScenes: (state, action: PayloadAction<SceneMetadata[]>) => {
      state.scenes = action.payload;
    },
    addScene: (state, action: PayloadAction<SceneMetadata>) => {
      state.scenes.push(action.payload);
    },
    updateScene: (state, action: PayloadAction<SceneMetadata>) => {
      const index = state.scenes.findIndex((s) => s.sceneId === action.payload.sceneId);
      if (index !== -1) {
        state.scenes[index] = action.payload;
      }
      if (state.currentScene?.sceneId === action.payload.sceneId) {
        state.currentScene = action.payload;
      }
    },
    setTiles: (state, action: PayloadAction<SceneTile[]>) => {
      state.tiles = action.payload;
    },
    addLoadedTile: (state, action: PayloadAction<string>) => {
      state.loadedTiles.add(action.payload);
    },
    clearLoadedTiles: (state) => {
      state.loadedTiles.clear();
    },
    setCameraPosition: (state, action: PayloadAction<[number, number, number]>) => {
      state.cameraPosition = action.payload;
    },
    setCameraDirection: (state, action: PayloadAction<[number, number, number]>) => {
      state.cameraDirection = action.payload;
    },
    setSelectedObjects: (state, action: PayloadAction<string[]>) => {
      state.selectedObjects = action.payload;
    },
    toggleObjectSelection: (state, action: PayloadAction<string>) => {
      const index = state.selectedObjects.indexOf(action.payload);
      if (index !== -1) {
        state.selectedObjects.splice(index, 1);
      } else {
        state.selectedObjects.push(action.payload);
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    // New actions for filtering and UI
    setFilters: (state, action: PayloadAction<SceneFilters>) => {
      state.filters = action.payload;
    },
    updateFilters: (state, action: PayloadAction<Partial<SceneFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setSortBy: (state, action: PayloadAction<'createdAt' | 'updatedAt' | 'name'>) => {
      state.sortBy = action.payload;
    },
    setSortOrder: (state, action: PayloadAction<'asc' | 'desc'>) => {
      state.sortOrder = action.payload;
    },
    toggleSortOrder: (state) => {
      state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
    },
    setSelectedScenes: (state, action: PayloadAction<string[]>) => {
      state.selectedScenes = action.payload;
    },
    toggleSceneSelection: (state, action: PayloadAction<string>) => {
      const index = state.selectedScenes.indexOf(action.payload);
      if (index !== -1) {
        state.selectedScenes.splice(index, 1);
      } else {
        state.selectedScenes.push(action.payload);
      }
    },
    selectAllScenes: (state) => {
      state.selectedScenes = state.scenes.map((scene) => scene.sceneId);
    },
    clearSceneSelection: (state) => {
      state.selectedScenes = [];
    },
    setViewMode: (state, action: PayloadAction<'grid' | 'list'>) => {
      state.viewMode = action.payload;
    },
    toggleViewMode: (state) => {
      state.viewMode = state.viewMode === 'grid' ? 'list' : 'grid';
    },
  },
});

export const {
  setCurrentScene,
  setScenes,
  addScene,
  updateScene,
  setTiles,
  addLoadedTile,
  clearLoadedTiles,
  setCameraPosition,
  setCameraDirection,
  setSelectedObjects,
  toggleObjectSelection,
  setLoading,
  setError,
  clearError,
  // New exports
  setFilters,
  updateFilters,
  clearFilters,
  setSortBy,
  setSortOrder,
  toggleSortOrder,
  setSelectedScenes,
  toggleSceneSelection,
  selectAllScenes,
  clearSceneSelection,
  setViewMode,
  toggleViewMode,
} = sceneSlice.actions;

export default sceneSlice.reducer;
