import { create, type StoreApi } from 'zustand';
import { persist } from 'zustand/middleware';
import zukeeper from 'zukeeper';
import type { User } from '../types';

interface AuthState {
  // State
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  // Actions
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (patch: Partial<User>) => void;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  zukeeper(
    persist(
      (set: StoreApi<AuthState>['setState']) => ({
        // Initial state
        user: null,
        token: null,
        isAuthenticated: false,

        // Login action - set token and user
        login: (token: string, user: User) => {
          set({
            token,
            user,
            isAuthenticated: true,
          });
        },

        // Logout action - clear everything
        logout: () => {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });
        },

        // Update user data partially
        updateUser: (patch: Partial<User>) => {
          set((state) => ({
            user: state.user ? { ...state.user, ...patch } : null,
          }));
        },

        // Set user directly (e.g., after fetching profile)
        setUser: (user: User | null) => {
          set({
            user,
            isAuthenticated: !!user,
          });
        },
      }),
      {
        name: 'auth-storage', // localStorage key
        partialize: (state) => ({
          user: state.user,
          token: state.token,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    )
  )
);

// Selector hooks for convenience
export const useUser = () => useAuthStore((state) => state.user);
export const useToken = () => useAuthStore((state) => state.token);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
