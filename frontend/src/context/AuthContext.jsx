import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiCall } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const userData = await apiCall('/auth/me');
      setUser(userData);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    await fetch('/api/auth/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    }).then(res => {
      if (!res.ok) throw new Error('Invalid credentials');
      return res.json();
    });

    // Re-fetch user data from the auth cookie
    const userData = await apiCall('/auth/me');
    setUser(userData);
    return userData;
  };

  const signup = async (email, password) => {
    await apiCall('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  };

  const logout = async () => {
    await apiCall('/auth/logout', { method: 'POST' });
    setUser(null);
  };

  const updateCredits = (delta) => {
    setUser(prev => prev ? { ...prev, credits: prev.credits + delta } : prev);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, updateCredits, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
