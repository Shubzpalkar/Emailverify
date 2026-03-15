import { useState, useEffect } from 'react';
import { apiCall } from '../api/client';
import { useToast } from '../components/Toast';
import './Admin.css';

export default function Admin() {
  const { showToast } = useToast();
  const [users, setUsers] = useState([]);

  const loadUsers = async () => {
    try {
      const data = await apiCall('/admin/users');
      setUsers(data);
    } catch (err) {
      showToast(err.message || 'Failed to load users', 'error');
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const addCredits = async (userId, amount) => {
    try {
      await apiCall(`/admin/users/${userId}/credits?amount=${amount}`, { method: 'POST' });
      showToast(`Added ${amount.toLocaleString()} credits`);
      loadUsers();
    } catch (err) {
      showToast(err.message || 'Failed to add credits', 'error');
    }
  };

  return (
    <section className="container page-enter" style={{ paddingTop: '1rem' }}>
      <div className="dashboard-header" style={{ marginTop: '3rem', marginBottom: '2rem' }}>
        <h2>Admin Panel</h2>
      </div>

      <div className="glass-card admin-table-card">
        <div className="card-header">
          <h3>All Users</h3>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>User ID</th>
                <th>Email</th>
                <th>Role</th>
                <th>Credits</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {user.id.substring(0, 8)}...
                  </td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`tag tag-${user.role === 'admin' ? 'warning' : 'valid'}`}>
                      {user.role}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{user.credits.toLocaleString()}</td>
                  <td className="admin-actions">
                    <button className="btn-secondary btn-small" onClick={() => addCredits(user.id, 10000)}>
                      +10k
                    </button>
                    <button className="btn-secondary btn-small" onClick={() => addCredits(user.id, 100000)}>
                      +100k
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
