import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  FileText, 
  Trash, 
  Play, 
  CheckCircle, 
  XCircle, 
  WarningCircle, 
  Question,
  EnvelopeSimple,
  ShieldCheck,
  Globe,
  SpinnerGap,
  UploadSimple,
  ListNumbers,
  Plugs,
  Code,
  ArrowCircleDown,
  Sparkle,
  Copy,
  Check,
  CaretDown
} from '@phosphor-icons/react';
import { apiCall } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import DownloadModal from '../components/DownloadModal';
import './Verify.css';

export default function Verify() {
  const { user, updateCredits } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Active tab state: 'file' | 'paste' | 'single' | 'integration' | 'api'
  const [activeTab, setActiveTab] = useState('file');

  // Sidebar cleaning type selector
  const [cleaningType, setCleaningType] = useState('one-time');

  // Bulk file upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [activeJob, setActiveJob] = useState(null);
  const [showDownloadModal, setShowDownloadModal] = useState(false);

  // Paste list state
  const [pastedEmails, setPastedEmails] = useState('');
  const [pastingInProgress, setPastingInProgress] = useState(false);

  // Single verify state
  const [singleEmail, setSingleEmail] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [singleResult, setSingleResult] = useState(null);

  // API tab copied state
  const [copiedCurl, setCopiedCurl] = useState(false);

  const userCredits = user?.credit_pool !== undefined ? user.credit_pool : (user?.credits !== undefined ? user.credits : 0);

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const onFileSelect = (file) => {
    if (!file) return;
    if (!file.name.match(/\.(csv|xls|xlsx|txt)$/i)) {
      return showToast('Invalid file format. Please upload CSV, XLSX, or TXT', 'error');
    }
    if (file.size > 500 * 1024 * 1024) {
      return showToast('File too large (max 500MB)', 'error');
    }
    setSelectedFile(file);
  };

  // --- Start File Upload ---
  const handleStartUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploading(true);
    setUploadProgress(`Uploading and processing ${selectedFile.name}...`);

    try {
      const res = await apiCall('/jobs/upload', {
        method: 'POST',
        body: formData,
      });
      setUploadProgress(`Job started! Processing ${res.total_emails.toLocaleString()} emails.`);
      showToast('Verification job created successfully');
      
      setActiveJob({ 
        id: res.job_id, 
        file_name: selectedFile.name, 
        status: 'processing', 
        total_emails: res.total_emails,
        counts: {} 
      });
    } catch (err) {
      showToast(err.message || 'Upload failed', 'error');
      setUploading(false);
      setUploadProgress('');
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) onFileSelect(e.dataTransfer.files[0]);
  };

  // --- Paste Email List Submit ---
  const handlePasteSubmit = async (e) => {
    e.preventDefault();
    const emails = pastedEmails
      .split(/[\n,;]+/)
      .map(e => e.trim())
      .filter(e => e.length > 0 && e.includes('@'));

    if (emails.length === 0) {
      return showToast('Please enter at least one valid email address', 'error');
    }

    // Create a virtual CSV file and upload through the standard file upload pipeline
    const csvContent = 'email\n' + emails.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const file = new File([blob], `pasted_list_${new Date().toISOString().slice(0, 10)}.csv`, { type: 'text/csv' });

    setSelectedFile(file);
    setActiveTab('file');
    setPastedEmails('');
    showToast(`${emails.length} email addresses ready for verification`);
  };

  // --- Single Verify ---
  const handleSingleVerify = async (e) => {
    e.preventDefault();
    if (!singleEmail.trim()) return;
    setVerifying(true);
    setSingleResult(null);

    try {
      const res = await apiCall('/verify', {
        method: 'POST',
        body: JSON.stringify({ email: singleEmail.trim() }),
      });
      setSingleResult(res);
      updateCredits(-1);
      showToast('Verification complete');
    } catch (err) {
      showToast(err.message || 'Verification failed', 'error');
    } finally {
      setVerifying(false);
    }
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'valid' || s === 'deliverable') {
      return { label: 'Valid', class: 'status-badge-valid', icon: <CheckCircle size={16} weight="fill" /> };
    }
    if (s === 'invalid' || s === 'undeliverable' || s === 'disposable') {
      return { label: s === 'disposable' ? 'Disposable' : 'Invalid', class: 'status-badge-invalid', icon: <XCircle size={16} weight="fill" /> };
    }
    if (s === 'catch_all' || s === 'risky' || s === 'role_based') {
      return { label: s === 'catch_all' ? 'Catch-All' : s === 'role_based' ? 'Role Based' : 'Risky', class: 'status-badge-risky', icon: <WarningCircle size={16} weight="fill" /> };
    }
    return { label: 'Unknown', class: 'status-badge-unknown', icon: <Question size={16} weight="bold" /> };
  };

  const copyCurlCode = () => {
    const code = `curl -X POST "https://api.emailverify.com/api/verify" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{"email": "john@example.com"}'`;
    navigator.clipboard.writeText(code);
    setCopiedCurl(true);
    setTimeout(() => setCopiedCurl(false), 2000);
    showToast('Code snippet copied to clipboard');
  };

  return (
    <section className="container page-enter verify-page-wrapper">
      <div className="verify-saas-container">
        
        {/* =========================================
            LEFT PANEL: CONTEXT, CLEANING TYPE & CREDITS
            ========================================= */}
        <aside className="verify-sidebar-panel">
          <div className="sidebar-section">
            <span className="sidebar-label">Module</span>
            <h3 className="sidebar-title">Email Verification</h3>
          </div>

          <div className="sidebar-section">
            <label className="sidebar-label" htmlFor="cleaning-type-select">Cleaning Type</label>
            <div className="custom-select-wrapper">
              <select 
                id="cleaning-type-select"
                className="sidebar-select"
                value={cleaningType}
                onChange={(e) => setCleaningType(e.target.value)}
              >
                <option value="one-time">One-Time List Cleaning</option>
                <option value="real-time">Real-time API Verification</option>
                <option value="scheduled">Scheduled Recurring</option>
              </select>
              <CaretDown size={14} className="select-caret" />
            </div>
          </div>

          <div className="sidebar-status-legend">
            <span className="sidebar-label">Status Categories</span>
            <div className="legend-items">
              <div className="legend-row">
                <span className="legend-dot valid" />
                <span>Deliverable / Valid</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot invalid" />
                <span>Invalid / Bounced</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot risky" />
                <span>Risky / Catch-All</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot unknown" />
                <span>Unknown / Timeout</span>
              </div>
            </div>
          </div>

          <div className="sidebar-credits-box">
            <div className="sidebar-credits-header">
              <span className="sidebar-credits-label">Available Balance</span>
              <span className="sidebar-credits-val">{userCredits.toLocaleString()}</span>
            </div>
            <p className="sidebar-credits-sub">Credits used for bulk list and API verifications.</p>
            <Link to="/billing" className="btn-primary btn-full btn-small">
              <Sparkle size={14} weight="fill" />
              + Buy Credits
            </Link>
          </div>
        </aside>

        {/* =========================================
            MAIN WORKSPACE AREA WITH SPACIOUS TABS
            ========================================= */}
        <main className="verify-main-workspace">
          
          {/* Workspace Tab Selector */}
          <div className="workspace-tabs-bar" role="tablist" aria-label="Verification Methods">
            <button 
              className={`workspace-tab-btn ${activeTab === 'file' ? 'active' : ''}`}
              onClick={() => setActiveTab('file')}
              role="tab"
              aria-selected={activeTab === 'file'}
            >
              <UploadSimple size={18} />
              <span>File Upload</span>
            </button>

            <button 
              className={`workspace-tab-btn ${activeTab === 'paste' ? 'active' : ''}`}
              onClick={() => setActiveTab('paste')}
              role="tab"
              aria-selected={activeTab === 'paste'}
            >
              <ListNumbers size={18} />
              <span>Paste Email List</span>
            </button>

            <button 
              className={`workspace-tab-btn ${activeTab === 'single' ? 'active' : ''}`}
              onClick={() => setActiveTab('single')}
              role="tab"
              aria-selected={activeTab === 'single'}
            >
              <EnvelopeSimple size={18} />
              <span>Single Email</span>
            </button>

            <button 
              className={`workspace-tab-btn ${activeTab === 'integration' ? 'active' : ''}`}
              onClick={() => setActiveTab('integration')}
              role="tab"
              aria-selected={activeTab === 'integration'}
            >
              <Plugs size={18} />
              <span>Integrations</span>
            </button>

            <button 
              className={`workspace-tab-btn ${activeTab === 'api' ? 'active' : ''}`}
              onClick={() => setActiveTab('api')}
              role="tab"
              aria-selected={activeTab === 'api'}
            >
              <Code size={18} />
              <span>API Quickstart</span>
            </button>
          </div>

          {/* Workspace Body Card */}
          <div className="workspace-content-card">
            
            {/* ----------------------------------------------------
                TAB 1: FILE UPLOAD
                ---------------------------------------------------- */}
            {activeTab === 'file' && (
              <div className="tab-pane-enter">
                {!uploading && !activeJob ? (
                  !selectedFile ? (
                    <div
                      className={`upload-dropzone-large ${dragOver ? 'dragover' : ''}`}
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={onDrop}
                      role="button"
                      tabIndex={0}
                      aria-label="Upload email list file"
                    >
                      <div className="dropzone-icon-box">
                        <FileText size={48} color="var(--primary)" weight="duotone" />
                      </div>
                      <h3 className="dropzone-main-heading">Drag & Drop Your File Here</h3>
                      <p className="dropzone-sub-heading">CSV, XLSX, XLS or TXT files up to 500MB</p>
                      
                      <button 
                        type="button" 
                        className="btn-primary" 
                        onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                      >
                        Select File
                      </button>

                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv,.txt,.xlsx,.xls"
                        style={{ display: 'none' }}
                        onChange={e => { if (e.target.files.length) onFileSelect(e.target.files[0]); }}
                      />
                    </div>
                  ) : (
                    <div className="file-selected-summary">
                      <div className="file-card-inner">
                        <div className="file-badge-icon">
                          <FileText size={36} color="var(--primary)" weight="duotone" />
                        </div>
                        <div className="file-info-col">
                          <h4 className="file-name-heading">{selectedFile.name}</h4>
                          <div className="file-meta-badges">
                            <span className="badge-pill">{selectedFile.name.split('.').pop().toUpperCase()}</span>
                            <span className="file-size-text">{formatFileSize(selectedFile.size)}</span>
                          </div>
                        </div>
                        <button 
                          className="btn-icon btn-remove"
                          onClick={() => setSelectedFile(null)}
                          title="Remove file"
                          aria-label="Remove file"
                        >
                          <Trash size={18} />
                        </button>
                      </div>

                      <div className="file-actions-row">
                        <button 
                          className="btn-secondary"
                          onClick={() => setSelectedFile(null)}
                        >
                          Choose Different File
                        </button>
                        <button 
                          className="btn-primary"
                          onClick={handleStartUpload}
                        >
                          <Play size={16} weight="fill" />
                          Start Verification
                        </button>
                      </div>
                    </div>
                  )
                ) : (
                  <div className="verification-running-view">
                    <div className="progress-card-header">
                      <div>
                        <h3 className="progress-main-title">Verification in Progress</h3>
                        <p className="progress-sub-title">{uploadProgress || 'Processing your email list...'}</p>
                      </div>
                      {activeJob?.id && (
                        <span className="job-id-tag">Job ID: {activeJob.id.slice(0, 8)}</span>
                      )}
                    </div>

                    <div className="progress-meter-wrapper">
                      <div className="progress-meter-bar animated-stripes" style={{ width: '100%' }} />
                    </div>

                    <div className="live-status-cards-grid">
                      <div className="live-card valid">
                        <span className="live-card-label">Deliverable</span>
                        <strong className="live-card-val">{activeJob?.counts?.valid ?? 'Processing'}</strong>
                      </div>
                      <div className="live-card invalid">
                        <span className="live-card-label">Invalid</span>
                        <strong className="live-card-val">{activeJob?.counts?.invalid ?? 'Processing'}</strong>
                      </div>
                      <div className="live-card risky">
                        <span className="live-card-label">Risky / Catch-all</span>
                        <strong className="live-card-val">{activeJob?.counts?.risky ?? 'Processing'}</strong>
                      </div>
                      <div className="live-card unknown">
                        <span className="live-card-label">Status</span>
                        <strong className="live-card-val">Active</strong>
                      </div>
                    </div>

                    <div className="progress-actions-footer">
                      <button
                        className="btn-secondary"
                        onClick={() => {
                          setSelectedFile(null);
                          setUploading(false);
                          setActiveJob(null);
                        }}
                      >
                        Verify Another File
                      </button>

                      <Link to="/history" className="btn-secondary">
                        View in History
                      </Link>

                      {activeJob && activeJob.status === "completed" && (
                        <button
                          className="btn-primary"
                          onClick={() => setShowDownloadModal(true)}
                        >
                          <ArrowCircleDown size={18} />
                          Download Results
                        </button>
                      )}
                    </div>

                    {showDownloadModal && activeJob && (
                      <DownloadModal
                        job={activeJob}
                        onClose={() => setShowDownloadModal(false)}
                      />
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ----------------------------------------------------
                TAB 2: PASTE EMAIL LIST
                ---------------------------------------------------- */}
            {activeTab === 'paste' && (
              <div className="tab-pane-enter">
                <form onSubmit={handlePasteSubmit} className="paste-list-form">
                  <div className="paste-header">
                    <h3>Paste Email List</h3>
                    <p>Enter email addresses line by line or separated by commas.</p>
                  </div>

                  <textarea
                    className="paste-textarea"
                    rows={10}
                    placeholder={"john@company.com\njane@acme.corp\nsales@business.org\nuser@domain.com"}
                    value={pastedEmails}
                    onChange={(e) => setPastedEmails(e.target.value)}
                    required
                  />

                  <div className="paste-footer">
                    <span className="paste-count-indicator">
                      {pastedEmails.split(/[\n,;]+/).filter(e => e.trim().length > 0).length} emails entered
                    </span>
                    <button type="submit" className="btn-primary">
                      Verify Emails
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* ----------------------------------------------------
                TAB 3: SINGLE EMAIL
                ---------------------------------------------------- */}
            {activeTab === 'single' && (
              <div className="tab-pane-enter single-verify-tab">
                <div className="single-verify-centered">
                  <h3 className="single-verify-heading">Verify a Single Email</h3>
                  <p className="single-verify-sub">Check mailbox deliverability, MX records, and spam protection instantly.</p>

                  <form onSubmit={handleSingleVerify} className="single-email-form">
                    <div className="single-input-wrapper">
                      <EnvelopeSimple size={20} className="single-input-icon" />
                      <input
                        type="email"
                        placeholder="email@example.com"
                        value={singleEmail}
                        onChange={e => setSingleEmail(e.target.value)}
                        required
                        className="single-email-input"
                      />
                    </div>
                    <button type="submit" className="btn-primary" disabled={verifying}>
                      {verifying ? (
                        <>
                          <SpinnerGap size={18} className="spinning" />
                          Verifying...
                        </>
                      ) : (
                        <>
                          <ShieldCheck size={18} />
                          Verify Email
                        </>
                      )}
                    </button>
                  </form>

                  {singleResult && (
                    <div className="single-result-card">
                      <div className="single-result-header">
                        <span className="single-result-email">{singleResult.email}</span>
                        {(() => {
                          const badge = getStatusBadge(singleResult.detailed_status || singleResult.status);
                          return (
                            <span className={`status-badge-pill ${badge.class}`}>
                              {badge.icon}
                              {badge.label}
                            </span>
                          );
                        })()}
                      </div>

                      <div className="single-result-grid">
                        <div className="result-metric-box">
                          <span className="metric-label">Domain</span>
                          <strong>{singleResult.domain || 'N/A'}</strong>
                        </div>
                        <div className="result-metric-box">
                          <span className="metric-label">Role Account</span>
                          <strong>{singleResult.role_based ? 'Yes' : 'No'}</strong>
                        </div>
                        <div className="result-metric-box">
                          <span className="metric-label">Disposable</span>
                          <strong>{singleResult.disposable ? 'Yes' : 'No'}</strong>
                        </div>
                        <div className="result-metric-box">
                          <span className="metric-label">Confidence</span>
                          <strong>{singleResult.confidence !== undefined ? `${(singleResult.confidence * 100).toFixed(0)}%` : '100%'}</strong>
                        </div>
                        {singleResult.mx_server && (
                          <div className="result-metric-box full-width">
                            <span className="metric-label">MX Server Host</span>
                            <code>{singleResult.mx_server}</code>
                          </div>
                        )}
                        {singleResult.reason && (
                          <div className="result-metric-box full-width">
                            <span className="metric-label">Technical Reason</span>
                            <span className="technical-reason-text">{singleResult.reason}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ----------------------------------------------------
                TAB 4: INTEGRATIONS
                ---------------------------------------------------- */}
            {activeTab === 'integration' && (
              <div className="tab-pane-enter">
                <div className="integrations-header">
                  <h3>Connected Integrations</h3>
                  <p>Seamlessly clean prospect lists directly from your favorite CRM and marketing automation tools.</p>
                </div>

                <div className="integrations-grid">
                  <div className="integration-card">
                    <div className="integration-icon-col">
                      <Plugs size={32} color="#ff4a00" weight="duotone" />
                    </div>
                    <div className="integration-info">
                      <h4>Zapier Automation</h4>
                      <p>Trigger instant verification upon form submission or new CRM leads.</p>
                    </div>
                    <button className="btn-secondary btn-small" onClick={() => showToast('Zapier Integration ready to connect')}>
                      Connect
                    </button>
                  </div>

                  <div className="integration-card">
                    <div className="integration-icon-col">
                      <Globe size={32} color="#2563eb" weight="duotone" />
                    </div>
                    <div className="integration-info">
                      <h4>Webhooks & Callbacks</h4>
                      <p>Receive real-time notifications on verification job completion.</p>
                    </div>
                    <button className="btn-secondary btn-small" onClick={() => navigate('/settings/keys')}>
                      Configure
                    </button>
                  </div>

                  <div className="integration-card">
                    <div className="integration-icon-col">
                      <FileText size={32} color="#16a34a" weight="duotone" />
                    </div>
                    <div className="integration-info">
                      <h4>Google Sheets</h4>
                      <p>Verify email rows automatically in linked Google Sheets spreadsheets.</p>
                    </div>
                    <button className="btn-secondary btn-small" onClick={() => showToast('Google Sheets extension available')}>
                      Connect
                    </button>
                  </div>

                  <div className="integration-card">
                    <div className="integration-icon-col">
                      <EnvelopeSimple size={32} color="#f59e0b" weight="duotone" />
                    </div>
                    <div className="integration-info">
                      <h4>HubSpot & CRM Sync</h4>
                      <p>Clean contacts and update bounce risk properties automatically.</p>
                    </div>
                    <button className="btn-secondary btn-small" onClick={() => showToast('HubSpot OAuth ready')}>
                      Connect
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ----------------------------------------------------
                TAB 5: API QUICKSTART
                ---------------------------------------------------- */}
            {activeTab === 'api' && (
              <div className="tab-pane-enter">
                <div className="api-quickstart-header">
                  <div>
                    <h3>Developer API Quickstart</h3>
                    <p>Integrate real-time email verification directly into your registration forms or backend.</p>
                  </div>
                  <Link to="/settings/keys" className="btn-secondary btn-small">
                    Manage API Keys
                  </Link>
                </div>

                <div className="code-snippet-card">
                  <div className="code-header">
                    <span>cURL Request</span>
                    <button className="btn-copy" onClick={copyCurlCode}>
                      {copiedCurl ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
                      {copiedCurl ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="code-body">
{`curl -X POST "https://api.emailverify.com/api/verify" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{"email": "john@example.com"}'`}
                  </pre>
                </div>

                <div className="code-snippet-card" style={{ marginTop: '1.25rem' }}>
                  <div className="code-header">
                    <span>Response (JSON)</span>
                  </div>
                  <pre className="code-body">
{`{
  "email": "john@example.com",
  "status": "valid",
  "detailed_status": "deliverable",
  "domain": "example.com",
  "mx_server": "mail.example.com",
  "is_role": false,
  "is_disposable": false,
  "confidence": 0.98
}`}
                  </pre>
                </div>
              </div>
            )}

          </div>
        </main>

      </div>
    </section>
  );
}
