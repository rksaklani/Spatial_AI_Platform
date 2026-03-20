/**
 * Scene slice for managing 3D scene state
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { SceneMetadata, SceneTile } from '../../types/scene.types';

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
} = sceneSlice.actions;

export default sceneSlice.reducer;
