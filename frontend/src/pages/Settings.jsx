import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';

export default function Settings() {
  const { user, sendPasswordReset } = useAuth();
  const { showToast } = useToast();
  const [formData, setFormData] = useState({
    display_name: user?.display_name || '',
    company: user?.company || '',
    phone: user?.phone || ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/account/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await user.getIdToken()}`
        },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error('Failed to update profile');
      showToast('Profile updated successfully', 'success');
      // In a real app we might want to refresh the user context here
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async () => {
    try {
      await sendPasswordReset(user.email);
      showToast('Password reset email sent. Check your inbox.', 'success');
    } catch (error) {
      showToast('Failed to send reset email', 'error');
    }
  };

  return (
    <div className="glass-card" style={{ padding: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>Account Settings</h2>
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '500px' }}>
        <div className="form-group">
          <label>Name</label>
          <input type="text" name="display_name" value={formData.display_name} onChange={handleChange} className="form-control" />
        </div>
        <div className="form-group">
          <label>Company</label>
          <input type="text" name="company" value={formData.company} onChange={handleChange} className="form-control" />
        </div>
        <div className="form-group">
          <label>Phone Number</label>
          <input type="text" name="phone" value={formData.phone} onChange={handleChange} className="form-control" />
        </div>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </form>

      <hr style={{ margin: '2rem 0', borderColor: 'var(--border)' }} />

      <h3 style={{ marginBottom: '1rem' }}>Security & Authentication</h3>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <button type="button" onClick={handlePasswordReset} className="btn-secondary">
          Change Password
        </button>
      </div>
    </div>
  );
}
