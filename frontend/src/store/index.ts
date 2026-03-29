/**
 * Redux store configuration with RTK Query and persistence
 */

import { configureStore, combineReducers } from '@reduxjs/toolkit';
import {
  persistStore,
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';
import { storage } from './utils/storage';
import { baseApi } from './api/baseApi';
import authReducer from './slices/authSlice';
import sceneReducer from './slices/sceneSlice';
import uiReducer from './slices/uiSlice';
import notificationReducer from './slices/notificationSlice';
import preferencesReducer from './slices/preferencesSlice';
import { apiMiddleware } from './middleware/apiMiddleware';

// Persist configuration
const persistConfig = {
  key: 'root',
  version: 1,
  storage,
  whitelist: ['auth', 'preferences', 'notifications'], // Persist auth, preferences, and notifications
  blacklist: [baseApi.reducerPath], // Don't persist API cache
};

// Combine reducers
const rootReducer = combineReducers({
  [baseApi.reducerPath]: baseApi.reducer,
  auth: authReducer,
  scene: sceneReducer,
  ui: uiReducer,
  notifications: notificationReducer,
  preferences: preferencesReducer,
});

// Create persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore redux-persist actions
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        // Ignore these field paths in all actions (including File objects in uploads)
        ignoredActionPaths: [
          'payload.timestamp',
          'meta.baseQueryMeta',
          'meta.arg.originalArgs.file', // Ignore File objects in upload mutations
          'payload.file', // Ignore File objects in payloads
        ],
        // Ignore these paths in the state
        ignoredPaths: ['scene.currentScene.metadata', 'scene.loadedTiles'],
      },
    })
      .concat(baseApi.middleware)
      .concat(apiMiddleware),
});

// Create persistor
export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
