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
    specialChar: /[^A-Za-z0-9]/.test(newPassword),
  };

  const isAllMet = Object.values(requirements).every(Boolean);

  const handleSubmit = async (event) => {
    event.preventDefault();
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

  const requirementItems = [
    ['minChar', 'Minimum 8 characters'],
    ['uppercase', 'At least 1 uppercase letter'],
    ['lowercase', 'At least 1 lowercase letter'],
    ['number', 'At least 1 number'],
    ['specialChar', 'At least 1 special character'],
  ];

  return (
    <section className="auth-container page-enter">
      <div className="glass-card auth-card">
        <div className="auth-eyebrow">Secure your account</div>
        <h1>Set a new password</h1>
        <p className="auth-subtitle">Choose a strong password you have not used elsewhere.</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="input-group">
            <label htmlFor="reset-new-password">New password</label>
            <div className="password-input-wrapper">
              <input
                id="reset-new-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="Enter your new password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                required
              />
              <button
                type="button"
                className="btn-icon password-toggle"
                onClick={() => setShowPassword((visible) => !visible)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeSlash size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="reset-confirm-password">Confirm password</label>
            <input
              id="reset-confirm-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Repeat your new password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
            />
          </div>

          <div className="password-requirements" aria-label="Password requirements">
            <span className="password-requirements-title">Password requirements</span>
            <ul>
              {requirementItems.map(([key, label]) => (
                <li key={key} className={requirements[key] ? 'met' : ''}>
                  {requirements[key]
                    ? <Check size={14} weight="bold" />
                    : <X size={14} weight="bold" />}
                  <span>{label}</span>
                </li>
              ))}
            </ul>
          </div>

          <button type="submit" className="btn-primary btn-full" disabled={loading || !isAllMet}>
            {loading ? 'Updating...' : 'Reset password'}
          </button>
        </form>
        <p className="auth-switch">
          Remembered your password? <Link to="/login">Back to login</Link>
        </p>
      </div>
    </section>
  );
}
