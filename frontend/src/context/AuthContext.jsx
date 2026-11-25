
import { createContext, useContext, useState, useCallback } from 'react';
import { apiRequest } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAuthenticated = Boolean(user);

  const login = useCallback(async (data) => {
    setLoading(true);
    setError(null);

    try {
      await apiRequest('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const currentUser = await apiRequest('/api/auth/me');

      setUser(currentUser);

      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally { 
      setLoading(false);
    }
  }, []);

  const signup = useCallback(async (data) => {
    setLoading(true);
    setError(null);

    try {
      await apiRequest('/api/auth/signup', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiRequest('/api/auth/logout', {
        method: 'POST',
      });
    } finally {
      setUser(null);
      setError(null);
    }
  }, []);

  const value = {
    user,
    isAuthenticated,
    loading,
    error,
    login,
    signup,
    logout,
    clearError: () => setError(null),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);

  if (!ctx) {
    throw new Error('useAuthContext must be used inside AuthProvider');
  }

  return ctx;
}
