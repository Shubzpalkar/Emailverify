import { Link } from 'react-router-dom';
import './Landing.css';

export default function Landing() {
  return (
    <section className="hero page-enter">
      <div className="hero-content">
        <div className="badge">🚀 Lightning Fast Engine</div>
        <h1>Clean your email lists at <span className="text-gradient">warp speed.</span></h1>
        <p className="subtitle">
          Valid, Invalid, Catch-all, or Disposable. Know exactly who you are sending to
          using our dedicated DuckDB analytics instance.
        </p>
        <div className="hero-actions">
          <Link to="/signup" className="btn-primary btn-large">Start Verifying Free</Link>
          <Link to="/login" className="btn-secondary btn-large">Learn More</Link>
        </div>
      </div>
      <div className="hero-graphic">
        <div className="glass-card mockup-card">
          <div className="mockup-header">
            <div className="dots">
              <span className="dot-red"></span>
              <span className="dot-yellow"></span>
              <span className="dot-green"></span>
            </div>
            <div className="mockup-title">verification_results.csv</div>
          </div>
          <div className="mockup-body">
            <div className="mockup-row">
              <span className="email">john@stripe.com</span>
              <span className="tag tag-valid">Valid</span>
            </div>
            <div className="mockup-row">
              <span className="email">admin@company.com</span>
              <span className="tag tag-warning">Role</span>
            </div>
            <div className="mockup-row">
              <span className="email">sdajd8@temp-mail.org</span>
              <span className="tag tag-error">Disposable</span>
            </div>
            <div className="mockup-row">
              <span className="email">bounce@fake.net</span>
              <span className="tag tag-error">Invalid</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
