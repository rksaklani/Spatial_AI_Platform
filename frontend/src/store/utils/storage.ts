/**
 * Safe storage wrapper for redux-persist
 * 
 * Provides fallback when localStorage is not available
 * (e.g., SSR, private browsing, or disabled storage)
 * 
 * IMPORTANT: Redux-persist v6+ requires storage methods to return Promises.
 * We wrap synchronous localStorage operations in Promise.resolve() to ensure
 * immediate resolution while maintaining the async interface redux-persist expects.
 */

// Redux-persist compatible storage interface
// All methods MUST return promises for redux-persist v6+
interface StorageEngine {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

// In-memory fallback storage
class MemoryStorage implements StorageEngine {
  private storage: Map<string, string> = new Map();

  async getItem(key: string): Promise<string | null> {
    return this.storage.get(key) || null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.storage.set(key, value);
  }

  async removeItem(key: string): Promise<void> {
    this.storage.delete(key);
  }
}

// Synchronous localStorage wrapper that returns promises
// This ensures immediate writes while satisfying redux-persist's async interface
class LocalStorageWrapper implements StorageEngine {
  getItem(key: string): Promise<string | null> {
    try {
      const value = localStorage.getItem(key);
      return Promise.resolve(value);
    } catch (e) {
      console.warn('localStorage.getItem failed:', e);
      return Promise.resolve(null);
    }
  }

  setItem(key: string, value: string): Promise<void> {
    try {
      localStorage.setItem(key, value);
      return Promise.resolve();
    } catch (e) {
      console.warn('localStorage.setItem failed:', e);
      return Promise.resolve();
    }
  }

  removeItem(key: string): Promise<void> {
    try {
      localStorage.removeItem(key);
      return Promise.resolve();
    } catch (e) {
      console.warn('localStorage.removeItem failed:', e);
      return Promise.resolve();
    }
  }
}

// Check if localStorage is available
function isLocalStorageAvailable(): boolean {
  try {
    const testKey = '__redux_persist_test__';
    localStorage.setItem(testKey, 'test');
    localStorage.removeItem(testKey);
    return true;
  } catch (e) {
    return false;
  }
}

// Create safe storage
function createSafeStorage(): StorageEngine {
  if (isLocalStorageAvailable()) {
    return new LocalStorageWrapper();
  } else {
    console.warn('localStorage not available, using memory storage');
    return new MemoryStorage();
  }
}

export const storage = createSafeStorage();
