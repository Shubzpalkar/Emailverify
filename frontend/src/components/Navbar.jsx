import { Link, useNavigate } from 'react-router-dom';
import { EnvelopeSimpleOpen } from '@phosphor-icons/react';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      showToast('Logged out successfully');
      navigate('/');
    } catch {
      showToast('Logout failed', 'error');
    }
  };

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">
        <EnvelopeSimpleOpen size={24} weight="fill" color="var(--primary)" />
        <span>EmailVerif</span>
      </Link>
      <div className="nav-links">
        {!user ? (
          <>
            <Link to="/login" className="nav-link btn-secondary">Log in</Link>
            <Link to="/signup" className="nav-link btn-primary">Sign up</Link>
          </>
        ) : (
          <>
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/verify" className="nav-link">Verify</Link>
            {user.role === 'admin' && (
              <Link to="/admin" className="nav-link">Admin</Link>
            )}
            <button className="nav-link btn-secondary" onClick={handleLogout}>Log out</button>
          </>
        )}
      </div>
    </nav>
  );
}
