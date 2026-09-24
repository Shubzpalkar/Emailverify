import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  getAdmins, getAllUsers, getSuperadminDashboard, 
  createAdmin, updateAdminCredits, suspendAdmin, impersonateUser
} from '../api/client';
import { useToast } from '../components/Toast';
import './Dashboard.css'; // Reuse dashboard styles for layout

export default function SuperAdmin() {
  const { showToast, checkAuth } = useToast();
  const auth = useAuth(); // get checkAuth from context manually below since useToast might not have it
  const { checkAuth: refreshContext } = useAuth();
  
  const [activeTab, setActiveTab] = useState('admins');
  
  const [admins, setAdmins] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  // Modals
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [newAdmin, setNewAdmin] = useState({ email: '', password: '', credit_pool: '' });

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      if (activeTab === 'admins') {
        setAdmins(await getAdmins());
      } else if (activeTab === 'users') {
        setAllUsers(await getAllUsers());
      } else if (activeTab === 'analytics') {
        const data = await getSuperadminDashboard();
        setAnalytics(data);
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleCreateAdmin = async (e) => {
    e.preventDefault();
    try {
      await createAdmin({ ...newAdmin, credit_pool: Number(newAdmin.credit_pool) || 0 });
      showToast('Admin created successfully');
      setShowAdminModal(false);
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handeAdminCredits = async (adminId, amount) => {
    const amt = parseInt(prompt("Amount to add/remove:", "10000"), 10);
    if (!amt || isNaN(amt)) return;
    try {
      await updateAdminCredits(adminId, amt);
      showToast('Credits updated');
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleSuspendAdmin = async (adminId) => {
    try {
      await suspendAdmin(adminId);
      showToast('Status toggled');
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleImpersonate = async (userId) => {
    try {
      await impersonateUser(userId);
      showToast('Impersonation token set. Refreshing...');
      await refreshContext();
      window.location.href = '/dashboard';
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <section className="container page-enter" style={{ paddingTop: '1rem' }}>
      <div className="dashboard-header" style={{ marginTop: '2rem', marginBottom: '1rem' }}>
        <h1>System Superadmin Control</h1>
      </div>

      <div className="tabs" style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button className={`btn-secondary ${activeTab === 'admins' ? 'active' : ''}`} onClick={() => setActiveTab('admins')}>Admins</button>
        <button className={`btn-secondary ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>All Users</button>
        <button className={`btn-secondary ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>Analytics</button>
      </div>

      {activeTab === 'admins' && (
        <div className="glass-card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Admin Accounts</h3>
            <button className="btn-primary" onClick={() => setShowAdminModal(true)}>+ Create Admin</button>
          </div>
          <div className="table-container mt-4">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Pool / Used</th>
                  <th>Users / Jobs</th>
                  <th>Last Login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {admins.map(a => (
                  <tr key={a.id}>
                    <td>{a.email}</td>
                    <td>
                      <span className={`tag tag-${a.is_active ? 'valid' : 'invalid'}`}>
                        {a.is_active ? 'Active' : 'Suspended'}
                      </span>
                    </td>
                    <td>{a.credit_pool.toLocaleString()} / {a.credits_used.toLocaleString()}</td>
                    <td>{a.user_count} / {a.job_count}</td>
                    <td>{a.last_login ? new Date(a.last_login).toLocaleDateString() : 'Never'}</td>
                    <td style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn-secondary btn-small" onClick={() => handeAdminCredits(a.id)}>+/- Credits</button>
                      <button className="btn-secondary btn-small" onClick={() => handleSuspendAdmin(a.id)}>Toggle Status</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="glass-card">
          <div className="card-header">
            <h3>Global User Overview</h3>
          </div>
          <div className="table-container mt-4">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Admin Owner</th>
                  <th>Status</th>
                  <th>Tier</th>
                  <th>Credits</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {allUsers.map(u => (
                  <tr key={u.id}>
                    <td>{u.email}</td>
                    <td>{u.admin_email || 'System'}</td>
                    <td>
                      <span className={`tag tag-${u.is_active ? 'valid' : 'invalid'}`}>
                        {u.is_active ? 'Active' : 'Suspended'}
                      </span>
                    </td>
                    <td><span className="tag tag-unknown">{u.tier}</span></td>
                    <td>{u.credit_pool.toLocaleString()}</td>
                    <td>
                      <button className="btn-secondary btn-small" onClick={() => handleImpersonate(u.id)}>Impersonate</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'analytics' && analytics && (
        <div className="dashboard-grid">
          <div className="glass-card stat-card">
            <h3>Total Platform Admins</h3>
            <div>{analytics.total_admins}</div>
          </div>
          <div className="glass-card stat-card">
            <h3>Total End Users</h3>
            <div>{analytics.total_users}</div>
          </div>
          <div className="glass-card stat-card">
            <h3>Total Jobs Run</h3>
            <div>{analytics.total_jobs}</div>
          </div>
          <div className="glass-card stat-card">
            <h3>Credits Dispersed</h3>
            <div>{analytics.total_credits_allocated.toLocaleString()}</div>
          </div>
        </div>
      )}

      {showAdminModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="glass-card page-enter" style={{ minWidth: '400px' }} role="dialog" aria-modal="true" aria-labelledby="create-admin-title">
            <h2 id="create-admin-title">Create Admin</h2>
            <form onSubmit={handleCreateAdmin}>
              <div style={{ marginBottom: '1rem', marginTop: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Email</label>
                <input type="email" value={newAdmin.email} onChange={e => setNewAdmin({...newAdmin, email: e.target.value})} className="input-field w-full" required />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Password</label>
                <input type="password" value={newAdmin.password} onChange={e => setNewAdmin({...newAdmin, password: e.target.value})} className="input-field w-full" required />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Initial Credit Pool</label>
                <input type="number" value={newAdmin.credit_pool} onChange={e => setNewAdmin({...newAdmin, credit_pool: e.target.value})} className="input-field w-full" required />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Create</button>
                <button type="button" className="btn-secondary" onClick={() => setShowAdminModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
