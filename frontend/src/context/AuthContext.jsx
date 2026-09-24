import { createContext, useContext, useEffect, useState } from 'react';
import { apiCall } from '../api/client';
import { auth } from '../firebase/config';
import {
  googleLogin as firebaseGoogleLogin,
  onIdTokenChanged,
  login as firebaseLogin,
  logout as firebaseLogout,
  sendVerificationEmail,
  signup as firebaseSignup,
} from '../firebase/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(auth));

  const syncUser = async () => {
    const userData = await apiCall('/auth/sync-user', { method: 'POST' });
    setUser(userData);
    return userData;
  };

  const checkAuth = async () => {
    if (!auth?.currentUser) {
      setUser(null);
      return null;
    }
    const userData = await apiCall('/auth/me');
    setUser(userData);
    return userData;
  };

  useEffect(() => {
    if (!auth) return undefined;

    const unsubscribe = onIdTokenChanged(auth, async (currentFirebaseUser) => {
      setFirebaseUser(currentFirebaseUser);
      if (!currentFirebaseUser) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        await syncUser();
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    });

    return unsubscribe;
  }, []);

  const login = async (email, password) => {
    const firebaseUserResult = await firebaseLogin(email, password);
    const userData = await syncUser();
    return { firebaseUser: firebaseUserResult, user: userData };
  };

  const signup = async (email, password) => {
    const firebaseUserResult = await firebaseSignup(email, password);
    const userData = await syncUser();
    return { firebaseUser: firebaseUserResult, user: userData };
  };

  const googleLogin = async () => {
    const firebaseUserResult = await firebaseGoogleLogin();
    const userData = await syncUser();
    return { firebaseUser: firebaseUserResult, user: userData };
  };

  const logout = async () => {
    try {
      await apiCall('/auth/logout', { method: 'POST' });
    } catch {
      // Server-side logout is best-effort; Firebase owns the browser session.
    }
    await firebaseLogout();
    setUser(null);
    setFirebaseUser(null);
  };

  const resendVerificationEmail = async () => {
    await sendVerificationEmail();
  };

  const updateCredits = (delta) => {
    setUser(prev => prev ? {
      ...prev,
      credits: (prev.credits || 0) + delta,
      credit_pool: (prev.credit_pool || 0) + delta,
    } : prev);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        firebaseUser,
        loading,
        login,
        signup,
        googleLogin,
        logout,
        resendVerificationEmail,
        updateCredits,
        checkAuth,
        syncUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}