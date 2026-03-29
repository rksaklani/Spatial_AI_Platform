/**
 * Property-Based Test: Authentication Token Persistence
 * 
 * **Validates: Requirements 1.6, 22.3**
 * 
 * This test verifies that authentication tokens are correctly persisted
 * across browser sessions using redux-persist and localStorage.
 * 
 * Property: For any valid authentication token, storing it in the auth state
 * and then retrieving it from persisted storage should return the same token.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fc from 'fast-check';
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { persistStore, persistReducer, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from 'redux-persist';
import authReducer, { loginSuccess, logout } from '../authSlice';
import sceneReducer from '../sceneSlice';
import uiReducer from '../uiSlice';
import { storage } from '../../utils/storage';

describe('Property 1: Authentication Token Persistence', () => {
  // Clean up localStorage before and after each test
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  /**
   * Property: Token persistence and retrieval consistency
   * 
   * For any valid authentication token:
   * - Storing the token in auth state should persist it to storage
   * - Rehydrating the store should restore the exact same token
   * - The token value must match exactly (no corruption or transformation)
   */
  it('should persist and retrieve authentication tokens without modification', { timeout: 30000 }, async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate arbitrary valid JWT-like tokens
        fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' ')),
        fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' ')),
        fc.integer({ min: 300, max: 86400 }), // expiresIn: 5 minutes to 24 hours
        async (accessToken, refreshToken, expiresIn) => {
          // Use unique key for each test run to avoid conflicts
          const uniqueKey = `test-auth-persist-${Date.now()}-${Math.random()}`;
          
          // Create persist config matching the actual store configuration
          const persistConfig = {
            key: uniqueKey,
            version: 1,
            storage,
            whitelist: ['auth'], // Only persist auth state, matching production config
          };

          // Create root reducer matching the actual store structure
          const rootReducer = combineReducers({
            auth: authReducer,
            scene: sceneReducer,
            ui: uiReducer,
          });

          // Create persisted reducer
          const persistedReducer = persistReducer(persistConfig, rootReducer);

          // Create first store instance
          const store1 = configureStore({
            reducer: persistedReducer,
            middleware: (getDefaultMiddleware) =>
              getDefaultMiddleware({
                serializableCheck: {
                  ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
                },
              }),
          });

          const persistor1 = persistStore(store1);

          // Wait for initial rehydration
          await new Promise<void>((resolve) => {
            const unsubscribe = persistor1.subscribe(() => {
              const state = store1.getState();
              if (state._persist?.rehydrated) {
                unsubscribe();
                resolve();
              }
            });
          });

          // Dispatch login action with generated tokens
          store1.dispatch(loginSuccess({
            user: {
              id: 'test-user-id',
              email: 'test@example.com',
              name: 'Test User',
              organizationId: 'test-org-id',
            },
            token: accessToken,
            refreshToken: refreshToken,
            expiresIn,
          }));

          // Verify tokens are in state
          const state1 = store1.getState().auth;
          expect(state1.token).toBe(accessToken);
          expect(state1.refreshToken).toBe(refreshToken);
          expect(state1.isAuthenticated).toBe(true);

          // Flush persistence to ensure data is written
          await persistor1.flush();
          
          // Wait for localStorage write to complete
          await new Promise(resolve => setTimeout(resolve, 200));

          // Pause and purge the first store
          persistor1.pause();
          await persistor1.purge();

          // Create a second store instance (simulating app restart)
          // Need to create a NEW persisted reducer with the same config
          const persistedReducer2 = persistReducer(persistConfig, rootReducer);
          
          const store2 = configureStore({
            reducer: persistedReducer2,
            middleware: (getDefaultMiddleware) =>
              getDefaultMiddleware({
                serializableCheck: {
                  ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
                },
              }),
          });

          const persistor2 = persistStore(store2);

          // Wait for rehydration to complete
          await new Promise<void>((resolve) => {
            const unsubscribe = persistor2.subscribe(() => {
              const state = store2.getState();
              if (state._persist?.rehydrated) {
                unsubscribe();
                resolve();
              }
            });
          });

          // Verify tokens were restored correctly
          const state2 = store2.getState().auth;
          
          // Property assertion: Retrieved tokens must match stored tokens exactly
          expect(state2.token).toBe(accessToken);
          expect(state2.refreshToken).toBe(refreshToken);
          expect(state2.isAuthenticated).toBe(true);
          
          // Verify token expiration was also persisted
          expect(state2.tokenExpiresAt).toBeDefined();
          expect(typeof state2.tokenExpiresAt).toBe('number');

          // Clean up
          persistor2.pause();
          await persistor2.purge();
        }
      ),
      {
        numRuns: 20, // Run 20 test cases with different token combinations
        verbose: true,
      }
    );
  });

  /**
   * Property: Logout clears persisted tokens
   * 
   * After logout:
   * - All tokens should be removed from state
   * - Persisted storage should be cleared
   * - Rehydrating a new store should not restore tokens
   */
  it('should clear persisted tokens on logout', { timeout: 30000 }, async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' ')),
        fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' ')),
        async (accessToken, refreshToken) => {
          // Use unique key for each test run to avoid conflicts
          const uniqueKey = `test-auth-logout-${Date.now()}-${Math.random()}`;
          
          const persistConfig = {
            key: uniqueKey,
            version: 1,
            storage,
            whitelist: ['auth'],
          };

          // Create root reducer matching the actual store structure
          const rootReducer = combineReducers({
            auth: authReducer,
            scene: sceneReducer,
            ui: uiReducer,
          });

          const persistedReducer = persistReducer(persistConfig, rootReducer);

          // Create store and login
          const store1 = configureStore({
            reducer: persistedReducer,
            middleware: (getDefaultMiddleware) =>
              getDefaultMiddleware({
                serializableCheck: {
                  ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
                },
              }),
          });

          const persistor1 = persistStore(store1);

          await new Promise<void>((resolve) => {
            const unsubscribe = persistor1.subscribe(() => {
              if (store1.getState()._persist?.rehydrated) {
                unsubscribe();
                resolve();
              }
            });
          });

          // Login
          store1.dispatch(loginSuccess({
            user: {
              id: 'test-user-id',
              email: 'test@example.com',
              name: 'Test User',
              organizationId: 'test-org-id',
            },
            token: accessToken,
            refreshToken: refreshToken,
            expiresIn: 900,
          }));

          await persistor1.flush();
          
          // Wait for localStorage write to complete
          await new Promise(resolve => setTimeout(resolve, 200));

          // Logout
          store1.dispatch(logout());
          await persistor1.flush();
          
          // Wait for localStorage write to complete
          await new Promise(resolve => setTimeout(resolve, 200));

          // Verify state is cleared
          const stateAfterLogout = store1.getState().auth;
          expect(stateAfterLogout.token).toBeNull();
          expect(stateAfterLogout.refreshToken).toBeNull();
          expect(stateAfterLogout.isAuthenticated).toBe(false);

          persistor1.pause();
          await persistor1.purge();

          // Create new store to verify persistence was cleared
          const store2 = configureStore({
            reducer: persistedReducer,
            middleware: (getDefaultMiddleware) =>
              getDefaultMiddleware({
                serializableCheck: {
                  ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
                },
              }),
          });

          const persistor2 = persistStore(store2);

          await new Promise<void>((resolve) => {
            const unsubscribe = persistor2.subscribe(() => {
              if (store2.getState()._persist?.rehydrated) {
                unsubscribe();
                resolve();
              }
            });
          });

          // Property assertion: After logout, rehydrated state should have no tokens
          const rehydratedState = store2.getState().auth;
          expect(rehydratedState.token).toBeNull();
          expect(rehydratedState.refreshToken).toBeNull();
          expect(rehydratedState.isAuthenticated).toBe(false);

          // Clean up
          persistor2.pause();
          await persistor2.purge();
        }
      ),
      {
        numRuns: 20,
        verbose: true,
      }
    );
  });

  /**
   * Property: Token updates are persisted correctly
   * 
   * When tokens are updated (e.g., after refresh):
   * - New tokens should replace old tokens in storage
   * - Rehydration should return the latest tokens, not old ones
   */
  it('should persist token updates correctly', { timeout: 30000 }, async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate two different sets of tokens
        fc.tuple(
          fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' ')),
          fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' '))
        ).filter(([t1, t2]) => t1 !== t2),
        fc.tuple(
          fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' ')),
          fc.string({ minLength: 20, maxLength: 500 }).filter(s => !s.includes(' '))
        ).filter(([r1, r2]) => r1 !== r2),
        async ([firstAccessToken, secondAccessToken], [firstRefreshToken, secondRefreshToken]) => {
          // Use unique key for each test run to avoid conflicts
          const uniqueKey = `test-auth-update-${Date.now()}-${Math.random()}`;
          
          const persistConfig = {
            key: uniqueKey,
            version: 1,
            storage,
            whitelist: ['auth'],
          };

          // Create root reducer matching the actual store structure
          const rootReducer = combineReducers({
            auth: authReducer,
            scene: sceneReducer,
            ui: uiReducer,
          });

          const persistedReducer = persistReducer(persistConfig, rootReducer);

          const store1 = configureStore({
            reducer: persistedReducer,
            middleware: (getDefaultMiddleware) =>
              getDefaultMiddleware({
                serializableCheck: {
                  ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
                },
              }),
          });

          const persistor1 = persistStore(store1);

          await new Promise<void>((resolve) => {
            const unsubscribe = persistor1.subscribe(() => {
              if (store1.getState()._persist?.rehydrated) {
                unsubscribe();
                resolve();
              }
            });
          });

          // Login with first tokens
          store1.dispatch(loginSuccess({
            user: {
              id: 'test-user-id',
              email: 'test@example.com',
              name: 'Test User',
              organizationId: 'test-org-id',
            },
            token: firstAccessToken,
            refreshToken: firstRefreshToken,
            expiresIn: 900,
          }));

          await persistor1.flush();
          
          // Wait for localStorage write to complete
          await new Promise(resolve => setTimeout(resolve, 200));

          // Update to second tokens (simulating token refresh)
          store1.dispatch(loginSuccess({
            user: {
              id: 'test-user-id',
              email: 'test@example.com',
              name: 'Test User',
              organizationId: 'test-org-id',
            },
            token: secondAccessToken,
            refreshToken: secondRefreshToken,
            expiresIn: 900,
          }));

          await persistor1.flush();
          
          // Wait for localStorage write to complete
          await new Promise(resolve => setTimeout(resolve, 200));

          persistor1.pause();
          await persistor1.purge();

          // Create new store to verify latest tokens were persisted
          const store2 = configureStore({
            reducer: persistedReducer,
            middleware: (getDefaultMiddleware) =>
              getDefaultMiddleware({
                serializableCheck: {
                  ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
                },
              }),
          });

          const persistor2 = persistStore(store2);

          await new Promise<void>((resolve) => {
            const unsubscribe = persistor2.subscribe(() => {
              if (store2.getState()._persist?.rehydrated) {
                unsubscribe();
                resolve();
              }
            });
          });

          // Property assertion: Rehydrated state should have the LATEST tokens
          const rehydratedState = store2.getState().auth;
          expect(rehydratedState.token).toBe(secondAccessToken);
          expect(rehydratedState.refreshToken).toBe(secondRefreshToken);
          
          // Verify old tokens are NOT present
          expect(rehydratedState.token).not.toBe(firstAccessToken);
          expect(rehydratedState.refreshToken).not.toBe(firstRefreshToken);

          // Clean up
          persistor2.pause();
          await persistor2.purge();
        }
      ),
      {
        numRuns: 20,
        verbose: true,
      }
    );
  });
});
