import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function APISummary() {
  const { user, firebaseUser } = useAuth();
  const [data, setData] = useState({
    api_enabled: false,
    api_key_count: 0,
    requests_today: 0,
    requests_month: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchApiSummary() {
      if (!user) return;
      try {
        const res = await fetch('http://localhost:8000/api/account/api-summary', {
          headers: {
            'Authorization': `Bearer ${await firebaseUser.getIdToken()}`
          }
        });
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchApiSummary();
  }, [user]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="glass-card" style={{ padding: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>API Summary</h2>
      
      <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>API Status</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem', color: data.api_enabled ? 'var(--success)' : 'var(--warning)' }}>
            {data.api_enabled ? 'Enabled' : 'Disabled'}
          </p>
        </div>
        
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Active API Keys</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
            {data.api_key_count}
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Requests Today</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
            {data.requests_today}
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Requests This Month</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
            {data.requests_month}
          </p>
        </div>
      </div>
      
      <p style={{ marginTop: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        * Note: Detailed API usage statistics will be available in a future update.
      </p>
    </div>
  );
}
