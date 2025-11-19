import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../utils/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    // Skip auth check on mount - user must login
    setLoading(false);
  }, []);

  const checkAuth = async () => {
    try {
      // Try to refresh token to check if user is authenticated
      await authAPI.refresh();
      setUser({ authenticated: true });
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      const data = await authAPI.login(email, password);
      setUser({ authenticated: true });
      return { success: true, data };
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Login failed. Please try again.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const signup = async (firstName, lastName, email, password) => {
    try {
      setError(null);
      const data = await authAPI.signup(firstName, lastName, email, password);
      return { success: true, data };
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Signup failed. Please try again.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    setUser(null);
    // Clear any stored tokens or user data
    // The backend will handle cookie invalidation
  };

  const value = {
    user,
    loading,
    error,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};