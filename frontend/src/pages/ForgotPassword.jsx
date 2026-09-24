import { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../firebase/auth';
import { useToast } from '../components/Toast';
import './Auth.css';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const { showToast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await forgotPassword(email);
      showToast('Password reset email sent.');
      setSubmitted(true);
    } catch (err) {
      showToast(err.message || 'Request failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-container page-enter">
      <div className="glass-card auth-card">
        <div className="auth-eyebrow">Account recovery</div>
        <h1>Reset your password</h1>
        {submitted ? (
          <div className="success-state">
            <p>If that email is registered, you will receive a reset link shortly.</p>
            <p className="subtext">Please check your inbox and spam folder.</p>
            <Link to="/login" className="btn-primary btn-full auth-return-action">
              Return to Login
            </Link>
          </div>
        ) : (
          <>
            <p>Enter your email address and we'll send you a link to reset your password.</p>
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="input-group">
                <label htmlFor="forgot-email">Email Address</label>
                <input
                  id="forgot-email"
                  type="email"
                  autoComplete="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn-primary btn-full" disabled={loading}>
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
            <p className="auth-switch">
              Remembered your password? <Link to="/login">Log in</Link>
            </p>
          </>
        )}
      </div>
    </section>
  );
}