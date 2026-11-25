// ── Auth Context ──────────────────────────────────────────
// Provides global authentication state and helpers via React Context.

import { createContext, useContext, useState, useCallback } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';

const AuthContext = createContext(null);

/** Fake async delay to simulate a real API call */
const fakeDelay = (ms = 800) => new Promise(res => setTimeout(res, ms));

export function AuthProvider({ children }) {
  const [storedUser, setStoredUser] = useLocalStorage('hp_user', null);
  const [storedUsers, setStoredUsers] = useLocalStorage('hp_users', []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAuthenticated = Boolean(storedUser);

  /**
   * Register a new user.
   * @param {{ name: string, email: string, password: string }} data
   */
  const signup = useCallback(async (data) => {
    setLoading(true);
    setError(null);
    try {
      await fakeDelay();
      const existing = storedUsers.find(u => u.email === data.email);
      if (existing) throw new Error('An account with this email already exists.');

      const newUser = {
        id: crypto.randomUUID(),
        name: data.name,
        email: data.email,
        password: data.password, // NOTE: never store plain-text in production
        createdAt: new Date().toISOString(),
        avatar: `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(data.name)}&backgroundColor=6d28d9`,
      };
      setStoredUsers(prev => [...prev, newUser]);

      // Auto-login after signup
      const { password: _, ...safeUser } = newUser;
      setStoredUser(safeUser);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, [storedUsers, setStoredUsers, setStoredUser]);

  /**
   * Authenticate an existing user.
   * @param {{ email: string, password: string }} data
   */
  const login = useCallback(async (data) => {
    setLoading(true);
    setError(null);
    try {
      await fakeDelay();
      const user = storedUsers.find(
        u => u.email === data.email && u.password === data.password
      );
      if (!user) throw new Error('Invalid email or password.');

      const { password: _, ...safeUser } = user;
      setStoredUser(safeUser);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, [storedUsers, setStoredUser]);

  /** Sign out the current user */
  const logout = useCallback(() => {
    setStoredUser(null);
    setError(null);
  }, [setStoredUser]);

  /** Clear any auth error */
  const clearError = useCallback(() => setError(null), []);

  const value = {
    user: storedUser,
    isAuthenticated,
    loading,
    error,
    login,
    signup,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Consume auth context */
export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used inside <AuthProvider>');
  return ctx;
}
