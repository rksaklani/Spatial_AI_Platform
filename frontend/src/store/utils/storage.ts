/**
 * Safe storage wrapper for redux-persist
 * 
 * Provides fallback when localStorage is not available
 * (e.g., SSR, private browsing, or disabled storage)
 */

interface Storage {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

// In-memory fallback storage
class MemoryStorage implements Storage {
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
function createSafeStorage(): Storage {
  if (isLocalStorageAvailable()) {
    // Use localStorage if available
    return {
      async getItem(key: string): Promise<string | null> {
        try {
          return localStorage.getItem(key);
        } catch (e) {
          console.warn('localStorage.getItem failed:', e);
          return null;
        }
      },
      async setItem(key: string, value: string): Promise<void> {
        try {
          localStorage.setItem(key, value);
        } catch (e) {
          console.warn('localStorage.setItem failed:', e);
        }
      },
      async removeItem(key: string): Promise<void> {
        try {
          localStorage.removeItem(key);
        } catch (e) {
          console.warn('localStorage.removeItem failed:', e);
        }
      },
    };
  } else {
    // Fallback to memory storage
    console.warn('localStorage not available, using memory storage');
    return new MemoryStorage();
  }
}

export const storage = createSafeStorage();
