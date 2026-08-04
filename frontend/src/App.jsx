import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { PermissionProvider } from './context/PermissionContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Landing from './pages/Landing';
import Pricing from './pages/Pricing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import APIKeys from './pages/APIKeys';
import Verify from './pages/Verify';
import Admin from './pages/Admin';
import SuperAdmin from './pages/SuperAdmin';
import Billing from './pages/Billing';
import Subscription from './pages/Subscription';
import Invoices from './pages/Invoices';
import PaymentHistory from './pages/PaymentHistory';
import Credits from './pages/Credits';
import Profile from './pages/Profile';
import AccountLayout from './components/AccountLayout';
import Settings from './pages/Settings';
import Security from './pages/Security';
import BillingSummary from './pages/BillingSummary';
import APISummary from './pages/APISummary';
import Usage from './pages/Usage';
import TeamMembers from './pages/TeamMembers';
import DeleteAccount from './pages/DeleteAccount';
import WorkspaceOverview from './pages/WorkspaceOverview';
import WorkspaceSettings from './pages/WorkspaceSettings';
import AcceptInvite from './pages/AcceptInvite';


function GuestRoute({ children }) {
  const { user, firebaseUser, loading } = useAuth();
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 70px)' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>Loading Auth...</div>
      </div>
    );
  }
  if (user && firebaseUser?.emailVerified) return <Navigate to="/dashboard" replace />;
  if (user && !firebaseUser?.emailVerified) return <Navigate to="/verify-email" replace />;
  return children;
}

export default function App() {
  return (
    <PermissionProvider>
      <Navbar />
      <main style={{ paddingTop: '75px' }}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
          <Route path="/signup" element={<GuestRoute><Signup /></GuestRoute>} />
          <Route path="/forgot-password" element={<GuestRoute><ForgotPassword /></GuestRoute>} />
          <Route path="/reset-password" element={<GuestRoute><ResetPassword /></GuestRoute>} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/accept-invite" element={<AcceptInvite />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/settings/keys" element={<APIKeys />} />
            <Route path="/verify" element={<Verify />} />
            <Route path="/billing" element={<Billing />} />
            <Route path="/subscription" element={<Subscription />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/payment-history" element={<PaymentHistory />} />
            <Route path="/credits" element={<Credits />} />
            
            {/* Account Center Routes */}
            <Route path="/account" element={<AccountLayout />}>
              <Route path="" element={<Navigate to="/account/profile" replace />} />
              <Route path="profile" element={<Profile />} />
              <Route path="settings" element={<Settings />} />
              <Route path="security" element={<Security />} />
              <Route path="billing" element={<BillingSummary />} />
              <Route path="api" element={<APISummary />} />
              <Route path="usage" element={<Usage />} />
              <Route path="workspace" element={<WorkspaceOverview />} />
              <Route path="team" element={<TeamMembers />} />
              <Route path="workspace-settings" element={<WorkspaceSettings />} />
              <Route path="delete" element={<DeleteAccount />} />
            </Route>
          </Route>

          {/* Admin routes */}
          <Route element={<ProtectedRoute requiredRole={['admin', 'superadmin']} />}>
            <Route path="/admin" element={<Admin />} />
          </Route>

          {/* Superadmin routes */}
          <Route element={<ProtectedRoute requiredRole="superadmin" />}>
            <Route path="/superadmin" element={<SuperAdmin />} />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </PermissionProvider>
  );
}
