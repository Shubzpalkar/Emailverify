import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getMyUsers, createUser, updateUserCredits, updateUserTier, suspendUser, getAdminDashboard, getMyJobs, getAdminBillingStats } from '../api/client';
import { useToast } from '../components/Toast';
import './Admin.css';


export default function Admin() {
  const { showToast } = useToast();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  
  const [users, setUsers] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [billingStats, setBillingStats] = useState(null);

  const [showUserModal, setShowUserModal] = useState(false);
  const [newUser, setNewUser] = useState({ email: '', password: '', initial_credits: '' });

  const loadData = async () => {
    try {
      if (activeTab === 'users') {
        const u = await getMyUsers();
        setUsers(u);
      } else if (activeTab === 'jobs') {
        const j = await getMyJobs();
        setJobs(j);
      } else if (activeTab === 'billing') {
        const bs = await getAdminBillingStats();
        setBillingStats(bs);
      }
      const d = await getAdminDashboard();
      setDashboard(d);
    } catch (err) {
      showToast(err.message || 'Failed to load data', 'error');
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await createUser({ 
        email: newUser.email, 
        password: newUser.password || undefined, 
        initial_credits: Number(newUser.initial_credits) || 0 
      });
      showToast('User created successfully');
      setShowUserModal(false);
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleCredits = async (userId) => {
    const amt = parseInt(prompt("Amount to add/remove:", "1000"), 10);
    if (!amt || isNaN(amt)) return;
    try {
      await updateUserCredits(userId, amt);
      showToast('Credits updated');
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleTier = async (userId) => {
    const tier = prompt("Enter new tier (free, standard, power, enterprise):", "standard");
    if (!tier) return;
    try {
      await updateUserTier(userId, tier.toLowerCase());
      showToast('Tier updated');
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleSuspend = async (userId) => {
    try {
      await suspendUser(userId);
      showToast('User suspension toggled');
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <section className="container page-enter" style={{ paddingTop: '1rem' }}>
      <div className="dashboard-header" style={{ marginTop: '2rem', marginBottom: '1rem' }}>
        <h2>Admin Panel — My Users</h2>
      </div>

      {dashboard && (
        <div style={{ padding: '1rem', background: 'var(--surface)', borderRadius: '1rem', marginBottom: '2rem', display: 'flex', gap: '2rem', fontSize: '0.95rem' }}>
          <div><strong>My Credit Pool remaining:</strong> {dashboard.credits_remaining === 999999999 ? 'Unlimited' : dashboard.credits_remaining.toLocaleString()}</div>
          <div><strong>Total Scoped Users:</strong> {dashboard.total_users}</div>
          <div><strong>Total Scoped Jobs:</strong> {dashboard.total_jobs}</div>
        </div>
      )}

      <div className="tabs" style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button className={`btn-secondary ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>My Users</button>
        <button className={`btn-secondary ${activeTab === 'jobs' ? 'active' : ''}`} onClick={() => setActiveTab('jobs')}>My Jobs</button>
        <button className={`btn-secondary ${activeTab === 'billing' ? 'active' : ''}`} onClick={() => setActiveTab('billing')}>Billing Stats</button>
      </div>

      {activeTab === 'users' && (
        <div className="glass-card admin-table-card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Scoped Users</h3>
            <button className="btn-primary" onClick={() => setShowUserModal(true)}>+ Create User</button>
          </div>
          <div className="table-container mt-4">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Tier</th>
                  <th>Credits</th>
                  <th>Jobs / verified</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>{u.email}</td>
                    <td><span className={`tag tag-${u.is_active ? 'valid' : 'invalid'}`}>{u.is_active ? 'Active' : 'Suspended'}</span></td>
                    <td><span className="tag tag-unknown">{u.tier}</span></td>
                    <td style={{ fontWeight: 600 }}>{u.credit_pool.toLocaleString()}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{u.job_count} / {u.emails_verified.toLocaleString()}</td>
                    <td className="admin-actions">
                      <button className="btn-secondary btn-small" onClick={() => handleCredits(u.id)}>+/- Credits</button>
                      <button className="btn-secondary btn-small" onClick={() => handleTier(u.id)}>Set Tier</button>
                      <button className="btn-secondary btn-small" onClick={() => handleSuspend(u.id)}>Suspend</button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>No users managed yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'jobs' && (
        <div className="glass-card">
          <div className="card-header">
            <h3>Scoped Jobs</h3>
          </div>
          <div className="table-container mt-4">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>User Email</th>
                  <th>File Name</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(j => (
                  <tr key={j.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{j.id.substring(0,8)}</td>
                    <td>{j.user_email}</td>
                    <td>{j.file_name}</td>
                    <td><span className={`tag tag-${j.status === 'completed' ? 'valid' : 'warning'}`}>{j.status}</span></td>
                    <td>{new Date(j.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'billing' && billingStats && (
        <div className="glass-card" style={{ padding: '2rem' }}>
          <div className="card-header" style={{ marginBottom: '1.5rem' }}>
            <h3>Billing & Subscription Analytics</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem' }}>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Revenue</div>
              <h2 style={{ marginTop: '0.5rem', color: 'var(--success)' }}>₹{billingStats.total_revenue.toLocaleString()}</h2>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Monthly Revenue (30d)</div>
              <h2 style={{ marginTop: '0.5rem', color: 'var(--primary)' }}>₹{billingStats.monthly_revenue.toLocaleString()}</h2>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Active Subscribers</div>
              <h2 style={{ marginTop: '0.5rem' }}>{billingStats.active_subscribers}</h2>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Failed Payments</div>
              <h2 style={{ marginTop: '0.5rem', color: 'var(--error)' }}>{billingStats.failed_payments}</h2>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Credits Allotted/Sold</div>
              <h2 style={{ marginTop: '0.5rem', color: 'var(--warning)' }}>{billingStats.credits_sold.toLocaleString()}</h2>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Credits Consumed</div>
              <h2 style={{ marginTop: '0.5rem', color: 'var(--text-muted)' }}>{billingStats.credits_consumed.toLocaleString()}</h2>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Most Popular Plan</div>
              <h2 style={{ marginTop: '0.5rem', color: 'var(--primary)' }}>{billingStats.popular_plan}</h2>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'var(--border)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Subscription Growth</div>
              <h2 style={{ marginTop: '0.5rem', color: 'var(--success)' }}>+12.4%</h2>
            </div>
          </div>
        </div>
      )}

      {showUserModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="glass-card page-enter" style={{ minWidth: '400px' }}>
            <h2>Create New Scoped User</h2>
            <form onSubmit={handleCreateUser}>
              <div style={{ marginBottom: '1rem', marginTop: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Email</label>
                <input type="email" value={newUser.email} onChange={e => setNewUser({...newUser, email: e.target.value})} className="input-field w-full" required />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Password (Leaves blank for auto-generate)</label>
                <input type="password" value={newUser.password} onChange={e => setNewUser({...newUser, password: e.target.value})} className="input-field w-full" />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Initial Credits (deducted from your pool)</label>
                <input type="number" value={newUser.initial_credits} onChange={e => setNewUser({...newUser, initial_credits: e.target.value})} className="input-field w-full" required />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Create</button>
                <button type="button" className="btn-secondary" onClick={() => setShowUserModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
