import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { validateInvite, acceptInvite } from '../api/client';
import { auth } from '../firebase/config';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from 'firebase/auth';
import { CheckCircle, WarningCircle, EnvelopeSimple } from '@phosphor-icons/react';
import './Auth.css'; // Reuse existing auth styles

export default function AcceptInvite() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [inviteData, setInviteData] = useState(null);
  
  const [password, setPassword] = useState('');
  
  useEffect(() => {
    if (!token) {
      setError('Invalid invitation link');
      setLoading(false);
      return;
    }
    
    validateInvite(token)
      .then(data => {
        setInviteData(data);
      })
      .catch(err => {
        setError(err.message || 'Failed to validate invitation');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    
    try {
      let userCredential;
      
      // If user exists in Firebase, just sign them in. Otherwise, create the account.
      if (inviteData.user_exists) {
        userCredential = await signInWithEmailAndPassword(auth, inviteData.email, password);
      } else {
        userCredential = await createUserWithEmailAndPassword(auth, inviteData.email, password);
      }
      
      const fbToken = await userCredential.user.getIdToken();
      
      // Tell backend to finalize invite
      await acceptInvite(token, { firebase_token: fbToken });
      
      // Redirect to dashboard
      navigate('/dashboard');
      
    } catch (err) {
      if (err.code === 'auth/wrong-password') {
        setError('Incorrect password for this account.');
      } else if (err.code === 'auth/weak-password') {
        setError('Password must be at least 6 characters.');
      } else {
        setError(err.message || 'An error occurred during account creation');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="auth-container">
        <div className="auth-card glass-card">
          <div className="text-center p-4">Validating invitation...</div>
        </div>
      </div>
    );
  }

  if (error && !inviteData) {
    return (
      <div className="auth-container">
        <div className="auth-card glass-card fade-in">
          <div className="auth-header text-center">
            <WarningCircle size={48} color="var(--danger-color)" className="mx-auto mb-4" />
            <h2>Invalid Invitation</h2>
            <p className="text-secondary">{error}</p>
          </div>
          <div className="mt-6 text-center">
            <Link to="/login" className="btn-primary" style={{ display: 'inline-block' }}>Go to Login</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card glass-card slide-up">
        <div className="auth-header text-center">
          <div className="auth-icon-wrapper mx-auto mb-4" style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(76, 175, 80, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <EnvelopeSimple size={32} color="var(--success-color)" />
          </div>
          <h2>Join {inviteData.workspace_name}</h2>
          <p className="text-secondary">
            You've been invited to join as a <strong>{inviteData.role}</strong>.
          </p>
        </div>

        {error && <div className="error-alert mt-4">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form mt-6">
          <div className="form-group">
            <label>Email Address</label>
            <input type="email" value={inviteData.email} disabled className="disabled-input" />
          </div>
          
          <div className="form-group">
            <label>{inviteData.user_exists ? 'Enter your password' : 'Create a Password'}</label>
            <input 
              type="password" 
              required 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={inviteData.user_exists ? "Password" : "At least 6 characters"}
            />
          </div>

          <button type="submit" className="btn-primary w-full mt-2" disabled={submitting}>
            {submitting ? 'Processing...' : (inviteData.user_exists ? 'Log in & Accept' : 'Create Account & Accept')}
          </button>
        </form>
      </div>
    </div>
  );
}
