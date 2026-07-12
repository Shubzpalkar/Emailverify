import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ requiredRole }) {
  const { user, firebaseUser, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 70px)' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>Loading...</div>
      </div>
    );
  }

  if (!firebaseUser || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!firebaseUser.emailVerified || !user.email_verified) {
    return <Navigate to="/verify-email" replace />;
  }

  if (requiredRole) {
    const allowed = Array.isArray(requiredRole)
      ? requiredRole.includes(user.role)
      : user.role === requiredRole;
    if (!allowed) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return <Outlet />;
}