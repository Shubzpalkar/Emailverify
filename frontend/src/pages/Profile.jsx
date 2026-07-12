import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import './Auth.css';

export default function Profile() {
  const { user, firebaseUser, resendVerificationEmail } = useAuth();

  return (
    <div className="glass-card profile-card" style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>User Profile</h2>
        <Link to="/account/settings" className="btn-secondary btn-small">Edit Profile</Link>
      </div>
      
      <dl className="profile-list" style={{ maxWidth: '600px' }}>
        <div><dt>Name</dt><dd>{user?.display_name || firebaseUser?.displayName || 'Not set'}</dd></div>
        <div><dt>Email</dt><dd>{user?.email}</dd></div>
        <div><dt>Company</dt><dd>{user?.company || 'Not set'}</dd></div>
        <div><dt>Phone</dt><dd>{user?.phone || 'Not set'}</dd></div>
        <div><dt>Current Plan</dt><dd>{user?.plan}</dd></div>
        <div><dt>Credits Remaining</dt><dd>{user?.credit_pool?.toLocaleString?.() ?? user?.credits}</dd></div>
        <div><dt>Account Created</dt><dd>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</dd></div>
        <div><dt>Last Login</dt><dd>{user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}</dd></div>
        <div>
          <dt>Email Verified</dt>
          <dd style={{ color: user?.email_verified ? 'var(--success)' : 'var(--warning)' }}>
            {user?.email_verified ? 'Verified' : 'Pending'}
          </dd>
        </div>
      </dl>
      {!user?.email_verified && (
        <button type="button" className="btn-secondary" onClick={resendVerificationEmail} style={{ marginTop: '1.5rem' }}>
          Resend verification email
        </button>
      )}
    </div>
  );
}