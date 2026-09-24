import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import './Auth.css';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { login, googleLogin } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const routeAfterLogin = (firebaseUser, user) => {
    if (user?.role === 'superadmin') {
      navigate('/superadmin', { replace: true });
      return;
    }
    if (!firebaseUser?.emailVerified && user?.role !== 'superadmin') {
      navigate('/verify-email', { replace: true });
      return;
    }
    navigate('/dashboard', { replace: true });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { firebaseUser, user } = await login(email, password);
      showToast('Welcome back!');
      routeAfterLogin(firebaseUser, user);
    } catch (err) {
      let msg = err.message || 'Login failed';
      if (err.code === 'auth/user-not-found' || err.code === 'auth/invalid-credential' || msg.includes('invalid-credential') || msg.includes('user-not-found')) {
        msg = 'Invalid credentials or account not found. Please check your email and password.';
      } else if (err.code === 'auth/wrong-password') {
        msg = 'Incorrect password. Please try again.';
      } else if (err.code === 'auth/too-many-requests') {
        msg = 'Access to this account has been temporarily disabled due to many failed login attempts. You can reset your password or try again later.';
      }
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      const { firebaseUser } = await googleLogin();
      showToast('Welcome back!');
      routeAfterLogin(firebaseUser);
    } catch (err) {
      showToast(err.message || 'Google sign-in failed', 'error');
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <section className="auth-container page-enter">
      <div className="glass-card auth-card">
        <div className="auth-eyebrow">Secure account access</div>
        <h1>Welcome back</h1>
        <p>Enter your details to access your dashboard.</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="input-group">
            <label htmlFor="login-email">Email Address</label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              placeholder="name@company.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="input-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="forgot-password-link">
            <Link to="/forgot-password">Forgot password?</Link>
          </div>
          <button type="submit" className="btn-primary btn-full" disabled={loading || googleLoading}>
            {loading ? 'Authenticating...' : 'Log In'}
          </button>
        </form>
        <div className="auth-divider"><span>or</span></div>
        <button type="button" className="btn-secondary btn-full" onClick={handleGoogleLogin} disabled={loading || googleLoading}>
          {googleLoading ? 'Connecting...' : 'Continue with Google'}
        </button>
        <p className="auth-switch">
          Don't have an account? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </section>
  );
}