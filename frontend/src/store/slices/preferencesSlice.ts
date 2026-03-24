/**
 * User Preferences Redux Slice
 * Requirements: 29.4, 31.6
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

interface ViewerSettings {
  defaultRenderingMode: 'client' | 'server';
  showFps: boolean;
  showCoordinates: boolean;
  autoRotate: boolean;
  quality: 'low' | 'medium' | 'high';
}

interface NotificationSettings {
  processingComplete: boolean;
  mentions: boolean;
  collaborationUpdates: boolean;
  email: boolean;
}

interface PreferencesState {
  theme: 'light' | 'dark';
  language: string;
  viewerSettings: ViewerSettings;
  notificationSettings: NotificationSettings;
}

const initialState: PreferencesState = {
  theme: 'dark',
  language: 'en',
  viewerSettings: {
    defaultRenderingMode: 'client',
    showFps: true,
    showCoordinates: false,
    autoRotate: false,
    quality: 'high',
  },
  notificationSettings: {
    processingComplete: true,
    mentions: true,
    collaborationUpdates: true,
    email: true,
  },
};

const preferencesSlice = createSlice({
  name: 'preferences',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload;
    },
    updateViewerSettings: (state, action: PayloadAction<Partial<ViewerSettings>>) => {
      state.viewerSettings = { ...state.viewerSettings, ...action.payload };
    },
    updateNotificationSettings: (state, action: PayloadAction<Partial<NotificationSettings>>) => {
      state.notificationSettings = { ...state.notificationSettings, ...action.payload };
    },
    resetPreferences: () => initialState,
  },
});

export const {
  setTheme,
  setLanguage,
  updateViewerSettings,
  updateNotificationSettings,
  resetPreferences,
} = preferencesSlice.actions;

export default preferencesSlice.reducer;
