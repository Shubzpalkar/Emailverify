import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../components/Toast';

export default function DeleteAccount() {
  const { user, firebaseUser, logout } = useAuth();
  const navigate = useNavigate();
  const { showToast } = useToast();
  
  const [showConfirm, setShowConfirm] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDelete = async (e) => {
    e.preventDefault();
    if (confirmText !== 'DELETE') return;
    
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/account', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${await firebaseUser.getIdToken()}`
        }
      });
      
      if (!res.ok) throw new Error('Failed to delete account');
      
      showToast('Account successfully deleted.', 'success');
      await logout();
      navigate('/');
    } catch (error) {
      showToast(error.message, 'error');
      setLoading(false);
    }
  };

  return (
    <div className="glass-card" style={{ padding: '2rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--danger)' }}>Delete Account</h2>
      
      <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
        <h4 style={{ color: 'var(--danger)', marginBottom: '0.5rem' }}>Warning: This action is permanent</h4>
        <p style={{ color: 'var(--text-muted)' }}>
          Once you delete your account, there is no going back. Please be certain.
          This will permanently delete your user data, verifications, api keys, and billing history.
        </p>
      </div>

      {!showConfirm ? (
        <button onClick={() => setShowConfirm(true)} className="btn-danger">
          Delete My Account
        </button>
      ) : (
        <form onSubmit={handleDelete} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '400px' }}>
          <div className="form-group">
            <label>Please type <strong>DELETE</strong> to confirm:</label>
            <input 
              type="text" 
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              className="form-control"
              placeholder="DELETE"
              required
            />
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button 
              type="submit" 
              className="btn-danger" 
              disabled={confirmText !== 'DELETE' || loading}
            >
              {loading ? 'Deleting...' : 'Confirm Deletion'}
            </button>
            <button 
              type="button" 
              onClick={() => { setShowConfirm(false); setConfirmText(''); }} 
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
