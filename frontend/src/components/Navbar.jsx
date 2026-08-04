import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { EnvelopeSimpleOpen, List, X } from '@phosphor-icons/react';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('home');

  const sections = ['home', 'features', 'how-it-works', 'pricing-preview', 'api-section', 'security', 'testimonials', 'faq'];

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);

      // Scrollspy logic
      if (location.pathname === '/') {
        const scrollPosition = window.scrollY + 100; // offset for nav height
        
        // Check if we are near the bottom of the page
        if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 50) {
          setActiveSection('faq');
          return;
        }

        for (const sectionId of sections) {
          const el = document.getElementById(sectionId);
          if (el) {
            const top = el.offsetTop;
            const height = el.offsetHeight;
            if (scrollPosition >= top && scrollPosition < top + height) {
              setActiveSection(sectionId);
              break;
            }
          }
        }
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await logout();
      showToast('Logged out successfully');
      setMobileMenuOpen(false);
      navigate('/');
    } catch {
      showToast('Logout failed', 'error');
    }
  };

  const handleSectionClick = (e, sectionId) => {
    setMobileMenuOpen(false);
    if (location.pathname === '/') {
      e.preventDefault();
      const element = document.getElementById(sectionId);
      if (element) {
        const offset = 80;
        const bodyRect = document.body.getBoundingClientRect().top;
        const elementRect = element.getBoundingClientRect().top;
        const elementPosition = elementRect - bodyRect;
        const offsetPosition = elementPosition - offset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
        setActiveSection(sectionId);
      }
    }
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const isPublicPage = location.pathname === '/' || location.pathname === '/pricing';

  return (
    <nav className={`navbar ${scrolled ? 'navbar-scrolled' : ''} ${mobileMenuOpen ? 'navbar-open' : ''}`} aria-label="Main Navigation">
      <div className="nav-container">
        <Link to="/" className="nav-brand" aria-label="EmailVerif Home">
          <EnvelopeSimpleOpen size={28} weight="fill" color="var(--primary)" />
          <span>EmailVerif</span>
        </Link>

        {isPublicPage && (
          <div className="navbar-center" role="navigation">
            <Link 
              to="/#home" 
              onClick={(e) => handleSectionClick(e, 'home')} 
              className={`nav-link ${location.pathname === '/' && activeSection === 'home' ? 'active' : ''}`}
            >
              Home
            </Link>
            <Link 
              to="/#features" 
              onClick={(e) => handleSectionClick(e, 'features')} 
              className={`nav-link ${location.pathname === '/' && activeSection === 'features' ? 'active' : ''}`}
            >
              Features
            </Link>
            <Link 
              to="/#how-it-works" 
              onClick={(e) => handleSectionClick(e, 'how-it-works')} 
              className={`nav-link ${location.pathname === '/' && activeSection === 'how-it-works' ? 'active' : ''}`}
            >
              How It Works
            </Link>
            <Link 
              to="/pricing" 
              className={`nav-link ${location.pathname === '/pricing' ? 'active' : ''}`}
            >
              Pricing
            </Link>
            <Link 
              to="/#api-section" 
              onClick={(e) => handleSectionClick(e, 'api-section')} 
              className={`nav-link ${location.pathname === '/' && activeSection === 'api-section' ? 'active' : ''}`}
            >
              API
            </Link>
            <Link 
              to="/#api-section" 
              onClick={(e) => handleSectionClick(e, 'api-section')} 
              className={`nav-link ${location.pathname === '/' && activeSection === 'api-section' ? 'active' : ''}`}
            >
              Documentation
            </Link>
            <Link 
              to="/#faq" 
              onClick={(e) => handleSectionClick(e, 'faq')} 
              className={`nav-link ${location.pathname === '/' && activeSection === 'faq' ? 'active' : ''}`}
            >
              FAQ
            </Link>
          </div>
        )}

        <div className="nav-links">
          {isPublicPage ? (
            user ? (
              <>
                <Link to="/dashboard" className="btn-primary btn-small">Dashboard</Link>
                <button className="btn-secondary btn-small" onClick={handleLogout}>Log out</button>
              </>
            ) : (
              <>
                <Link to="/login" className="nav-link">Log in</Link>
                <Link to="/signup" className="btn-primary btn-small">Start Free</Link>
              </>
            )
          ) : (
            user && (
              <>
                <Link to="/dashboard" className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}>Dashboard</Link>
                <Link to="/verify" className={`nav-link ${location.pathname === '/verify' ? 'active' : ''}`}>Verify</Link>
                <Link to="/history" className={`nav-link ${location.pathname === '/history' ? 'active' : ''}`}>History</Link>
                <Link to="/analytics" className={`nav-link ${location.pathname === '/analytics' ? 'active' : ''}`}>Analytics</Link>
                <Link to="/billing" className={`nav-link ${location.pathname.startsWith('/billing') || location.pathname === '/subscription' || location.pathname === '/invoices' || location.pathname === '/payment-history' || location.pathname === '/credits' ? 'active' : ''}`}>Billing</Link>
                <Link to="/settings/keys" className={`nav-link ${location.pathname.startsWith('/settings') ? 'active' : ''}`}>API Keys</Link>
                <Link to="/account/profile" className={`nav-link ${location.pathname.startsWith('/account') ? 'active' : ''}`}>Profile</Link>
                {user.role === 'superadmin' && (
                  <Link to="/superadmin" className="nav-link">Superadmin</Link>
                )}
                {(user.role === 'admin' || user.role === 'superadmin') && (
                  <Link to="/admin" className="nav-link">Admin Panel</Link>
                )}
                <button className="btn-secondary btn-small" onClick={handleLogout}>Log out</button>
              </>
            )
          )}
        </div>

        {/* Mobile Hamburger Toggle */}
        {isPublicPage && (
          <button 
            className="mobile-nav-toggle" 
            onClick={toggleMobileMenu} 
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X size={26} /> : <List size={26} />}
          </button>
        )}
      </div>

      {/* Mobile Drawer Menu */}
      {isPublicPage && mobileMenuOpen && (
        <div className="mobile-drawer-menu" role="dialog" aria-modal="true" aria-label="Mobile Navigation Menu">
          <div className="mobile-drawer-links">
            <Link to="/#home" onClick={(e) => handleSectionClick(e, 'home')} className="mobile-nav-link">Home</Link>
            <Link to="/#features" onClick={(e) => handleSectionClick(e, 'features')} className="mobile-nav-link">Features</Link>
            <Link to="/#how-it-works" onClick={(e) => handleSectionClick(e, 'how-it-works')} className="mobile-nav-link">How It Works</Link>
            <Link to="/pricing" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">Pricing</Link>
            <Link to="/#api-section" onClick={(e) => handleSectionClick(e, 'api-section')} className="mobile-nav-link">API</Link>
            <Link to="/#api-section" onClick={(e) => handleSectionClick(e, 'api-section')} className="mobile-nav-link">Documentation</Link>
            <Link to="/#faq" onClick={(e) => handleSectionClick(e, 'faq')} className="mobile-nav-link">FAQ</Link>
            <div className="mobile-drawer-auth">
              {user ? (
                <>
                  <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)} className="btn-primary btn-full">Dashboard</Link>
                  <button className="btn-secondary btn-full" onClick={handleLogout}>Log out</button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link text-center" style={{ margin: '1rem 0' }}>Log in</Link>
                  <Link to="/signup" onClick={() => setMobileMenuOpen(false)} className="btn-primary btn-full">Start Free</Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
