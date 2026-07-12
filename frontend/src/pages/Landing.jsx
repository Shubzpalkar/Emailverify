import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Check, 
  ShieldCheck, 
  Cpu, 
  Users, 
  Warning, 
  FileCsv, 
  Download, 
  ArrowRight,
  DotsThreeCircle,
  Code,
  Globe,
  XCircle,
  CheckCircle,
  Star,
  Clock
} from '@phosphor-icons/react';
import './Landing.css';

export default function Landing() {
  const location = useLocation();
  const [demoEmail, setDemoEmail] = useState('');
  const [demoState, setDemoState] = useState('idle'); // idle, checking, success
  const [demoStep, setDemoStep] = useState(0);
  const [demoResult, setDemoResult] = useState(null);
  const [activeFaq, setActiveFaq] = useState(null);
  const [apiTab, setApiTab] = useState('request'); // request, response

  // Scroll to hash section if present in URL
  useEffect(() => {
    if (location.hash) {
      const id = location.hash.substring(1);
      const element = document.getElementById(id);
      if (element) {
        setTimeout(() => {
          const offset = 80;
          const bodyRect = document.body.getBoundingClientRect().top;
          const elementRect = element.getBoundingClientRect().top;
          const elementPosition = elementRect - bodyRect;
          const offsetPosition = elementPosition - offset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }, 100);
      }
    }
  }, [location]);

  // Viewport Scroll Animations hook
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animated');
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach((el) => observer.observe(el));

    return () => {
      animatedElements.forEach((el) => observer.unobserve(el));
    };
  }, []);

  const demoSteps = [
    { title: 'Syntax Check', desc: 'Validating format RFC compliance' },
    { title: 'Domain Verification', desc: 'Checking domain name server syntax' },
    { title: 'DNS Lookup', desc: 'Checking active record details' },
    { title: 'MX Record Check', desc: 'Resolving destination exchange servers' },
    { title: 'SMTP Verification', desc: 'Establishing remote mail socket connection' },
    { title: 'Risk Assessment', desc: 'Evaluating temporary and disposable domains' },
    { title: 'Aggregating Results', desc: 'Structuring final analysis scores' }
  ];

  const handleDemoVerify = (e) => {
    e.preventDefault();
    if (!demoEmail || !demoEmail.includes('@')) {
      alert('Please enter a valid email address.');
      return;
    }

    setDemoState('checking');
    setDemoStep(0);

    const duration = 400; // 400ms per verification step
    let stepCount = 0;

    const stepInterval = setInterval(() => {
      stepCount++;
      if (stepCount < demoSteps.length) {
        setDemoStep(stepCount);
      } else {
        clearInterval(stepInterval);
        const domain = demoEmail.split('@')[1].toLowerCase();
        let status = 'valid';
        let isRole = false;
        let isDisposable = false;
        let smtpResult = '250 Mailbox exists';
        let syntaxCheck = 'Passed';
        let domainExists = 'Passed';
        let mxRecord = 'Found (1 MX record)';
        let smtpVerification = 'Passed';
        let catchAll = 'No';
        let confidenceScore = '99%';
        let verificationTime = `${Math.floor(Math.random() * 80) + 120}ms`;
        let smtpResponseCode = '250';
        let riskLevel = 'Safe';

        if (domain.includes('temp') || domain.includes('mailinator')) {
          status = 'disposable';
          isDisposable = true;
          smtpResult = '550 Disposable email address';
          smtpVerification = 'Failed';
          confidenceScore = '12%';
          riskLevel = 'High Risk';
          smtpResponseCode = '550';
        } else if (demoEmail.startsWith('admin@') || demoEmail.startsWith('support@') || demoEmail.startsWith('info@')) {
          status = 'catch_all';
          isRole = true;
          catchAll = 'Yes';
          smtpResult = '250 Role address / Catch-all active';
          confidenceScore = '68%';
          riskLevel = 'Medium Risk';
        } else if (domain === 'invalid.com' || demoEmail.includes('bounce')) {
          status = 'invalid';
          smtpResult = '550 Requested action not taken: mailbox unavailable';
          smtpVerification = 'Failed';
          domainExists = 'Failed';
          mxRecord = 'Not Found';
          confidenceScore = '0%';
          riskLevel = 'High Risk';
          smtpResponseCode = '550';
        }

        setDemoResult({
          email: demoEmail,
          domain,
          status,
          isRole: isRole ? 'Yes' : 'No',
          isDisposable: isDisposable ? 'Yes' : 'No',
          smtpResult,
          syntaxCheck,
          domainExists,
          mxRecord,
          smtpVerification,
          catchAll,
          confidenceScore,
          verificationTime,
          smtpResponseCode,
          riskLevel,
          verifiedAt: new Date().toLocaleTimeString()
        });
        setDemoState('success');
      }
    }, duration);
  };

  const resetDemo = () => {
    setDemoEmail('');
    setDemoState('idle');
    setDemoResult(null);
  };

  const toggleFaq = (index) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  const features = [
    {
      title: 'SMTP Verification',
      desc: 'Real-time mailbox check verifying active mailboxes without sending an email.',
      icon: <Globe size={24} color="var(--primary)" />
    },
    {
      title: 'Catch-All Detection',
      desc: 'Identify domains set to accept all incoming mail, preventing soft-bounce loops.',
      icon: <DotsThreeCircle size={24} color="var(--primary)" />
    },
    {
      title: 'Disposable Detection',
      desc: 'Instantly isolate burner addresses from temp-mail generators and bot signups.',
      icon: <Warning size={24} color="var(--primary)" />
    },
    {
      title: 'Role Account Detection',
      desc: 'Tag generic accounts like info@, billing@, or admin@ that dilute engagement.',
      icon: <Users size={24} color="var(--primary)" />
    },
    {
      title: 'Bulk Verification',
      desc: 'Upload CSV lists containing millions of addresses and verify at lightning speed.',
      icon: <FileCsv size={24} color="var(--primary)" />
    },
    {
      title: 'API Access',
      desc: 'Clean REST endpoints for real-time validation directly in your web forms.',
      icon: <Code size={24} color="var(--primary)" />
    }
  ];

  const testimonials = [
    { review: 'EmailVerif has reduced our client campaign bounce rates from 14% to below 0.5% in the first week. Deliverability has skyrocketed!', name: 'Sarah Jenkins', role: 'Head of Growth, ScaleUp Agency', rating: 5, company: 'ScaleUp Agency', industry: 'Lead Generation' },
    { review: 'The Developer API is incredibly fast. Real-time form checks at registration completely stopped dummy signups for our SaaS.', name: 'Marcus Chen', role: 'CTO, DevSuite Platforms', rating: 5, company: 'DevSuite Platforms', industry: 'SaaS Software' },
    { review: 'Our outreach team can send 50k emails daily without blacklisting fear. The SMTP validation details are the cleanest we have seen.', name: 'Elena Rostova', role: 'Sales Director, OutboundLabs', rating: 5, company: 'OutboundLabs', industry: 'B2B Sales Outreach' }
  ];

  const pricingPreview = [
    { name: 'Free', price: '₹0', credits: '100 Credits', uploadLimit: '1,000 rows', api: 'No API Access', support: 'Community Support', speed: 'Normal Speed', link: '/signup', popular: false },
    { name: 'Starter', price: '₹999', credits: '50,000 Credits', uploadLimit: '100,000 rows', api: 'No API Access', support: 'Email Support', speed: 'High Speed', link: '/signup', popular: false },
    { name: 'Growth', price: '₹4,999', credits: '500,000 Credits', uploadLimit: '1,000,000 rows', api: 'Full API Access', support: 'Priority Support', speed: 'Turbo Speed', link: '/signup', popular: true },
    { name: 'Enterprise', price: 'Custom', credits: 'Unlimited Scale', uploadLimit: 'Unlimited rows', api: 'Full API Access', support: 'Dedicated SLA', speed: 'Custom Priority', link: 'mailto:sales@emailverif.com', popular: false }
  ];

  return (
    <div className="landing-page">
      {/* 1. HERO SECTION */}
      <section id="home" className="hero-section page-enter">
        <div className="hero-container container">
          <div className="hero-content">
            <span className="badge">🚀 Real-Time SMTP Validation</span>
            <h1>Verify Emails <span className="text-gradient">Before You Send</span></h1>
            <p className="subtitle">
              Reduce bounce rates, improve email deliverability, and clean your email lists using real-time SMTP verification.
            </p>
            <div className="hero-actions">
              <Link to="/signup" className="btn-primary btn-large" aria-label="Start Free Trial">Start Free</Link>
              <Link to="/pricing" className="btn-secondary btn-large" aria-label="View Product Pricing">View Pricing</Link>
            </div>

            {/* TRUST BADGES */}
            <div className="trust-badges-row">
              <span className="badge-item"><Check size={16} color="var(--success)" weight="bold" /> No Credit Card Required</span>
              <span className="badge-item"><Check size={16} color="var(--success)" weight="bold" /> 100 Free Credits</span>
              <span className="badge-item"><Check size={16} color="var(--success)" weight="bold" /> Secure Payments</span>
              <span className="badge-item"><Check size={16} color="var(--success)" weight="bold" /> Fast Setup</span>
            </div>
            
            <div className="hero-stats-grid">
              <div className="hero-stat-item">
                <h3>99%</h3>
                <p>Accuracy</p>
              </div>
              <div className="hero-stat-item">
                <h3>5,000</h3>
                <p>Emails / Min</p>
              </div>
              <div className="hero-stat-item">
                <h3>Real-Time</h3>
                <p>Verification</p>
              </div>
              <div className="hero-stat-item">
                <h3>Enterprise</h3>
                <p>Ready</p>
              </div>
            </div>
          </div>
          
          <div className="hero-graphic">
            <div className="glass-card mockup-dashboard">
              <div className="mockup-header">
                <div className="dots">
                  <span className="dot-red"></span>
                  <span className="dot-yellow"></span>
                  <span className="dot-green"></span>
                </div>
                <div className="mockup-title">Dashboard Live Activity</div>
              </div>
              <div className="mockup-body">
                <div className="dashboard-stats">
                  <div className="d-stat">
                    <span>Total Jobs</span>
                    <strong>12,492</strong>
                  </div>
                  <div className="d-stat">
                    <span>Avg Accuracy</span>
                    <strong style={{ color: 'var(--success)' }}>99.82%</strong>
                  </div>
                  <div className="d-stat">
                    <span>Credits Left</span>
                    <strong>45,210</strong>
                  </div>
                </div>
                <div className="mockup-logs">
                  <div className="log-row">
                    <span className="log-time">17:19:01</span>
                    <span className="log-msg">Uploaded <strong>list_marketing_q2.csv</strong></span>
                  </div>
                  <div className="log-row">
                    <span className="log-time">17:19:12</span>
                    <span className="log-msg">Job #4312 started. Processing 5,420 records...</span>
                  </div>
                  <div className="log-row">
                    <span className="log-time">17:19:25</span>
                    <span className="log-msg" style={{ color: 'var(--success)' }}>Job complete! 98.4% deliverable rate.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. TRUSTED BY SECTION */}
      <section className="trusted-by-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Social Proof</span>
          <h2>Trusted by Industry Leaders</h2>
        </div>
        <div className="logo-cloud">
          <div className="logo-item">Stripe</div>
          <div className="logo-item">Vercel</div>
          <div className="logo-item">Clerk</div>
          <div className="logo-item">Linear</div>
          <div className="logo-item">Notion</div>
          <div className="logo-item">Resend</div>
        </div>
      </section>

      {/* 3. STATISTICS SECTION */}
      <section className="stats-section container animate-on-scroll">
        <div className="stats-grid">
          <div className="stat-item">
            <h3>12.4M+</h3>
            <p>Emails Verified</p>
          </div>
          <div className="stat-item">
            <h3>8,000+</h3>
            <p>Active Customers</p>
          </div>
          <div className="stat-item">
            <h3>99.9%</h3>
            <p>Verification Accuracy</p>
          </div>
          <div className="stat-item">
            <h3>120+</h3>
            <p>Countries Served</p>
          </div>
        </div>
      </section>

      {/* 5. WHY CHOOSE US */}
      <section id="features" className="features-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Why Choose Us</span>
          <h2>Clean lists with <span className="text-gradient">precision checks</span></h2>
          <p>Everything you need to automate email cleaning and maximize campaign delivery.</p>
        </div>
        <div className="features-grid">
          {features.map((feat, idx) => (
            <div key={idx} className="feature-card glass-card">
              <div className="feat-icon-box">{feat.icon}</div>
              <h3>{feat.title}</h3>
              <p>{feat.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 6. INTERACTIVE EMAIL VERIFICATION DEMO */}
      <section className="demo-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Try it out</span>
          <h2>Live Validation Demo</h2>
          <p>Inspect any email address and witness the real-time diagnostic pipeline.</p>
        </div>
        <div className="glass-card demo-wrapper">
          {demoState === 'idle' && (
            <form onSubmit={handleDemoVerify} className="demo-form">
              <input 
                type="email" 
                placeholder="enter-any-email@domain.com"
                value={demoEmail}
                onChange={e => setDemoEmail(e.target.value)}
                required
                aria-label="Email to verify"
              />
              <button type="submit" className="btn-primary">Verify Address</button>
            </form>
          )}

          {demoState === 'checking' && (
            <div className="demo-loading">
              <div className="spinner"></div>
              <p className="loading-step">Current Step: <strong>{demoSteps[demoStep].title}</strong></p>
              <span className="step-desc">{demoSteps[demoStep].desc}</span>
              
              {/* Animated Verification Flow */}
              <div className="verification-flow-steps">
                {demoSteps.map((step, idx) => (
                  <div key={idx} className={`flow-step-dot ${idx <= demoStep ? 'active' : ''} ${idx === demoStep ? 'pulse' : ''}`}>
                    <span className="step-number">{idx + 1}</span>
                    <span className="step-label">{step.title}</span>
                  </div>
                ))}
              </div>
              <div className="progress-bar">
                <div className="progress" style={{ width: `${((demoStep + 1) / demoSteps.length) * 100}%` }}></div>
              </div>
            </div>
          )}

          {demoState === 'success' && demoResult && (
            <div className="demo-success">
              <div className="success-header">
                <h4>Result for: <span className="text-gradient">{demoResult.email}</span></h4>
                <button className="btn-secondary btn-small" onClick={resetDemo}>Check Another</button>
              </div>

              {/* Enhanced 12 result cards */}
              <div className="premium-results-layout">
                <div className="result-category-block">
                  <h5>Diagnostics Summary</h5>
                  <div className="demo-results-grid">
                    <div className="res-row">
                      <span>Email Target</span>
                      <strong>{demoResult.email}</strong>
                    </div>
                    <div className="res-row">
                      <span>Domain Name</span>
                      <strong>{demoResult.domain}</strong>
                    </div>
                    <div className="res-row">
                      <span>Risk Profile</span>
                      <span className={`risk-tag risk-${demoResult.riskLevel.toLowerCase().replace(' ', '-')}`}>
                        {demoResult.riskLevel}
                      </span>
                    </div>
                    <div className="res-row">
                      <span>Confidence Score</span>
                      <strong style={{ color: demoResult.status === 'valid' ? 'var(--success)' : 'var(--warning)' }}>
                        {demoResult.confidenceScore}
                      </strong>
                    </div>
                    <div className="res-row">
                      <span>SMTP Diagnostics</span>
                      <span className="smtp-code">{demoResult.smtpResult}</span>
                    </div>
                  </div>
                </div>

                <div className="result-category-block">
                  <h5>Technical Verification Steps</h5>
                  <div className="demo-results-grid">
                    <div className="res-row">
                      <span>Syntax Check</span>
                      <span className="step-status"><CheckCircle size={16} color="var(--success)" weight="fill" /> {demoResult.syntaxCheck}</span>
                    </div>
                    <div className="res-row">
                      <span>Domain Check</span>
                      <span className="step-status">
                        {demoResult.domainExists === 'Passed' ? 
                          <CheckCircle size={16} color="var(--success)" weight="fill" /> : 
                          <XCircle size={16} color="var(--error)" weight="fill" />
                        } 
                        {demoResult.domainExists}
                      </span>
                    </div>
                    <div className="res-row">
                      <span>MX Configuration</span>
                      <span className="step-status">
                        {demoResult.mxRecord !== 'Not Found' ? 
                          <CheckCircle size={16} color="var(--success)" weight="fill" /> : 
                          <XCircle size={16} color="var(--error)" weight="fill" />
                        } 
                        {demoResult.mxRecord}
                      </span>
                    </div>
                    <div className="res-row">
                      <span>SMTP Handshake</span>
                      <span className="step-status">
                        {demoResult.smtpVerification === 'Passed' ? 
                          <CheckCircle size={16} color="var(--success)" weight="fill" /> : 
                          <XCircle size={16} color="var(--error)" weight="fill" />
                        } 
                        {demoResult.smtpVerification}
                      </span>
                    </div>
                    <div className="res-row">
                      <span>SMTP Code</span>
                      <strong className="code-accent">{demoResult.smtpResponseCode}</strong>
                    </div>
                    <div className="res-row">
                      <span>Catch-All Check</span>
                      <strong>{demoResult.catchAll}</strong>
                    </div>
                    <div className="res-row">
                      <span>Disposable Address</span>
                      <strong>{demoResult.isDisposable}</strong>
                    </div>
                    <div className="res-row">
                      <span>Role-Based Address</span>
                      <strong>{demoResult.isRole}</strong>
                    </div>
                    <div className="res-row">
                      <span>Response Latency</span>
                      <span className="latency-val"><Clock size={14} /> {demoResult.verificationTime}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* 7. DASHBOARD PREVIEW */}
      <section className="dashboard-preview-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Powerful Analytics</span>
          <h2>Enterprise Dashboard Overview</h2>
          <p>Track your outreach health, list status breakdown, API credits, and job progress in real-time.</p>
        </div>
        <div className="dashboard-preview-container glass-card">
          <div className="mockup-header">
            <div className="dots">
              <span className="dot-red"></span>
              <span className="dot-yellow"></span>
              <span className="dot-green"></span>
            </div>
            <div className="mockup-title">https://app.emailverif.com/dashboard</div>
          </div>
          <div className="mockup-body dashboard-preview-layout">
            <div className="dashboard-sidebar">
              <div className="sidebar-logo">
                <ShieldCheck size={20} color="var(--primary)" weight="fill" /> 
                <span>EmailVerif</span>
              </div>
              <div className="sidebar-links">
                <span className="active-link">Overview</span>
                <span>List Verifications</span>
                <span>API Keys</span>
                <span>Billing</span>
                <span>Profile Settings</span>
              </div>
            </div>
            <div className="dashboard-main">
              <div className="main-header">
                <h3>Welcome back, Admin</h3>
                <span className="plan-pill">Growth Plan</span>
              </div>
              <div className="preview-metrics-row">
                <div className="preview-metric-box">
                  <span>Emails Checked</span>
                  <strong>2,548,210</strong>
                </div>
                <div className="preview-metric-box">
                  <span>Verification Accuracy</span>
                  <strong style={{ color: 'var(--success)' }}>99.98%</strong>
                </div>
                <div className="preview-metric-box">
                  <span>API Credits Remaining</span>
                  <strong>485,210</strong>
                </div>
              </div>
              <div className="preview-chart-mockup">
                <div className="chart-header">
                  <span>Outbound Deliverability History</span>
                  <span className="text-muted">Last 30 Days</span>
                </div>
                <div className="chart-bars">
                  <div className="chart-bar" style={{ height: '70%' }}><span className="bar-tooltip">98.2%</span></div>
                  <div className="chart-bar" style={{ height: '85%' }}><span className="bar-tooltip">99.1%</span></div>
                  <div className="chart-bar" style={{ height: '90%' }}><span className="bar-tooltip">99.5%</span></div>
                  <div className="chart-bar" style={{ height: '95%' }}><span className="bar-tooltip">99.8%</span></div>
                  <div className="chart-bar" style={{ height: '98%' }}><span className="bar-tooltip">99.9%</span></div>
                  <div className="chart-bar" style={{ height: '100%' }}><span className="bar-tooltip">99.9%</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 8. HOW IT WORKS */}
      <section id="how-it-works" className="how-it-works container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Process</span>
          <h2>How It <span className="text-gradient">Works</span></h2>
          <p>Get clean results in three simple, automated steps.</p>
        </div>
        <div className="timeline">
          <div className="timeline-item">
            <div className="timeline-icon">
              <FileCsv size={28} color="white" />
            </div>
            <div className="timeline-content">
              <h3>Step 1: Upload CSV</h3>
              <p>Drag and drop your spreadsheet or list file (.csv) containing the email column into the dashboard panel. Our engine automatically parses and detects your fields.</p>
            </div>
          </div>
          <div className="timeline-item">
            <div className="timeline-icon">
              <Cpu size={28} color="white" />
            </div>
            <div className="timeline-content">
              <h3>Step 2: Verify Emails</h3>
              <p>Our multi-threaded verification scheduler connects to remote MX servers, classifying every address with full SMTP diagnostics without sending a single spam message.</p>
            </div>
          </div>
          <div className="timeline-item">
            <div className="timeline-icon">
              <Download size={28} color="white" />
            </div>
            <div className="timeline-content">
              <h3>Step 3: Download Results</h3>
              <p>Export a clean spreadsheet categorizing all Valid, Invalid, Role-based, and Disposable addresses. Upload and start sending with bounce-free confidence.</p>
            </div>
          </div>
        </div>
      </section>

      {/* 9. PRICING */}
      <section id="pricing" className="pricing-preview-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Plans Overview</span>
          <h2>Simple, scalable <span className="text-gradient">pricing plans</span></h2>
          <p>Get started with free credits and upgrade as you grow.</p>
        </div>
        <div className="pricing-preview-grid">
          {pricingPreview.map((plan, idx) => (
            <div key={idx} className={`preview-card glass-card ${plan.popular ? 'featured-preview' : ''}`}>
              {plan.popular && <span className="preview-popular-tag">Best Value</span>}
              <h4>{plan.name}</h4>
              <h3>{plan.price}</h3>
              <p className="preview-credits">{plan.credits}</p>
              
              <div className="pricing-features-preview-list">
                <span>Upload size: {plan.uploadLimit}</span>
                <span>{plan.api}</span>
                <span>{plan.support}</span>
                <span>Speed: {plan.speed}</span>
              </div>
              
              <div style={{ marginTop: '1.5rem' }}>
                <Link to={plan.link} className={`btn-full ${plan.popular ? 'btn-primary' : 'btn-secondary'}`} aria-label={`Choose plan ${plan.name}`}>
                  Upgrade Plan
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 10. TESTIMONIALS */}
      <section id="testimonials" className="testimonials-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Reviews</span>
          <h2>Trusted by Marketing Experts</h2>
          <p>What our early adopters have to say about the deliverability boost.</p>
        </div>
        <div className="testimonials-grid">
          {testimonials.map((t, idx) => (
            <div key={idx} className="testimonial-card glass-card">
              <div className="stars-row">
                {[...Array(t.rating)].map((_, i) => (
                  <Star key={i} size={16} color="#fbbf24" weight="fill" />
                ))}
              </div>
              <p className="testimonial-text">"{t.review}"</p>
              <div className="testimonial-author">
                <strong>{t.name}</strong>
                <span>{t.role} | {t.industry}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 11. FAQ ACCORDION */}
      <section id="faq" className="faq-section container animate-on-scroll">
        <div className="faq-header text-center">
          <span className="badge">Got Questions?</span>
          <h2>FAQ Accordion</h2>
          <p>Answers to common queries regarding security, accuracy, and credits.</p>
        </div>
        <div className="faq-list">
          {[
            {
              q: 'How accurate is verification?',
              a: 'Our verification engine achieves over 99% accuracy by performing multi-step verification including MX record validation, syntax checks, and real-time SMTP connection tests.'
            },
            {
              q: 'How does SMTP verification work?',
              a: 'We connect directly to the recipient mail server and initiate an SMTP conversation without sending an actual email. This tells us whether the mailbox exists and can accept mail.'
            },
            {
              q: 'Do credits expire?',
              a: 'Free credits are provided once upon signup. Paid plan credits roll over for 12 months as long as your subscription is active, so you never lose what you bought.'
            },
            {
              q: 'Is API available?',
              a: 'Yes, API access is available starting from the Growth plan. We provide clean RESTful endpoints and generate secure API keys in the settings panel.'
            },
            {
              q: 'Is my data secure?',
              a: 'Absolutely. We do not store your verified email lists after processing. All lists are stored in a transient DuckDB database instance and automatically purged after download.'
            }
          ].map((faq, idx) => (
            <div key={idx} className="faq-item glass-card">
              <button className="faq-question" onClick={() => toggleFaq(idx)} aria-expanded={activeFaq === idx} aria-controls={`faq-answer-${idx}`}>
                <span>{faq.q}</span>
                <span className={`faq-icon ${activeFaq === idx ? 'open' : ''}`}>+</span>
              </button>
              <div id={`faq-answer-${idx}`} className={`faq-answer ${activeFaq === idx ? 'show' : ''}`} role="region">
                <p>{faq.a}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 12. FINAL CTA */}
      <section className="final-cta-section container animate-on-scroll">
        <div className="glass-card cta-wrapper">
          <h2>Start Verifying Emails Today</h2>
          <p>Protect your sender reputation and improve email deliverability with enterprise-grade verification.</p>
          <div className="cta-actions">
            <Link to="/signup" className="btn-primary btn-large" aria-label="Start Free Account">Start Free</Link>
            <a href="mailto:sales@emailverif.com" className="btn-secondary btn-large" aria-label="Book Demo Call">Book a Demo</a>
          </div>
          
          <div className="cta-trust-badges">
            <span>✓ 100 Free Credits</span>
            <span>✓ No Credit Card Required</span>
            <span>✓ 24×7 Priority Support</span>
          </div>
        </div>
      </section>

      {/* 13. SIMPLE FOOTER */}
      <footer className="footer-section">
        <div className="container footer-grid">
          <div className="footer-brand-col">
            <Link to="/" className="footer-logo" aria-label="EmailVerif Logo">
              <ShieldCheck size={28} color="var(--primary)" weight="fill" />
              <span>EmailVerif</span>
            </Link>
            <p>Clean your list, maximize deliverability, and land in the inbox every time.</p>
            
            {/* Social Links */}
            <div className="footer-socials">
              <a href="https://twitter.com/emailverif" target="_blank" rel="noreferrer" aria-label="Follow us on Twitter">Twitter</a>
              <a href="https://github.com/emailverif" target="_blank" rel="noreferrer" aria-label="View code on GitHub">GitHub</a>
              <a href="https://linkedin.com/company/emailverif" target="_blank" rel="noreferrer" aria-label="Follow us on LinkedIn">LinkedIn</a>
            </div>
            <p className="copyright">© 2026 EmailVerif. All rights reserved.</p>
          </div>
          
          <div className="footer-links-col">
            <h4>Product</h4>
            <Link to="/#features">Features</Link>
            <Link to="/pricing">Pricing</Link>
            <Link to="/#how-it-works">How It Works</Link>
            <a href="https://status.emailverif.com" target="_blank" rel="noreferrer">Status Page</a>
          </div>
          
          <div className="footer-links-col">
            <h4>Developers</h4>
            <Link to="/#features">Documentation</Link>
            <a href="#release-notes">Release Notes</a>
            <Link to="/settings/keys">API Keys</Link>
          </div>
          
          <div className="footer-links-col">
            <h4>Company</h4>
            <Link to="/#testimonials">Blog</Link>
            <a href="mailto:support@emailverif.com">Contact</a>
            <Link to="/#faq">FAQ</Link>
          </div>
          
          <div className="footer-links-col">
            <h4>Legal</h4>
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/terms">Terms of Service</Link>
            <Link to="/refund">Refund Policy</Link>
            <Link to="/cookies">Cookie Policy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
