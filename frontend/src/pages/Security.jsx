import { useAuth } from '../context/AuthContext';

export default function Security() {
  const { user, firebaseUser } = useAuth();
  
  const authProvider = firebaseUser?.providerData?.[0]?.providerId || 'password';

  return (
    <div className="glass-card" style={{ padding: '2rem' }}>
      <h1 style={{ marginBottom: '1.5rem' }}>Security</h1>
      
      <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Authentication Provider</h4>
          <p style={{ fontSize: '1.1rem', marginTop: '0.5rem', textTransform: 'capitalize' }}>
            {authProvider.replace('.com', '')}
          </p>
        </div>
        
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Account Status</h4>
          <p style={{ fontSize: '1.1rem', marginTop: '0.5rem' }}>
            {user?.status || 'Active'}
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Email Verification</h4>
          <p style={{ fontSize: '1.1rem', marginTop: '0.5rem', color: user?.email_verified ? 'var(--success)' : 'var(--warning)' }}>
            {user?.email_verified ? 'Verified' : 'Pending'}
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Last Login</h4>
          <p style={{ fontSize: '1.1rem', marginTop: '0.5rem' }}>
            {user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}
          </p>
        </div>
      </div>
      
      <p style={{ marginTop: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        * Active session management and Two-Factor Authentication (2FA) will be available in Version 2.
      </p>
    </div>
  );
}
