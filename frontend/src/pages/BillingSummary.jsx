import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export default function BillingSummary() {
  const { user } = useAuth();
  
  return (
    <div className="glass-card" style={{ padding: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>Billing Summary</h2>
      
      <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Current Plan</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem', fontWeight: 'bold' }}>
            {user?.plan || 'Free'}
          </p>
        </div>
        
        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Credits Remaining</h4>
          <p style={{ fontSize: '1.5rem', marginTop: '0.5rem', fontWeight: 'bold' }}>
            {user?.credit_pool?.toLocaleString?.() ?? user?.credits}
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Subscription Status</h4>
          <p style={{ fontSize: '1.1rem', marginTop: '0.5rem', color: 'var(--success)' }}>
            Active
          </p>
        </div>

        <div className="stat-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Next Renewal Date</h4>
          <p style={{ fontSize: '1.1rem', marginTop: '0.5rem' }}>
            -- Placeholder --
          </p>
        </div>
      </div>
      
      <div style={{ marginTop: '2rem' }}>
        <Link to="/pricing" className="btn-primary" style={{ display: 'inline-block' }}>
          Upgrade Plan
        </Link>
      </div>

      <hr style={{ margin: '2rem 0', borderColor: 'var(--border)' }} />

      <h3 style={{ marginBottom: '1rem' }}>Payment History</h3>
      <div className="table-responsive" style={{ opacity: 0.5 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Amount</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan="4" style={{ textAlign: 'center' }}>No payment history available.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
