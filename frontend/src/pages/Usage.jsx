import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Usage() {
  const { user } = useAuth();
  const [data, setData] = useState({
    verifications_today: 0,
    verifications_month: 0,
    total_verified: 0,
    success_rate: 0.0,
    last_verification: null,
    recent_jobs: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUsageSummary() {
      if (!user) return;
      try {
        const res = await fetch('http://localhost:8000/api/account/usage', {
          headers: {
            'Authorization': `Bearer ${await user.getIdToken()}`
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
    fetchUsageSummary();
  }, [user]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="glass-card" style={{ padding: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>Usage Summary</h2>
      
      <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Verifications Today</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
            {data.verifications_today}
          </p>
        </div>
        
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Verifications This Month</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
            {data.verifications_month}
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Total Verified</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
            {data.total_verified}
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Success Rate</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem', color: 'var(--success)' }}>
            {data.success_rate.toFixed(1)}%
          </p>
        </div>
      </div>

      <hr style={{ margin: '2rem 0', borderColor: 'var(--border)' }} />

      <h3 style={{ marginBottom: '1rem' }}>Recent Activity</h3>
      <p style={{ color: 'var(--text-muted)' }}>
        You have run <strong>{data.recent_jobs}</strong> total verification jobs.
        <br/><br/>
        {data.last_verification 
          ? `Last verification: ${new Date(data.last_verification).toLocaleString()}` 
          : 'No recent verifications.'}
      </p>
    </div>
  );
}
