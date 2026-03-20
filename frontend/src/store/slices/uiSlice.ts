/**
 * UI slice for managing application UI state
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

interface UIState {
  sidebarOpen: boolean;
  annotationMode: boolean;
  measurementMode: boolean;
  notifications: Notification[];
  loading: {
    global: boolean;
    upload: boolean;
    processing: boolean;
  };
  modal: {
    open: boolean;
    type: string | null;
    data: any;
  };
}

const initialState: UIState = {
  sidebarOpen: true,
  annotationMode: false,
  measurementMode: false,
  notifications: [],
  loading: {
    global: false,
    upload: false,
    processing: false,
  },
  modal: {
    open: false,
    type: null,
    data: null,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    setAnnotationMode: (state, action: PayloadAction<boolean>) => {
      state.annotationMode = action.payload;
      if (action.payload) {
        state.measurementMode = false;
      }
    },
    setMeasurementMode: (state, action: PayloadAction<boolean>) => {
      state.measurementMode = action.payload;
      if (action.payload) {
        state.annotationMode = false;
      }
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
      };
      state.notifications.push(notification);
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter((n) => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.global = action.payload;
    },
    setUploadLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.upload = action.payload;
    },
    setProcessingLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.processing = action.payload;
    },
    openModal: (state, action: PayloadAction<{ type: string; data?: any }>) => {
      state.modal.open = true;
      state.modal.type = action.payload.type;
      state.modal.data = action.payload.data || null;
    },
    closeModal: (state) => {
      state.modal.open = false;
      state.modal.type = null;
      state.modal.data = null;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setAnnotationMode,
  setMeasurementMode,
  addNotification,
  removeNotification,
  clearNotifications,
  setGlobalLoading,
  setUploadLoading,
  setProcessingLoading,
  openModal,
  closeModal,
} = uiSlice.actions;

export default uiSlice.reducer;
