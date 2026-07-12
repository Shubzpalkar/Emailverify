import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import './Auth.css';

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { signup, googleLogin } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await signup(email, password);
      showToast('Account created. Please verify your email.');
      navigate('/verify-email', { replace: true });
    } catch (err) {
      showToast(err.message || 'Signup failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setGoogleLoading(true);
    try {
      await googleLogin();
      showToast('Account ready.');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      showToast(err.message || 'Google sign-in failed', 'error');
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <section className="auth-container page-enter">
      <div className="glass-card auth-card">
        <h2>Create an account</h2>
        <p>Get 100 free credits to start verifying.</p>
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="signup-email">Email Address</label>
            <input
              id="signup-email"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="input-group">
            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              type="password"
              placeholder="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <button type="submit" className="btn-primary btn-full" disabled={loading || googleLoading}>
            {loading ? 'Processing...' : 'Sign Up'}
          </button>
        </form>
        <div className="auth-divider"><span>or</span></div>
        <button type="button" className="btn-secondary btn-full" onClick={handleGoogleSignup} disabled={loading || googleLoading}>
          {googleLoading ? 'Connecting...' : 'Continue with Google'}
        </button>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </section>
  );
}