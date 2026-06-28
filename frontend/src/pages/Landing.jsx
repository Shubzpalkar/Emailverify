import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Check, 
  ShieldCheck, 
  Lightning, 
  Cpu, 
  Users, 
  Warning, 
  FileCsv, 
  Download, 
  ArrowRight,
  DotsThreeCircle,
  Database,
  Code,
  Lock,
  Globe,
  XCircle,
  CheckCircle,
  Star,
  Envelope,
  Terminal,
  Shield,
  Key,
  ChartLine,
  FileText,
  Building,
  Briefcase,
  Clock,
  ArrowUpRight,
  EnvelopeSimple
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

  const problemSolutions = [
    {
      title: 'High Bounce Rates',
      desc: 'Sending campaigns to dead or non-existent mailboxes flag your IP as spam.',
      sol: 'Our engine checks active SMTP connections to ensure the inbox exists before you click send.'
    },
    {
      title: 'Poor Deliverability',
      desc: 'Trash domains and spam traps ruin sender score, causing inbox landing issues.',
      sol: 'We filter out temporary, catch-all, and disposable domains to preserve domain authority.'
    },
    {
      title: 'Blocked Domains',
      desc: 'Repeated bounces trigger blacklists across major ISPs like Google and Microsoft.',
      sol: 'Daily database cache scans automatically remove known blacklisted servers from lists.'
    },
    {
      title: 'Low Campaign Performance',
      desc: 'Emails sent to role addresses (info@, sales@) lead to low response rates.',
      sol: 'We detect role addresses and categorize results, allowing you to build highly-targeted lists.'
    }
  ];

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
    },
    {
      title: 'Fast Processing',
      desc: 'Async multi-threaded processing verified by a high-throughput backend.',
      icon: <Lightning size={24} color="var(--primary)" />
    },
    {
      title: 'Smart Cache',
      desc: 'Save credits by pulling results from our secure, 7-day historical database cache.',
      icon: <Database size={24} color="var(--primary)" />
    }
  ];

  const trustedSegments = [
    { name: 'Lead Gen Agencies', count: '180+ Active', desc: 'Maximize delivery for high volume cold outreach lists.' },
    { name: 'Sales Teams', count: '400+ Enterprise', desc: 'Secure domain reputation for B2B outbound campaign targets.' },
    { name: 'Recruitment Firms', count: '120+ Agencies', desc: 'Validate candidate applications and resume contacts.' },
    { name: 'Marketing Agencies', count: '300+ Clients', desc: 'Improve customer database quality and campaign metrics.' },
    { name: 'B2B SaaS Teams', count: '80+ Platforms', desc: 'Filter user signup domains dynamically at login point.' },
    { name: 'CRM Systems', count: '2.5M Syncs', desc: 'Maintain clean database entries via webhook routines.' }
  ];

  const providers = [
    { name: 'Google Workspace', status: 'Fully Compatible', desc: 'Validates Gmail and business account mailboxes without triggering alerts.' },
    { name: 'Microsoft 365', status: 'Fully Compatible', desc: 'Bypasses standard Office365 server traps for accurate live mailboxes.' },
    { name: 'Yahoo Mail', status: 'Fully Compatible', desc: 'Handles Yahoo SMTP connection limits safely to retrieve mailbox states.' },
    { name: 'Zoho Mail', status: 'Fully Compatible', desc: 'Detects business Zoho endpoints and flags active inbox statuses.' },
    { name: 'Proton Mail', status: 'Secure Check', desc: 'Handles encrypted Proton accounts without metadata compromise.' },
    { name: 'Fastmail', status: 'Fully Compatible', desc: 'Resolves fastmail domain alias addresses to avoid bounces.' },
    { name: 'Generic SMTP', status: '99.9% Success', desc: 'Support for custom servers, private ports, and internal configurations.' }
  ];

  const useCases = [
    { title: 'Lead Generation', desc: 'Clean outbound prospects lists to avoid spam box landing.', linkText: 'Clean Outbound Lists' },
    { title: 'Sales Outbound', desc: 'Enable cold emailers to contact buyers with total bounce immunity.', linkText: 'Enable Outbound' },
    { title: 'Recruiting Campaigns', desc: 'Clean outdated talent databases to maintain active contact sheets.', linkText: 'Clean Talent DB' },
    { title: 'Newsletter Marketing', desc: 'Verify incoming subscriber signup domains to block malicious bots.', linkText: 'Verify Signups' },
    { title: 'CRM Data Cleaning', desc: 'Clean Salesforce or Hubspot lists on schedule using API connections.', linkText: 'Integrate CRM' },
    { title: 'Cold Outreach', desc: 'Deliver emails to validated addresses to protect domain authority.', linkText: 'Protect Domain' }
  ];

  const apiRequestJson = `{
  "email": "hello@workspace.com",
  "dns_cache_check": true
}`;

  const apiResponseJson = `{
  "email": "hello@workspace.com",
  "status": "valid",
  "syntax": { "valid": true, "domain": "workspace.com" },
  "checks": {
    "domain_exists": true,
    "mx_records": true,
    "smtp_check": true,
    "catch_all": false,
    "disposable": false,
    "role_account": false
  },
  "confidence_score": 0.99,
  "verification_time_ms": 180,
  "smtp_response_code": 250,
  "risk_level": "safe"
}`;

  const securityFeatures = [
    { title: 'Encrypted Communication', desc: 'All data packets are secured with TLS 1.3 encryption and transit checks.', icon: <Lock size={28} /> },
    { title: 'Secure Infrastructure', desc: 'Hosted on enterprise VPCs with advanced access limit configuration.', icon: <Shield size={28} /> },
    { title: 'Privacy First Policy', desc: 'Uploaded email lists are completely purged from transient memory post processing.', icon: <CheckCircle size={28} /> },
    { title: 'Daily Database Backups', desc: 'Your metadata records are backed up and synced via safe encrypted nodes.', icon: <Database size={28} /> },
    { title: 'Role Based Access Control', desc: 'Grant granular dashboard permissions to team members and auditors.', icon: <Users size={28} /> },
    { title: 'Detailed Audit Logs', desc: 'Track API consumption, file exports, and credential usage reports.', icon: <FileText size={28} /> }
  ];

  const accuracySteps = [
    { label: 'Syntax Validation', val: 'RFC 5322 compliance' },
    { label: 'DNS Verification', val: 'A record audits' },
    { label: 'MX Checks', val: 'Priority servers lookup' },
    { label: 'SMTP Connection', val: 'Simulated mailbox check' },
    { label: 'Disposable Detection', val: 'Temp domain block' },
    { label: 'Role Account Check', val: 'Info / Admin separation' },
    { label: 'Catch-All Detection', val: 'Soft bounce loop analysis' },
    { label: 'Confidence Score', val: 'AI logic probability index' }
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
          <span className="badge">Audience Coverage</span>
          <h2>Trusted by Growing Businesses</h2>
          <p>Built for modern sales teams, recruiters, agencies and B2B companies.</p>
        </div>
        <div className="trusted-grid">
          {trustedSegments.map((seg, idx) => (
            <div key={idx} className="trusted-card glass-card">
              <Building size={28} color="var(--primary)" />
              <div>
                <h4>{seg.name}</h4>
                <p className="trusted-desc">{seg.desc}</p>
                <span className="trusted-count">{seg.count}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 2.5 ORIGINAL PROBLEM SECTION */}
      <section id="problem" className="problem-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">The Problem</span>
          <h2>The cost of sending to <span className="text-gradient">dirty lists</span></h2>
          <p>Sending emails without verifying them leads to negative reputations and blocks.</p>
        </div>
        <div className="problems-grid">
          {problemSolutions.map((item, idx) => (
            <div key={idx} className="problem-card glass-card">
              <div className="problem-tag">
                <Warning size={20} color="var(--error)" />
                <h4>{item.title}</h4>
              </div>
              <p className="problem-desc">{item.desc}</p>
              <div className="solution-box">
                <ShieldCheck size={20} color="var(--success)" />
                <p><strong>Solution:</strong> {item.sol}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. COMPARISON SECTION */}
      <section className="comparison-section-wrapper container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Risk & Impact</span>
          <h2>Why Verify Emails?</h2>
          <p>Compare the outcome of mailing unverified lists against validating targets first.</p>
        </div>
        <div className="comparison-cards-grid">
          <div className="comparison-card compare-bad glass-card">
            <div className="compare-card-title">
              <XCircle size={32} color="var(--error)" weight="fill" />
              <h3>Without Verification</h3>
            </div>
            <ul className="compare-list">
              <li>
                <Warning size={18} color="var(--error)" />
                <div>
                  <strong>High Bounce Rate:</strong> Unchecked mailboxes lead to massive bounce rates.
                </div>
              </li>
              <li>
                <Warning size={18} color="var(--error)" />
                <div>
                  <strong>Poor Deliverability:</strong> Spam filter mechanisms catch bad lists.
                </div>
              </li>
              <li>
                <Warning size={18} color="var(--error)" />
                <div>
                  <strong>Spam Complaints:</strong> Blocklists register your server domains immediately.
                </div>
              </li>
              <li>
                <Warning size={18} color="var(--error)" />
                <div>
                  <strong>Low Campaign ROI:</strong> Wasted budget sending to non-existent users.
                </div>
              </li>
              <li>
                <Warning size={18} color="var(--error)" />
                <div>
                  <strong>Damaged Sender Reputation:</strong> Forever flag your outbound IP records.
                </div>
              </li>
            </ul>
          </div>

          <div className="comparison-card compare-good glass-card">
            <div className="compare-card-title">
              <CheckCircle size={32} color="var(--success)" weight="fill" />
              <h3>With Our Platform</h3>
            </div>
            <ul className="compare-list">
              <li>
                <Check size={18} color="var(--success)" weight="bold" />
                <div>
                  <strong>Clean Email Lists:</strong> Automatically filter syntax typos and spam traps.
                </div>
              </li>
              <li>
                <Check size={18} color="var(--success)" weight="bold" />
                <div>
                  <strong>Lower Bounce Rate:</strong> Stay safely within ISP sending thresholds.
                </div>
              </li>
              <li>
                <Check size={18} color="var(--success)" weight="bold" />
                <div>
                  <strong>Higher Deliverability:</strong> Land in the inbox, increasing reply ratios.
                </div>
              </li>
              <li>
                <Check size={18} color="var(--success)" weight="bold" />
                <div>
                  <strong>Better Campaign Performance:</strong> Real contacts translate directly to revenue.
                </div>
              </li>
              <li>
                <Check size={18} color="var(--success)" weight="bold" />
                <div>
                  <strong>Protected Sender Reputation:</strong> Maintain high domain scores permanently.
                </div>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 4 & 5. LIVE VERIFICATION DEMO & ANIMATED PROCESS */}
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

      {/* 5 (Continued). STATIC VERIFICATION PROCESS EXPLANATION */}
      <section className="process-timeline-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Diagnostic Logic</span>
          <h2>The 7-Step Verification Workflow</h2>
          <p>Our backend engine runs these sequential operations on every single email address query.</p>
        </div>
        <div className="process-flow-container">
          <div className="process-flow-card glass-card">
            <span className="flow-num">01</span>
            <h4>Syntax Checks</h4>
            <p>Runs standard RFC structure syntax audits against input strings.</p>
          </div>
          <div className="flow-arrow"><ArrowRight size={24} /></div>
          <div className="process-flow-card glass-card">
            <span className="flow-num">02</span>
            <h4>Domain Verify</h4>
            <p>Audits active DNS state for resolving domain properties.</p>
          </div>
          <div className="flow-arrow"><ArrowRight size={24} /></div>
          <div className="process-flow-card glass-card">
            <span className="flow-num">03</span>
            <h4>DNS Check</h4>
            <p>Verifies active host connection routing configurations.</p>
          </div>
          <div className="flow-arrow"><ArrowRight size={24} /></div>
          <div className="process-flow-card glass-card">
            <span className="flow-num">04</span>
            <h4>MX Lookup</h4>
            <p>Extracts prioritized email server addresses from DNS tables.</p>
          </div>
          <div className="flow-arrow"><ArrowRight size={24} /></div>
          <div className="process-flow-card glass-card">
            <span className="flow-num">05</span>
            <h4>SMTP Handshake</h4>
            <p>Performs a live socket connection check without sending spam.</p>
          </div>
          <div className="flow-arrow"><ArrowRight size={24} /></div>
          <div className="process-flow-card glass-card">
            <span className="flow-num">06</span>
            <h4>Risk Check</h4>
            <p>Scans catch-all configurations and disposable services directories.</p>
          </div>
          <div className="flow-arrow"><ArrowRight size={24} /></div>
          <div className="process-flow-card glass-card">
            <span className="flow-num">07</span>
            <h4>Final Report</h4>
            <p>Scores the email status and records diagnostic confidence markers.</p>
          </div>
        </div>
      </section>

      {/* 6. FEATURES SECTION */}
      <section id="features" className="features-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Platform Features</span>
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

      {/* 7. SUPPORTED EMAIL PROVIDERS */}
      <section className="providers-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Compatibility</span>
          <h2>Supports Major Email Providers</h2>
          <p>Verified compatibility with complex corporate setups and popular personal domains.</p>
        </div>
        <div className="providers-grid">
          {providers.map((prov, idx) => (
            <div key={idx} className="provider-card glass-card">
              <div className="provider-card-header">
                <h4>{prov.name}</h4>
                <span className="provider-tag">{prov.status}</span>
              </div>
              <p className="provider-desc">{prov.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 8. USE CASE SECTION */}
      <section className="use-cases-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Who uses us</span>
          <h2>Use Cases For Verifying</h2>
          <p>How different team setups consume verification details to improve efficiency.</p>
        </div>
        <div className="use-cases-grid">
          {useCases.map((uc, idx) => (
            <div key={idx} className="use-case-card glass-card">
              <div className="uc-header">
                <Briefcase size={26} color="var(--primary)" />
                <h4>{uc.title}</h4>
              </div>
              <p className="uc-desc">{uc.desc}</p>
              <Link to="/signup" className="uc-cta-link" aria-label={`Start use case for ${uc.title}`}>
                {uc.linkText} <ArrowUpRight size={16} />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* 9. API SECTION */}
      <section id="api-section" className="api-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Developer Friendly</span>
          <h2>Developer API Integration</h2>
          <p>Integrate verification checks directly into signup forms or backend workflows.</p>
        </div>
        
        <div className="api-panel-wrapper glass-card">
          <div className="api-info-side">
            <h3>POST /api/v1/verify</h3>
            <p>Query mailboxes with ultra-low latency response cycles using standard HTTP clients.</p>
            
            <div className="api-features-vertical">
              <div className="api-feature-item">
                <Terminal size={22} color="var(--primary)" />
                <div>
                  <strong>REST API Standard:</strong> Pure JSON requests, standard status codes.
                </div>
              </div>
              <div className="api-feature-item">
                <Lightning size={22} color="var(--primary)" />
                <div>
                  <strong>Fast Response Cycles:</strong> Checks execute in less than 200ms globally.
                </div>
              </div>
              <div className="api-feature-item">
                <Key size={22} color="var(--primary)" />
                <div>
                  <strong>Secure Auth:</strong> Bearer tokens and client signature headers.
                </div>
              </div>
              <div className="api-feature-item">
                <Database size={22} color="var(--primary)" />
                <div>
                  <strong>High Throughput:</strong> Built on auto-scaling asynchronous workers.
                </div>
              </div>
            </div>
            
            <div className="api-action-buttons">
              <Link to="/signup" className="btn-primary" aria-label="Get API Key">Get API Key</Link>
              <a href="#documentation" className="btn-secondary" aria-label="View API Documentation">View Docs</a>
            </div>
          </div>

          <div className="api-code-side">
            <div className="code-tabs">
              <button 
                className={`code-tab-btn ${apiTab === 'request' ? 'active' : ''}`}
                onClick={() => setApiTab('request')}
              >
                Request JSON
              </button>
              <button 
                className={`code-tab-btn ${apiTab === 'response' ? 'active' : ''}`}
                onClick={() => setApiTab('response')}
              >
                Response JSON
              </button>
            </div>
            <div className="code-block-display">
              <pre>
                <code>
                  {apiTab === 'request' ? apiRequestJson : apiResponseJson}
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* 10. SECURITY SECTION */}
      <section id="security" className="security-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Security & Compliance</span>
          <h2>Enterprise Security</h2>
          <p>Protecting client data directories using industry standard infrastructure controls.</p>
        </div>
        <div className="security-grid">
          {securityFeatures.map((sec, idx) => (
            <div key={idx} className="security-card glass-card">
              <div className="security-icon-container">{sec.icon}</div>
              <h4>{sec.title}</h4>
              <p>{sec.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 11. ACCURACY SECTION */}
      <section className="accuracy-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Confidence System</span>
          <h2>How 99% Accuracy Is Achieved</h2>
          <p>A multi-phased parsing process that handles tricky mailboxes and domain configurations.</p>
        </div>
        
        <div className="accuracy-process-layout">
          <div className="accuracy-graphic-side">
            <div className="accuracy-circle">
              <div className="inner-accuracy">
                <h2>99.9%</h2>
                <span>Precision</span>
              </div>
            </div>
          </div>
          
          <div className="accuracy-grid-side">
            {accuracySteps.map((step, idx) => (
              <div key={idx} className="accuracy-step-item glass-card">
                <span className="acc-step-index">{idx + 1}</span>
                <div>
                  <strong>{step.label}</strong>
                  <p>{step.val}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 12. HOW IT WORKS */}
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
            <div className="timeline-content glass-card">
              <h3>Step 1: Upload CSV</h3>
              <p>Drag and drop your spreadsheet or list file (.csv) containing the email column into the dashboard panel. Our engine automatically parses and detects your fields.</p>
            </div>
          </div>
          <div className="timeline-item">
            <div className="timeline-icon">
              <Cpu size={28} color="white" />
            </div>
            <div className="timeline-content glass-card">
              <h3>Step 2: Verify Emails</h3>
              <p>Our multi-threaded verification scheduler connects to remote MX servers, classifying every address with full SMTP diagnostics without sending a single spam message.</p>
            </div>
          </div>
          <div className="timeline-item">
            <div className="timeline-icon">
              <Download size={28} color="white" />
            </div>
            <div className="timeline-content glass-card">
              <h3>Step 3: Download Results</h3>
              <p>Export a clean spreadsheet categorizing all Valid, Invalid, Role-based, and Disposable addresses. Upload and start sending with bounce-free confidence.</p>
            </div>
          </div>
        </div>
      </section>

      {/* 13. TESTIMONIAL SECTION */}
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

        {/* BETA PROGRAM BLOCK */}
        <div className="beta-program-wrapper glass-card text-center animate-on-scroll">
          <h3>Join Our Beta Program</h3>
          <p>Be one of our first customers. Experience enterprise scale email hygiene free of charge during our open portal window.</p>
          <Link to="/signup" className="btn-primary" aria-label="Join Beta Program">Join Beta Now</Link>
        </div>
      </section>

      {/* 14. IMPROVED PRICING PREVIEW */}
      <section id="pricing-preview" className="pricing-preview-section container animate-on-scroll">
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
        <div className="pricing-preview-cta">
          <Link to="/pricing" className="btn-primary btn-large" aria-label="View Full Pricing & Features">
            View Full Pricing & Compare Features <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* 15. FAQ ACCORDION */}
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

      {/* 16. CONTACT SECTION */}
      <section id="contact" className="contact-section container animate-on-scroll">
        <div className="section-header text-center">
          <span className="badge">Get in touch</span>
          <h2>Contact Support & Sales</h2>
          <p>Questions about volume discounts or custom SMTP integrations? Reach out to our teams.</p>
        </div>
        
        <div className="contact-block-layout glass-card">
          <div className="contact-details-side">
            <h3>Let's talk deliverability</h3>
            <p>Our engineers and account managers are available during key business schedules.</p>
            
            <div className="contact-info-list">
              <div className="contact-info-item">
                <EnvelopeSimple size={22} color="var(--primary)" />
                <div>
                  <span>Support Email</span>
                  <strong>support@emailverif.com</strong>
                </div>
              </div>
              <div className="contact-info-item">
                <EnvelopeSimple size={22} color="var(--primary)" />
                <div>
                  <span>Sales Division</span>
                  <strong>sales@emailverif.com</strong>
                </div>
              </div>
              <div className="contact-info-item">
                <Clock size={22} color="var(--primary)" />
                <div>
                  <span>Business Hours</span>
                  <strong>9:00 AM - 6:00 PM EST (Mon-Fri)</strong>
                </div>
              </div>
            </div>
          </div>
          
          <div className="contact-actions-side">
            <h4>Ready to get started?</h4>
            <p>Book a walkthrough demo call or message support teams directly.</p>
            <div className="contact-buttons-column">
              <a href="mailto:support@emailverif.com" className="btn-primary btn-large text-center" aria-label="Open support email client">
                Contact Support
              </a>
              <a href="mailto:sales@emailverif.com" className="btn-secondary btn-large text-center" aria-label="Request product live demo">
                Request Custom Demo
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* 17. FINAL CTA */}
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

      {/* 18. IMPROVED FOOTER */}
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
            <Link to="/#api-section">Documentation</Link>
            <Link to="/#api-section">API Docs</Link>
            <a href="#release-notes">Release Notes</a>
            <Link to="/settings/keys">API Keys</Link>
          </div>
          
          <div className="footer-links-col">
            <h4>Company</h4>
            <Link to="/#testimonials">Blog</Link>
            <Link to="/#contact">Contact</Link>
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
