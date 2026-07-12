import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Eye, EyeSlash, Check, X } from '@phosphor-icons/react';
import { resetPassword } from '../firebase/auth';
import { useToast } from '../components/Toast';
import './Auth.css';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [oobCode, setOobCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { showToast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    const code = searchParams.get('oobCode') || searchParams.get('token');
    if (!code) {
      showToast('Invalid or missing reset code', 'error');
      navigate('/login');
    } else {
      setOobCode(code);
    }
  }, [searchParams, navigate, showToast]);

  const requirements = {
    minChar: newPassword.length >= 8,
    uppercase: /[A-Z]/.test(newPassword),
    lowercase: /[a-z]/.test(newPassword),
    number: /[0-9]/.test(newPassword),
    specialChar: /[^A-Za-z0-9]/.test(newPassword)
  };

  const isAllMet = Object.values(requirements).every(Boolean);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      return showToast('Passwords do not match', 'error');
    }
    if (!isAllMet) {
      return showToast('Password does not meet all security requirements', 'error');
    }

    setLoading(true);
    try {
      await resetPassword(oobCode, newPassword);
      showToast('Password reset successfully');
      navigate('/login');
    } catch (err) {
      showToast(err.message || 'Reset failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-container page-enter">
      <div className="glass-card auth-card">
        <h2>Set new password</h2>
        <p className="auth-subtitle">Enter your new password below to complete the reset.</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="input-group">
            <label htmlFor="reset-new-password">New Password</label>
            <div className="password-input-wrapper" style={{ position: 'relative' }}>
              <input
                id="reset-new-password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
                style={{ paddingRight: '2.5rem' }}
              />
              <button
                type="button"
                className="btn-icon password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                {showPassword ? <EyeSlash size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="reset-confirm-password">Confirm Password</label>
            <input
              id="reset-confirm-password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <div className="password-requirements" style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
              Password Requirements:
            </span>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: requirements.minChar ? 'var(--success)' : 'var(--text-muted)' }}>
                {requirements.minChar ? <Check size={14} weight="bold" /> : <X size={14} weight="bold" color="var(--error)" />}
                <span>Minimum 8 Characters</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: requirements.uppercase ? 'var(--success)' : 'var(--text-muted)' }}>
                {requirements.uppercase ? <Check size={14} weight="bold" /> : <X size={14} weight="bold" color="var(--error)" />}
                <span>At least 1 Uppercase Letter</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: requirements.lowercase ? 'var(--success)' : 'var(--text-muted)' }}>
                {requirements.lowercase ? <Check size={14} weight="bold" /> : <X size={14} weight="bold" color="var(--error)" />}
                <span>At least 1 Lowercase Letter</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: requirements.number ? 'var(--success)' : 'var(--text-muted)' }}>
                {requirements.number ? <Check size={14} weight="bold" /> : <X size={14} weight="bold" color="var(--error)" />}
                <span>At least 1 Number</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: requirements.specialChar ? 'var(--success)' : 'var(--text-muted)' }}>
                {requirements.specialChar ? <Check size={14} weight="bold" /> : <X size={14} weight="bold" color="var(--error)" />}
                <span>At least 1 Special Character</span>
              </li>
            </ul>
          </div>

          <button type="submit" className="btn-primary btn-full" disabled={loading || !isAllMet}>
            {loading ? 'Updating...' : 'Reset Password'}
          </button>
        </form>
        <p className="auth-switch">
          Nevermind, I remembered! <Link to="/login">Back to Login</Link>
        </p>
      </div>
    </section>
  );
}
