import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiCall } from '../api/client';
import { useAuth } from './AuthContext';

const PermissionContext = createContext({
  permissions: [],
  hasPermission: () => false,
  loading: true
});

export const PermissionProvider = ({ children }) => {
  const { user, firebaseUser } = useAuth();
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPermissions = async () => {
      if (!user) {
        setPermissions([]);
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const response = await apiCall('/auth/permissions');
        setPermissions(response);
      } catch (error) {
        console.error('Failed to fetch permissions', error);
        setPermissions([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPermissions();
  }, [user]);

  const hasPermission = (permissionKey) => {
    // If it's a superadmin or they explicitly have the key
    // In our backend, role_superadmin has all permissions assigned.
    return permissions.includes(permissionKey);
  };

  return (
    <PermissionContext.Provider value={{ permissions, hasPermission, loading }}>
      {children}
    </PermissionContext.Provider>
  );
};

export const usePermissions = () => useContext(PermissionContext);

export const PermissionGuard = ({ permission, children, fallback = null }) => {
  const { hasPermission, loading } = usePermissions();

  if (loading) return null; // Or a spinner if preferred
  
  if (!hasPermission(permission)) {
    return fallback;
  }

  return children;
};
