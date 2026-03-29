/**
 * Utilities for managing persisted state
 */

import { persistor } from '../index';

/**
 * Clear all persisted state
 */
export const clearPersistedState = async (): Promise<void> => {
  await persistor.purge();
  localStorage.clear();
};

/**
 * Clear specific persisted state by key
 */
export const clearPersistedStateByKey = (key: string): void => {
  localStorage.removeItem(`persist:${key}`);
};

/**
 * Get persisted state size in bytes
 */
export const getPersistedStateSize = (): number => {
  let total = 0;
  for (const key in localStorage) {
    if (localStorage.hasOwnProperty(key)) {
      total += localStorage[key].length + key.length;
    }
  }
  return total;
};

/**
 * Check if state is persisted
 */
export const isStatePersisted = (key: string): boolean => {
  return localStorage.getItem(`persist:${key}`) !== null;
};

/**
 * Pause persistence
 */
export const pausePersistence = (): void => {
  persistor.pause();
};

/**
 * Resume persistence
 */
export const resumePersistence = (): void => {
  persistor.persist();
};

/**
 * Flush pending persistence operations
 */
export const flushPersistence = async (): Promise<void> => {
  await persistor.flush();
};
