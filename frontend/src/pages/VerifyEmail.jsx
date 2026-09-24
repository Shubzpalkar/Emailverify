import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { EnvelopeOpen } from '@phosphor-icons/react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import './Auth.css';

export default function VerifyEmail() {
  const { firebaseUser, resendVerificationEmail, checkAuth, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [sending, setSending] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    if (!firebaseUser) navigate('/login', { replace: true });
  }, [firebaseUser, navigate]);

  const handleResend = async () => {
    setSending(true);
    try {
      await resendVerificationEmail();
      showToast('Verification email sent.');
    } catch (err) {
      showToast(err.message || 'Could not send verification email', 'error');
    } finally {
      setSending(false);
    }
  };

  const handleContinue = async () => {
    setChecking(true);
    try {
      await firebaseUser.reload();
      await firebaseUser.getIdToken(true);
      const userData = await checkAuth();
      if (firebaseUser.emailVerified || userData?.email_verified) {
        navigate('/dashboard', { replace: true });
      } else {
        showToast('Your email is not verified yet.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Could not refresh verification status', 'error');
    } finally {
      setChecking(false);
    }
  };

  return (
    <section className="auth-container page-enter">
      <div className="glass-card auth-card">
        <div className="auth-icon-wrapper auth-icon-success" aria-hidden="true">
          <EnvelopeOpen size={30} weight="duotone" />
        </div>
        <div className="auth-header">
          <div className="auth-eyebrow">One final step</div>
          <h1>Verify your email</h1>
          <p>We sent a verification link to <strong>{firebaseUser?.email || 'your email address'}</strong>. Open it, then continue to your dashboard.</p>
        </div>
        <div className="auth-actions">
          <button type="button" className="btn-primary btn-full" onClick={handleContinue} disabled={checking}>
            {checking ? 'Checking...' : 'I verified my email'}
          </button>
          <button type="button" className="btn-secondary btn-full" onClick={handleResend} disabled={sending}>
            {sending ? 'Sending...' : 'Resend verification email'}
          </button>
        </div>
        <p className="auth-switch">
          Wrong account? <button type="button" className="link-button" onClick={logout}>Log out</button>
          {' · '}
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </section>
  );
}