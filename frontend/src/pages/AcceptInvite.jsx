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
      <div className="auth-container page-enter">
        <div className="auth-card glass-card">
          <div className="auth-loading" role="status" aria-live="polite">
            <span className="auth-loading-spinner" aria-hidden="true" />
            <span>Validating your invitation...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error && !inviteData) {
    return (
      <div className="auth-container page-enter">
        <div className="auth-card glass-card">
          <div className="auth-icon-wrapper auth-icon-error" aria-hidden="true">
            <WarningCircle size={30} weight="duotone" />
          </div>
          <div className="auth-header">
            <h1>Invalid invitation</h1>
            <p>{error}</p>
          </div>
          <div className="mt-6 text-center">
            <Link to="/login" className="btn-primary btn-full auth-return-action">Go to login</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container page-enter">
      <div className="auth-card glass-card">
        <div className="auth-icon-wrapper auth-icon-success" aria-hidden="true">
          <EnvelopeSimple size={30} weight="duotone" />
        </div>
        <div className="auth-header">
          <div className="auth-eyebrow">Workspace invitation</div>
          <h1>Join {inviteData.workspace_name}</h1>
          <p>
            You have been invited to join as a <strong>{inviteData.role}</strong>.
          </p>
        </div>

        {error && <div className="error-alert" role="alert">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form mt-6">
          <div className="form-group">
            <label htmlFor="invite-email">Email address</label>
            <input id="invite-email" type="email" autoComplete="email" value={inviteData.email} disabled className="disabled-input" />
          </div>

          <div className="form-group">
            <label htmlFor="invite-password">{inviteData.user_exists ? 'Enter your password' : 'Create a password'}</label>
            <input
              id="invite-password"
              type="password"
              autoComplete={inviteData.user_exists ? 'current-password' : 'new-password'}
              required
              minLength={inviteData.user_exists ? undefined : 6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={inviteData.user_exists ? "Password" : "At least 6 characters"}
            />
          </div>

          <button type="submit" className="btn-primary btn-full" disabled={submitting}>
            {submitting ? 'Processing...' : (inviteData.user_exists ? 'Log in & Accept' : 'Create Account & Accept')}
          </button>
        </form>
      </div>
    </div>
  );
}
