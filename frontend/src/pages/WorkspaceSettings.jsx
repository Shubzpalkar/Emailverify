import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import {
  getFullWorkspaceSettings, updateWorkspaceGeneral, uploadWorkspaceLogo,
  updateWorkspaceBranding, updateWorkspaceVerificationSettings,
  updateWorkspaceNotificationSettings, updateWorkspaceSecuritySettings,
  forceLogoutWorkspaceUsers, getWorkspaceAuditSummary, deleteWorkspaceDanger
} from '../api/client';
import {
  Buildings, Image, Users, CheckCircle, Sliders, Coin, Bell, ShieldCheck,
  CreditCard, ListDashes, Warning, Trash, Lock, Camera, ArrowRight,
  ArrowClockwise, Sparkle, Globe, Clock, FileCsv, FileXls, Code
} from '@phosphor-icons/react';
import './WorkspaceSettings.css';

const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Chicago', 'America/Denver',
  'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
  'Asia/Tokyo', 'Asia/Kolkata', 'Asia/Singapore', 'Australia/Sydney'
];

export default function WorkspaceSettings() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [activeSection, setActiveSection] = useState('general');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fullData, setFullData] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [logoUploading, setLogoUploading] = useState(false);

  // Forms State
  const [generalForm, setGeneralForm] = useState({
    company_name: '',
    workspace_name: '',
    website: '',
    industry: '',
    company_size: '',
    country: '',
    timezone: 'UTC',
    language: 'en'
  });

  const [brandingForm, setBrandingForm] = useState({
    brand_color: '#3b82f6',
    favicon_url: '',
    email_logo: ''
  });

  const [verificationForm, setVerificationForm] = useState({
    verification_mode: 'standard',
    download_format: 'CSV',
    duplicate_handling: 'remove',
    catch_all_handling: 'include',
    role_account_handling: 'include',
    disposable_handling: 'exclude',
    confidence_threshold: 70
  });

  const [notificationForm, setNotificationForm] = useState({
    notify_verification_completed: true,
    notify_credits_low: true,
    notify_team_invitations: true,
    notify_security_alerts: true,
    notify_weekly_reports: false,
    notify_monthly_reports: true,
    notify_api_usage_alerts: true
  });

  const [securityForm, setSecurityForm] = useState({
    require_email_verification: true,
    allow_google_login: true,
    session_timeout: '24h',
    low_credit_threshold: 1000
  });

  // Danger Zone Modal
  const [dangerModalOpen, setDangerModalOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmName, setDeleteConfirmName] = useState('');
  const [deletingWorkspace, setDeletingWorkspace] = useState(false);

  const canEdit = fullData?.can_edit ?? (user?.role === 'admin' || user?.role === 'superadmin');
  const isSuperadmin = fullData?.is_superadmin ?? (user?.role === 'superadmin');

  const fetchWorkspaceData = async () => {
    try {
      setLoading(true);
      const data = await getFullWorkspaceSettings();
      setFullData(data);

      if (data.general) {
        setGeneralForm({
          company_name: data.general.company_name || '',
          workspace_name: data.general.workspace_name || data.general.company_name || '',
          website: data.general.website || '',
          industry: data.general.industry || '',
          company_size: data.general.company_size || '',
          country: data.general.country || '',
          timezone: data.general.timezone || 'UTC',
          language: data.general.language || 'en'
        });

        setBrandingForm({
          brand_color: data.general.brand_color || '#3b82f6',
          favicon_url: data.general.favicon_url || '',
          email_logo: data.general.email_logo || ''
        });

        setSecurityForm({
          require_email_verification: data.general.require_email_verification ?? true,
          allow_google_login: data.general.allow_google_login ?? true,
          session_timeout: data.general.session_timeout || '24h',
          low_credit_threshold: data.general.low_credit_threshold || 1000
        });
      }

      if (data.verification_settings) {
        setVerificationForm({
          verification_mode: data.verification_settings.verification_mode || 'standard',
          download_format: data.verification_settings.download_format || 'CSV',
          duplicate_handling: data.verification_settings.duplicate_handling || 'remove',
          catch_all_handling: data.verification_settings.catch_all_handling || 'include',
          role_account_handling: data.verification_settings.role_account_handling || 'include',
          disposable_handling: data.verification_settings.disposable_handling || 'exclude',
          confidence_threshold: data.verification_settings.confidence_threshold ?? 70
        });
      }

      if (data.notification_settings) {
        setNotificationForm({
          notify_verification_completed: data.notification_settings.notify_verification_completed ?? true,
          notify_credits_low: data.notification_settings.notify_credits_low ?? true,
          notify_team_invitations: data.notification_settings.notify_team_invitations ?? true,
          notify_security_alerts: data.notification_settings.notify_security_alerts ?? true,
          notify_weekly_reports: data.notification_settings.notify_weekly_reports ?? false,
          notify_monthly_reports: data.notification_settings.notify_monthly_reports ?? true,
          notify_api_usage_alerts: data.notification_settings.notify_api_usage_alerts ?? true
        });
      }

      try {
        const audit = await getWorkspaceAuditSummary();
        setAuditLogs(audit);
      } catch { /* ignore fallback */ }

    } catch (err) {
      showToast(err.message || 'Failed to load workspace settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaceData();
  }, []);

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      showToast('Please select a valid image file (JPG, PNG, WebP)', 'error');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      showToast('Logo file size must be less than 2MB', 'error');
      return;
    }

    setLogoUploading(true);
    try {
      const res = await uploadWorkspaceLogo(file);
      showToast('Workspace logo updated successfully!');
      if (fullData?.general) {
        setFullData({
          ...fullData,
          general: { ...fullData.general, workspace_logo: res.logo_url }
        });
      }
    } catch (err) {
      showToast(err.message || 'Failed to upload logo', 'error');
    } finally {
      setLogoUploading(false);
    }
  };

  const handleGeneralSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateWorkspaceGeneral(generalForm);
      showToast('General workspace settings saved');
      setFullData(prev => prev ? { ...prev, general: updated } : prev);
    } catch (err) {
      showToast(err.message || 'Failed to save general settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleBrandingSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateWorkspaceBranding(brandingForm);
      showToast('Workspace branding updated');
      setFullData(prev => prev ? { ...prev, general: updated } : prev);
    } catch (err) {
      showToast(err.message || 'Failed to save branding', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleVerificationSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateWorkspaceVerificationSettings(verificationForm);
      showToast('Verification settings saved');
      setFullData(prev => prev ? { ...prev, verification_settings: updated } : prev);
    } catch (err) {
      showToast(err.message || 'Failed to save verification settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateWorkspaceNotificationSettings(notificationForm);
      showToast('Notification preferences saved');
      setFullData(prev => prev ? { ...prev, notification_settings: updated } : prev);
    } catch (err) {
      showToast(err.message || 'Failed to save notification preferences', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSecuritySubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateWorkspaceSecuritySettings(securityForm);
      showToast('Security policies saved');
      setFullData(prev => prev ? { ...prev, general: updated } : prev);
    } catch (err) {
      showToast(err.message || 'Failed to save security policies', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleForceLogoutAll = async () => {
    try {
      await forceLogoutWorkspaceUsers();
      showToast('All secondary user sessions have been terminated');
    } catch (err) {
      showToast(err.message || 'Failed to trigger force logout', 'error');
    }
  };

  const handleDeleteWorkspaceSubmit = async (e) => {
    e.preventDefault();
    if (!deletePassword || !deleteConfirmName) {
      showToast('Please fill out all required confirmation fields', 'error');
      return;
    }

    setDeletingWorkspace(true);
    try {
      await deleteWorkspaceDanger({
        password: deletePassword,
        workspace_name_confirmation: deleteConfirmName
      });
      showToast('Workspace permanently deleted');
      navigate('/dashboard');
    } catch (err) {
      showToast(err.message || 'Failed to delete workspace', 'error');
    } finally {
      setDeletingWorkspace(false);
    }
  };

  if (loading) {
    return (
      <div className="ws-settings-container">
        <div className="ws-card animate-pulse">
          <div style={{ height: '24px', width: '250px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', marginBottom: '1rem' }}></div>
          <div style={{ height: '16px', width: '400px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}></div>
        </div>
      </div>
    );
  }

  const gen = fullData?.general;
  const team = fullData?.team_summary;
  const credit = fullData?.credit_summary;

  return (
    <div className="ws-settings-container page-enter">
      {!canEdit && (
        <div className="read-only-banner">
          <Lock size={20} />
          <span>You are viewing workspace settings in read-only mode. Only Company Admins and Superadmins can modify settings.</span>
        </div>
      )}

      <div className="ws-settings-layout">
        {/* Left Navigation Sidebar */}
        <aside className="ws-nav-sidebar">
          <div className="ws-nav-title">Workspace Config</div>
          <div className="ws-nav-list">
            <button className={`ws-nav-item ${activeSection === 'general' ? 'active' : ''}`} onClick={() => setActiveSection('general')}>
              <Buildings size={18} /> General
            </button>
            <button className={`ws-nav-item ${activeSection === 'branding' ? 'active' : ''}`} onClick={() => setActiveSection('branding')}>
              <Image size={18} /> Branding
            </button>
            <button className={`ws-nav-item ${activeSection === 'team' ? 'active' : ''}`} onClick={() => setActiveSection('team')}>
              <Users size={18} /> Team Overview
            </button>
            <button className={`ws-nav-item ${activeSection === 'verification' ? 'active' : ''}`} onClick={() => setActiveSection('verification')}>
              <Sliders size={18} /> Verification Settings
            </button>
            <button className={`ws-nav-item ${activeSection === 'credits' ? 'active' : ''}`} onClick={() => setActiveSection('credits')}>
              <Coin size={18} /> Credit Settings
            </button>
            <button className={`ws-nav-item ${activeSection === 'notifications' ? 'active' : ''}`} onClick={() => setActiveSection('notifications')}>
              <Bell size={18} /> Notifications
            </button>
            <button className={`ws-nav-item ${activeSection === 'security' ? 'active' : ''}`} onClick={() => setActiveSection('security')}>
              <ShieldCheck size={18} /> Security
            </button>
            <button className={`ws-nav-item ${activeSection === 'billing' ? 'active' : ''}`} onClick={() => setActiveSection('billing')}>
              <CreditCard size={18} /> Billing
            </button>
            <button className={`ws-nav-item ${activeSection === 'audit' ? 'active' : ''}`} onClick={() => setActiveSection('audit')}>
              <ListDashes size={18} /> Audit Logs
            </button>
            {isSuperadmin && (
              <button className={`ws-nav-item danger-nav ${activeSection === 'danger' ? 'active' : ''}`} onClick={() => setActiveSection('danger')}>
                <Warning size={18} /> Danger Zone
              </button>
            )}
          </div>
        </aside>

        {/* Right Section Content */}
        <main style={{ flex: 1 }}>
          {/* SECTION 1: GENERAL */}
          {activeSection === 'general' && (
            <form onSubmit={handleGeneralSubmit} className="ws-card">
              <h3><Buildings size={22} /> General Information</h3>
              <p className="card-desc">Manage your workspace identity, company address details, and region localization.</p>

              <div className="form-grid-2">
                <div className="form-group">
                  <label>Workspace Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={generalForm.workspace_name}
                    onChange={e => setGeneralForm({ ...generalForm, workspace_name: e.target.value })}
                    disabled={!canEdit}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Company Legal Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={generalForm.company_name}
                    onChange={e => setGeneralForm({ ...generalForm, company_name: e.target.value })}
                    disabled={!canEdit}
                    required
                  />
                </div>

                <div className="form-group">
                  <label><Globe size={16} /> Company Website</label>
                  <input
                    type="url"
                    className="form-input"
                    placeholder="https://company.com"
                    value={generalForm.website}
                    onChange={e => setGeneralForm({ ...generalForm, website: e.target.value })}
                    disabled={!canEdit}
                  />
                </div>

                <div className="form-group">
                  <label>Industry</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="SaaS / Software"
                    value={generalForm.industry}
                    onChange={e => setGeneralForm({ ...generalForm, industry: e.target.value })}
                    disabled={!canEdit}
                  />
                </div>

                <div className="form-group">
                  <label>Company Size</label>
                  <select
                    className="form-select"
                    value={generalForm.company_size}
                    onChange={e => setGeneralForm({ ...generalForm, company_size: e.target.value })}
                    disabled={!canEdit}
                  >
                    <option value="">Select size</option>
                    <option value="1-10">1-10 employees</option>
                    <option value="11-50">11-50 employees</option>
                    <option value="51-200">51-200 employees</option>
                    <option value="201-500">201-500 employees</option>
                    <option value="500+">500+ employees</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Country</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="United States"
                    value={generalForm.country}
                    onChange={e => setGeneralForm({ ...generalForm, country: e.target.value })}
                    disabled={!canEdit}
                  />
                </div>

                <div className="form-group">
                  <label><Clock size={16} /> Timezone</label>
                  <select
                    className="form-select"
                    value={generalForm.timezone}
                    onChange={e => setGeneralForm({ ...generalForm, timezone: e.target.value })}
                    disabled={!canEdit}
                  >
                    {TIMEZONES.map(tz => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                </div>
              </div>

              {canEdit && (
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save General Settings'}
                </button>
              )}
            </form>
          )}

          {/* SECTION 2: BRANDING */}
          {activeSection === 'branding' && (
            <form onSubmit={handleBrandingSubmit} className="ws-card">
              <h3><Image size={22} /> Workspace Branding</h3>
              <p className="card-desc">Customize brand assets, logos, and custom color accents for exported reports.</p>

              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.75rem' }}>Workspace Logo</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                  <div style={{
                    width: '80px', height: '80px', borderRadius: '12px',
                    background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden'
                  }}>
                    {gen?.workspace_logo ? (
                      <img src={gen.workspace_logo} alt="Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                    ) : (
                      <Buildings size={32} color="var(--text-muted)" />
                    )}
                  </div>

                  {canEdit && (
                    <label className="btn-secondary" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Camera size={16} /> Upload New Logo
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        onChange={handleLogoUpload}
                        disabled={logoUploading}
                        style={{ display: 'none' }}
                      />
                    </label>
                  )}
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label>Brand Accent Color</label>
                  <div className="color-picker-group">
                    <input
                      type="color"
                      className="color-swatch"
                      value={brandingForm.brand_color}
                      onChange={e => setBrandingForm({ ...brandingForm, brand_color: e.target.value })}
                      disabled={!canEdit}
                    />
                    <input
                      type="text"
                      className="form-input"
                      value={brandingForm.brand_color}
                      onChange={e => setBrandingForm({ ...brandingForm, brand_color: e.target.value })}
                      disabled={!canEdit}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Favicon URL (Optional)</label>
                  <input
                    type="url"
                    className="form-input"
                    placeholder="https://company.com/favicon.ico"
                    value={brandingForm.favicon_url}
                    onChange={e => setBrandingForm({ ...brandingForm, favicon_url: e.target.value })}
                    disabled={!canEdit}
                  />
                </div>
              </div>

              {canEdit && (
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Branding'}
                </button>
              )}
            </form>
          )}

          {/* SECTION 3: TEAM OVERVIEW */}
          {activeSection === 'team' && (
            <div className="ws-card">
              <h3><Users size={22} /> Team Members Overview</h3>
              <p className="card-desc">Current workspace member statistics and quick management links.</p>

              <div className="summary-cards-grid">
                <div className="summary-card-item">
                  <label>Total Members</label>
                  <span className="metric-val">{team?.total_members || 1}</span>
                </div>
                <div className="summary-card-item">
                  <label>Active Members</label>
                  <span className="metric-val" style={{ color: 'var(--success, #22c55e)' }}>{team?.active_members || 1}</span>
                </div>
                <div className="summary-card-item">
                  <label>Pending Invites</label>
                  <span className="metric-val" style={{ color: 'var(--warning, #eab308)' }}>{team?.pending_invitations || 0}</span>
                </div>
                <div className="summary-card-item">
                  <label>Suspended</label>
                  <span className="metric-val" style={{ color: 'var(--danger, #ef4444)' }}>{team?.suspended_members || 0}</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button className="btn-primary" onClick={() => navigate('/account/team')}>
                  View Team Members <ArrowRight size={16} />
                </button>
                <button className="btn-secondary" onClick={() => navigate('/account/team')}>
                  Invite Member
                </button>
              </div>
            </div>
          )}

          {/* SECTION 4: VERIFICATION SETTINGS */}
          {activeSection === 'verification' && (
            <form onSubmit={handleVerificationSubmit} className="ws-card">
              <h3><Sliders size={22} /> Verification Defaults</h3>
              <p className="card-desc">Workspace-wide default verification mode, file export formats, and filtering rules.</p>

              <div className="form-grid-2" style={{ marginBottom: '1.5rem' }}>
                <div className="form-group">
                  <label>Default Verification Mode</label>
                  <select
                    className="form-select"
                    value={verificationForm.verification_mode}
                    onChange={e => setVerificationForm({ ...verificationForm, verification_mode: e.target.value })}
                    disabled={!canEdit}
                  >
                    <option value="standard">Standard Verification</option>
                    <option value="deep">Deep Scan Verification</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Default Export Format</label>
                  <select
                    className="form-select"
                    value={verificationForm.download_format}
                    onChange={e => setVerificationForm({ ...verificationForm, download_format: e.target.value })}
                    disabled={!canEdit}
                  >
                    <option value="CSV">CSV (.csv)</option>
                    <option value="XLSX">Excel (.xlsx)</option>
                    <option value="JSON">JSON (.json)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Duplicate Email Handling</label>
                  <select
                    className="form-select"
                    value={verificationForm.duplicate_handling}
                    onChange={e => setVerificationForm({ ...verificationForm, duplicate_handling: e.target.value })}
                    disabled={!canEdit}
                  >
                    <option value="remove">Remove Duplicates</option>
                    <option value="keep">Keep Duplicates</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Catch-All Mail Server Handling</label>
                  <select
                    className="form-select"
                    value={verificationForm.catch_all_handling}
                    onChange={e => setVerificationForm({ ...verificationForm, catch_all_handling: e.target.value })}
                    disabled={!canEdit}
                  >
                    <option value="include">Include in Output</option>
                    <option value="exclude">Exclude from Output</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Role Account Handling (admin@, info@)</label>
                  <select
                    className="form-select"
                    value={verificationForm.role_account_handling}
                    onChange={e => setVerificationForm({ ...verificationForm, role_account_handling: e.target.value })}
                    disabled={!canEdit}
                  >
                    <option value="include">Include</option>
                    <option value="exclude">Exclude</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Disposable Domain Handling</label>
                  <select
                    className="form-select"
                    value={verificationForm.disposable_handling}
                    onChange={e => setVerificationForm({ ...verificationForm, disposable_handling: e.target.value })}
                    disabled={!canEdit}
                  >
                    <option value="exclude">Exclude Disposable Emails</option>
                    <option value="include">Include Disposable Emails</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Confidence Threshold Score ({verificationForm.confidence_threshold}%)
                </label>
                <div className="slider-container">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={verificationForm.confidence_threshold}
                    onChange={e => setVerificationForm({ ...verificationForm, confidence_threshold: Number(e.target.value) })}
                    disabled={!canEdit}
                  />
                  <span className="slider-val-badge">{verificationForm.confidence_threshold}%</span>
                </div>
              </div>

              {canEdit && (
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Verification Settings'}
                </button>
              )}
            </form>
          )}

          {/* SECTION 5: CREDIT SETTINGS */}
          {activeSection === 'credits' && (
            <div className="ws-card">
              <h3><Coin size={22} /> Workspace Credit Configuration</h3>
              <p className="card-desc">View credit consumption metrics and configure low credit alert thresholds.</p>

              <div className="summary-cards-grid">
                <div className="summary-card-item">
                  <label>Remaining Credits</label>
                  <span className="metric-val" style={{ color: 'var(--primary, #3b82f6)' }}>{credit?.remaining_credits?.toLocaleString?.() ?? 0}</span>
                </div>
                <div className="summary-card-item">
                  <label>Total Allocated</label>
                  <span className="metric-val">{credit?.total_credits?.toLocaleString?.() ?? 0}</span>
                </div>
                <div className="summary-card-item">
                  <label>Used Credits</label>
                  <span className="metric-val">{credit?.used_credits?.toLocaleString?.() ?? 0}</span>
                </div>
                <div className="summary-card-item">
                  <label>Monthly Usage</label>
                  <span className="metric-val">{credit?.monthly_usage?.toLocaleString?.() ?? 0}</span>
                </div>
              </div>

              <form onSubmit={handleSecuritySubmit} style={{ marginTop: '1.5rem' }}>
                <div className="form-group" style={{ maxWidth: '400px', marginBottom: '1.5rem' }}>
                  <label>Low Credit Alert Threshold</label>
                  <input
                    type="number"
                    className="form-input"
                    value={securityForm.low_credit_threshold}
                    onChange={e => setSecurityForm({ ...securityForm, low_credit_threshold: Number(e.target.value) })}
                    disabled={!canEdit}
                  />
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Trigger automated email alerts when remaining credits fall below this number.
                  </span>
                </div>

                {canEdit && (
                  <button type="submit" className="btn-primary" disabled={saving}>
                    Save Threshold
                  </button>
                )}
              </form>
            </div>
          )}

          {/* SECTION 6: NOTIFICATION SETTINGS */}
          {activeSection === 'notifications' && (
            <form onSubmit={handleNotificationSubmit} className="ws-card">
              <h3><Bell size={22} /> Workspace Notifications</h3>
              <p className="card-desc">Configure workspace-wide automated notification and digest preferences.</p>

              <div className="preference-toggle-list" style={{ marginBottom: '2rem' }}>
                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Verification Completed</h4>
                    <p>Alert team when list verification jobs finish processing.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={notificationForm.notify_verification_completed}
                      onChange={e => setNotificationForm({ ...notificationForm, notify_verification_completed: e.target.checked })}
                      disabled={!canEdit}
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Credits Low Alert</h4>
                    <p>Notify administrators when credits cross threshold.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={notificationForm.notify_credits_low}
                      onChange={e => setNotificationForm({ ...notificationForm, notify_credits_low: e.target.checked })}
                      disabled={!canEdit}
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Team Invitations</h4>
                    <p>Notify when team members accept or join workspace.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={notificationForm.notify_team_invitations}
                      onChange={e => setNotificationForm({ ...notificationForm, notify_team_invitations: e.target.checked })}
                      disabled={!canEdit}
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Security & Auth Alerts</h4>
                    <p>Alert on suspicious logins, password resets, or API key changes.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={notificationForm.notify_security_alerts}
                      onChange={e => setNotificationForm({ ...notificationForm, notify_security_alerts: e.target.checked })}
                      disabled={!canEdit}
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>API Usage Alerts</h4>
                    <p>Notify when API request volume spikes or rate limits are reached.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={notificationForm.notify_api_usage_alerts}
                      onChange={e => setNotificationForm({ ...notificationForm, notify_api_usage_alerts: e.target.checked })}
                      disabled={!canEdit}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
              </div>

              {canEdit && (
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Notification Preferences'}
                </button>
              )}
            </form>
          )}

          {/* SECTION 7: SECURITY */}
          {activeSection === 'security' && (
            <form onSubmit={handleSecuritySubmit} className="ws-card">
              <h3><ShieldCheck size={22} /> Security Policies</h3>
              <p className="card-desc">Configure authentication restrictions, session timeout policies, and force session logouts.</p>

              <div className="preference-toggle-list" style={{ marginBottom: '2rem' }}>
                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Require Email Verification</h4>
                    <p>Force team members to verify email before accessing workspace resources.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={securityForm.require_email_verification}
                      onChange={e => setSecurityForm({ ...securityForm, require_email_verification: e.target.checked })}
                      disabled={!canEdit}
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Allow Google Single Sign-On (SSO)</h4>
                    <p>Permit users to authenticate via Google OAuth.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={securityForm.allow_google_login}
                      onChange={e => setSecurityForm({ ...securityForm, allow_google_login: e.target.checked })}
                      disabled={!canEdit}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
              </div>

              <div className="form-group" style={{ maxWidth: '400px', marginBottom: '2rem' }}>
                <label>Inactivity Session Timeout</label>
                <select
                  className="form-select"
                  value={securityForm.session_timeout}
                  onChange={e => setSecurityForm({ ...securityForm, session_timeout: e.target.value })}
                  disabled={!canEdit}
                >
                  <option value="30m">30 Minutes</option>
                  <option value="1h">1 Hour</option>
                  <option value="4h">4 Hours</option>
                  <option value="8h">8 Hours</option>
                  <option value="24h">24 Hours</option>
                </select>
              </div>

              {canEdit && (
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <button type="submit" className="btn-primary" disabled={saving}>
                    Save Security Policies
                  </button>
                  <button type="button" className="btn-secondary" onClick={handleForceLogoutAll}>
                    Force Logout All Users
                  </button>
                </div>
              )}
            </form>
          )}

          {/* SECTION 8: BILLING (READ-ONLY V1.0) */}
          {activeSection === 'billing' && (
            <div className="ws-card">
              <h3><CreditCard size={22} /> Workspace Billing Summary</h3>
              <p className="card-desc">Overview of active subscription plan and billing metadata.</p>

              <div className="summary-cards-grid">
                <div className="summary-card-item">
                  <label>Current Plan</label>
                  <span className="metric-val">{gen?.plan || 'Free'}</span>
                </div>
                <div className="summary-card-item">
                  <label>Remaining Credits</label>
                  <span className="metric-val">{gen?.credits_remaining?.toLocaleString?.() ?? 0}</span>
                </div>
                <div className="summary-card-item">
                  <label>Renewal Date</label>
                  <span className="metric-val" style={{ fontSize: '1.2rem' }}>Auto-Renew</span>
                </div>
              </div>

              <div style={{
                background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.25)',
                padding: '1rem 1.25rem', borderRadius: '12px', marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem'
              }}>
                <Sparkle size={20} color="var(--primary)" />
                <span style={{ fontSize: '0.9rem' }}>Billing management & payment integration will be activated after Dodo payment gateway configuration.</span>
              </div>
            </div>
          )}

          {/* SECTION 9: AUDIT LOGS */}
          {activeSection === 'audit' && (
            <div className="ws-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3><ListDashes size={22} /> Workspace Audit Logs</h3>
                <button className="btn-secondary btn-small" onClick={fetchWorkspaceData}>
                  <ArrowClockwise size={14} /> Refresh Logs
                </button>
              </div>
              <p className="card-desc">Recent activity and administrative configuration events in this workspace.</p>

              <div className="profile-table-container">
                <table className="profile-table">
                  <thead>
                    <tr>
                      <th>Action</th>
                      <th>Details</th>
                      <th>Actor</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map(a => (
                      <tr key={a.id}>
                        <td><strong>{a.action}</strong></td>
                        <td>{a.details}</td>
                        <td>{a.actor_name}</td>
                        <td>{a.created_at ? new Date(a.created_at).toLocaleString() : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SECTION 10: DANGER ZONE (SUPERADMIN ONLY) */}
          {activeSection === 'danger' && isSuperadmin && (
            <div className="ws-card" style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}>
              <h3 style={{ color: 'var(--danger, #ef4444)' }}><Warning size={22} /> Superadmin Danger Zone</h3>
              <p className="card-desc">Irreversible workspace deletion and ownership transfer controls.</p>

              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', padding: '1.25rem', borderRadius: '12px', marginBottom: '1.5rem' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: '#fca5a5' }}>Permanently Delete Workspace</h4>
                <p style={{ margin: '0 0 1rem 0', fontSize: '0.88rem', color: '#f8fafc' }}>
                  Deleting this workspace will unassign all team members, invalidate all associated API keys, and purge workspace database records.
                </p>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.4)' }}
                  onClick={() => setDangerModalOpen(true)}
                >
                  <Trash size={16} /> Delete Workspace
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Danger Zone Confirmation Modal */}
      {dangerModalOpen && (
        <div className="danger-modal-backdrop">
          <div className="danger-modal-card" role="dialog" aria-modal="true" aria-labelledby="delete-workspace-title">
            <h3 id="delete-workspace-title" style={{ color: 'var(--danger, #ef4444)', marginTop: 0 }}>Confirm Workspace Deletion</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              This action is permanent and cannot be undone. To confirm, please enter your superadmin password and type <code>{gen?.workspace_name || gen?.company_name}</code> below.
            </p>

            <form onSubmit={handleDeleteWorkspaceSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.25rem' }}>
              <div className="form-group">
                <label>Superadmin Password</label>
                <input
                  type="password"
                  className="form-input"
                  value={deletePassword}
                  onChange={e => setDeletePassword(e.target.value)}
                  placeholder="Enter superadmin password"
                  required
                />
              </div>

              <div className="form-group">
                <label>Type Workspace Name to Confirm</label>
                <input
                  type="text"
                  className="form-input"
                  value={deleteConfirmName}
                  onChange={e => setDeleteConfirmName(e.target.value)}
                  placeholder={gen?.workspace_name || gen?.company_name}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                <button type="button" className="btn-secondary" onClick={() => setDangerModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" style={{ background: '#ef4444' }} disabled={deletingWorkspace}>
                  {deletingWorkspace ? 'Deleting...' : 'Permanently Delete Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
