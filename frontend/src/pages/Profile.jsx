import { useState, useEffect } from 'react';
import { sendPasswordResetEmail } from 'firebase/auth';
import { auth } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import {
  getProfile, updateProfile, uploadAvatar, getPreferences,
  updatePreferences, getSessions, revokeSession, getLoginHistory,
  recordPasswordChange
} from '../api/client';
import {
  UserCircle, Buildings, Gear, ShieldCheck, User, Phone, Briefcase,
  Globe, Clock, Translate, Camera, Check, Copy, Desktop, DeviceMobile,
  FileCsv, FileXls, Code, Key, Sparkle, LockKey, Lock, ShieldWarning,
  Sun, Moon, Laptop, Trash
} from '@phosphor-icons/react';
import { applyTheme } from '../utils/theme';
import './Profile.css';

const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Chicago', 'America/Denver',
  'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
  'Asia/Tokyo', 'Asia/Kolkata', 'Asia/Singapore', 'Australia/Sydney'
];

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Spanish (Español)' },
  { code: 'fr', label: 'French (Français)' },
  { code: 'de', label: 'German (Deutsch)' },
  { code: 'ja', label: 'Japanese (日本語)' },
  { code: 'hi', label: 'Hindi (हिन्दी)' }
];

export default function Profile() {
  const { user, firebaseUser, syncUser, resendVerificationEmail } = useAuth();
  const { showToast } = useToast();

  const [activeTab, setActiveTab] = useState('personal');
  const [loading, setLoading] = useState(true);
  const [profileData, setProfileData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loginHistory, setLoginHistory] = useState([]);

  // Forms State
  const [personalForm, setPersonalForm] = useState({
    display_name: '',
    phone: '',
    job_title: '',
    department: '',
    employee_id: '',
    timezone: 'UTC',
    language: 'en'
  });

  const [preferencesForm, setPreferencesForm] = useState({
    theme: 'system',
    email_notifications: true,
    notify_verification_completed: true,
    notify_credit_alerts: true,
    notify_team_invites: true,
    notify_security_alerts: true,
    download_preference: 'CSV',
    verification_preference: 'standard'
  });

  const [avatarUploading, setAvatarUploading] = useState(false);
  const [savingPersonal, setSavingPersonal] = useState(false);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [passwordResetLoading, setPasswordResetLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const fetchProfileData = async () => {
    try {
      setLoading(true);
      const data = await getProfile();
      setProfileData(data);

      if (data.personal_info) {
        setPersonalForm({
          display_name: data.personal_info.display_name || '',
          phone: data.personal_info.phone || '',
          job_title: data.personal_info.job_title || '',
          department: data.personal_info.department || '',
          employee_id: data.personal_info.employee_id || '',
          timezone: data.personal_info.timezone || 'UTC',
          language: data.personal_info.language || 'en'
        });
      }

      if (data.preferences) {
        const themeVal = data.preferences.theme || 'system';
        setPreferencesForm({
          theme: themeVal,
          email_notifications: data.preferences.email_notifications ?? true,
          notify_verification_completed: data.preferences.notify_verification_completed ?? true,
          notify_credit_alerts: data.preferences.notify_credit_alerts ?? true,
          notify_team_invites: data.preferences.notify_team_invites ?? true,
          notify_security_alerts: data.preferences.notify_security_alerts ?? true,
          download_preference: data.preferences.download_preference || 'CSV',
          verification_preference: data.preferences.verification_preference || 'standard'
        });
        applyTheme(themeVal);
      }

      // Fetch sessions and history
      try {
        const sess = await getSessions();
        setSessions(sess);
      } catch { /* ignore fallback */ }

      try {
        const hist = await getLoginHistory();
        setLoginHistory(hist);
      } catch { /* ignore fallback */ }

    } catch (err) {
      showToast(err.message || 'Failed to load profile data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileData();
  }, []);

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      showToast('Please select a valid image file (JPG, PNG, WebP)', 'error');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      showToast('Avatar file size must be less than 2 MB', 'error');
      return;
    }

    setAvatarUploading(true);
    try {
      const res = await uploadAvatar(file);
      showToast('Avatar updated successfully!');
      if (profileData) {
        setProfileData({
          ...profileData,
          personal_info: {
            ...profileData.personal_info,
            avatar_url: res.avatar_url
          }
        });
      }
      await syncUser();
    } catch (err) {
      showToast(err.message || 'Failed to upload avatar', 'error');
    } finally {
      setAvatarUploading(false);
    }
  };

  const handlePersonalSubmit = async (e) => {
    e.preventDefault();
    setSavingPersonal(true);
    try {
      const updated = await updateProfile(personalForm);
      showToast('Personal information updated successfully');
      setProfileData(prev => prev ? { ...prev, personal_info: updated } : prev);
      await syncUser();
    } catch (err) {
      showToast(err.message || 'Failed to update personal information', 'error');
    } finally {
      setSavingPersonal(false);
    }
  };

  const handleThemeSelect = (newTheme) => {
    setPreferencesForm(prev => ({ ...prev, theme: newTheme }));
    applyTheme(newTheme);
  };

  const handlePreferencesSubmit = async (e) => {
    e.preventDefault();
    setSavingPreferences(true);
    try {
      const updated = await updatePreferences(preferencesForm);
      showToast('Preferences updated successfully');
      setProfileData(prev => prev ? { ...prev, preferences: updated } : prev);
      applyTheme(preferencesForm.theme);
    } catch (err) {
      showToast(err.message || 'Failed to update preferences', 'error');
    } finally {
      setSavingPreferences(false);
    }
  };

  const handlePasswordReset = async () => {
    if (!profileData?.personal_info?.email) return;
    setPasswordResetLoading(true);
    try {
      await sendPasswordResetEmail(auth, profileData.personal_info.email);
      await recordPasswordChange();
      showToast('Password reset link sent to your email');
    } catch (err) {
      showToast(err.message || 'Failed to send password reset email', 'error');
    } finally {
      setPasswordResetLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    try {
      await revokeSession(sessionId);
      showToast('Session revoked successfully');
      setSessions(sessions.filter(s => s.id !== sessionId));
    } catch (err) {
      showToast(err.message || 'Failed to revoke session', 'error');
    }
  };

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopiedId(type);
    showToast('Copied to clipboard!');
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (loading) {
    return (
      <div className="profile-container">
        <div className="profile-hero animate-pulse">
          <div className="profile-avatar-fallback">...</div>
          <div style={{ flex: 1 }}>
            <div style={{ height: '24px', width: '200px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', marginBottom: '10px' }}></div>
            <div style={{ height: '16px', width: '300px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}></div>
          </div>
        </div>
      </div>
    );
  }

  const pInfo = profileData?.personal_info;
  const wInfo = profileData?.workspace_info;
  const prefs = profileData?.preferences;
  const aMeta = profileData?.account_metadata;

  return (
    <div className="profile-container page-enter">
      {/* User Hero Banner */}
      <div className="profile-hero">
        <div className="profile-avatar-wrapper">
          {pInfo?.avatar_url ? (
            <img src={pInfo.avatar_url} alt="Profile Avatar" className="profile-avatar-img" />
          ) : (
            <div className="profile-avatar-fallback">
              {(pInfo?.display_name || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
          )}
          <label htmlFor="avatar-file-input" className="avatar-upload-overlay" title="Upload new avatar">
            <Camera size={16} />
            <input
              id="avatar-file-input"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleAvatarChange}
              disabled={avatarUploading}
              style={{ display: 'none' }}
            />
          </label>
        </div>

        <div className="profile-hero-info">
          <h2>
            {pInfo?.display_name || 'User Profile'}
            {aMeta?.email_verified && <Check size={20} color="var(--success, #22c55e)" title="Verified Account" />}
          </h2>
          <p>{pInfo?.email}</p>
          <div className="profile-hero-badges">
            <span className="profile-badge badge-role">
              <UserCircle size={14} /> {wInfo?.current_role}
            </span>
            <span className="profile-badge badge-plan">
              <Sparkle size={14} /> {wInfo?.workspace_plan} Plan
            </span>
            <span className={`profile-badge ${aMeta?.account_status === 'Active' ? 'badge-status-active' : 'badge-status-pending'}`}>
              ● {aMeta?.account_status}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="profile-tabs">
        <button
          className={`profile-tab-btn ${activeTab === 'personal' ? 'active' : ''}`}
          onClick={() => setActiveTab('personal')}
        >
          <User size={18} /> Personal Info
        </button>
        <button
          className={`profile-tab-btn ${activeTab === 'workspace' ? 'active' : ''}`}
          onClick={() => setActiveTab('workspace')}
        >
          <Buildings size={18} /> Workspace Info
        </button>
        <button
          className={`profile-tab-btn ${activeTab === 'preferences' ? 'active' : ''}`}
          onClick={() => setActiveTab('preferences')}
        >
          <Gear size={18} /> Preferences
        </button>
        <button
          className={`profile-tab-btn ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          <ShieldCheck size={18} /> Security & Sessions
        </button>
        <button
          className={`profile-tab-btn ${activeTab === 'account' ? 'active' : ''}`}
          onClick={() => setActiveTab('account')}
        >
          <Key size={18} /> Account Details
        </button>
      </div>

      {/* SECTION 1: PERSONAL INFORMATION */}
      {activeTab === 'personal' && (
        <form onSubmit={handlePersonalSubmit} className="profile-section-card">
          <h3><User size={22} /> Personal Information</h3>
          <p className="section-desc">Manage your public display details, contact numbers, and location preferences.</p>

          <div className="form-grid-2">
            <div className="form-group">
              <label><User size={16} /> Full Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="John Doe"
                value={personalForm.display_name}
                onChange={e => setPersonalForm({ ...personalForm, display_name: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label><Lock size={16} /> Work Email (Managed by Auth)</label>
              <input
                type="email"
                className="form-input"
                value={pInfo?.email || ''}
                readOnly
                disabled
              />
            </div>

            <div className="form-group">
              <label><Phone size={16} /> Phone Number</label>
              <input
                type="tel"
                className="form-input"
                placeholder="+1 (555) 000-0000"
                value={personalForm.phone}
                onChange={e => setPersonalForm({ ...personalForm, phone: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label><Briefcase size={16} /> Job Title / Designation</label>
              <input
                type="text"
                className="form-input"
                placeholder="Senior QA / Full Stack Engineer"
                value={personalForm.job_title}
                onChange={e => setPersonalForm({ ...personalForm, job_title: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label><Buildings size={16} /> Department</label>
              <input
                type="text"
                className="form-input"
                placeholder="Engineering / DevOps"
                value={personalForm.department}
                onChange={e => setPersonalForm({ ...personalForm, department: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label><Key size={16} /> Employee ID (Optional)</label>
              <input
                type="text"
                className="form-input"
                placeholder="EMP-10928"
                value={personalForm.employee_id}
                onChange={e => setPersonalForm({ ...personalForm, employee_id: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label><Clock size={16} /> Timezone</label>
              <select
                className="form-select"
                value={personalForm.timezone}
                onChange={e => setPersonalForm({ ...personalForm, timezone: e.target.value })}
              >
                {TIMEZONES.map(tz => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label><Translate size={16} /> Preferred Language</label>
              <select
                className="form-select"
                value={personalForm.language}
                onChange={e => setPersonalForm({ ...personalForm, language: e.target.value })}
              >
                {LANGUAGES.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.label}</option>
                ))}
              </select>
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={savingPersonal}>
            {savingPersonal ? 'Saving Changes...' : 'Save Personal Info'}
          </button>
        </form>
      )}

      {/* SECTION 2: WORKSPACE INFORMATION */}
      {activeTab === 'workspace' && (
        <div className="profile-section-card">
          <h3><Buildings size={22} /> Workspace Information</h3>
          <p className="section-desc">Read-only details of the organization workspace you currently belong to.</p>

          <div className="read-only-grid">
            <div className="read-only-item">
              <label>Company Name</label>
              <span>{wInfo?.company_name}</span>
            </div>
            <div className="read-only-item">
              <label>Workspace Name</label>
              <span>{wInfo?.workspace_name}</span>
            </div>
            <div className="read-only-item">
              <label>Current Role</label>
              <span className="text-capitalize">{wInfo?.current_role}</span>
            </div>
            <div className="read-only-item">
              <label>Workspace Plan</label>
              <span>{wInfo?.workspace_plan}</span>
            </div>
            <div className="read-only-item">
              <label>Date Joined</label>
              <span>{wInfo?.date_joined ? new Date(wInfo.date_joined).toLocaleDateString() : 'N/A'}</span>
            </div>
            <div className="read-only-item">
              <label>Workspace Status</label>
              <span className="text-capitalize">{wInfo?.workspace_status}</span>
            </div>
          </div>
        </div>
      )}

      {/* SECTION 3: PREFERENCES */}
      {activeTab === 'preferences' && (
        <form onSubmit={handlePreferencesSubmit} className="profile-section-card">
          <h3><Gear size={22} /> User Preferences</h3>
          <p className="section-desc">Customize your interface theme, download exports, and notification triggers.</p>

          {/* Theme Selector */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.75rem' }}>Interface Theme</label>
            <div className="segmented-control">
              <button
                type="button"
                className={`segmented-btn ${preferencesForm.theme === 'light' ? 'active' : ''}`}
                onClick={() => handleThemeSelect('light')}
              >
                <Sun size={16} /> Light
              </button>
              <button
                type="button"
                className={`segmented-btn ${preferencesForm.theme === 'dark' ? 'active' : ''}`}
                onClick={() => handleThemeSelect('dark')}
              >
                <Moon size={16} /> Dark
              </button>
              <button
                type="button"
                className={`segmented-btn ${preferencesForm.theme === 'system' ? 'active' : ''}`}
                onClick={() => handleThemeSelect('system')}
              >
                <Laptop size={16} /> System
              </button>
            </div>
          </div>

          {/* Download & Verification Preferences */}
          <div className="form-grid-2" style={{ marginBottom: '2rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.75rem' }}>Default Download Format</label>
              <div className="segmented-control">
                <button
                  type="button"
                  className={`segmented-btn ${preferencesForm.download_preference === 'CSV' ? 'active' : ''}`}
                  onClick={() => setPreferencesForm({ ...preferencesForm, download_preference: 'CSV' })}
                >
                  <FileCsv size={16} /> CSV
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${preferencesForm.download_preference === 'XLSX' ? 'active' : ''}`}
                  onClick={() => setPreferencesForm({ ...preferencesForm, download_preference: 'XLSX' })}
                >
                  <FileXls size={16} /> XLSX
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${preferencesForm.download_preference === 'JSON' ? 'active' : ''}`}
                  onClick={() => setPreferencesForm({ ...preferencesForm, download_preference: 'JSON' })}
                >
                  <Code size={16} /> JSON
                </button>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.75rem' }}>Verification Preference</label>
              <div className="segmented-control">
                <button
                  type="button"
                  className={`segmented-btn ${preferencesForm.verification_preference === 'standard' ? 'active' : ''}`}
                  onClick={() => setPreferencesForm({ ...preferencesForm, verification_preference: 'standard' })}
                >
                  Standard
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${preferencesForm.verification_preference === 'deep' ? 'active' : ''}`}
                  onClick={() => setPreferencesForm({ ...preferencesForm, verification_preference: 'deep' })}
                >
                  Deep Scan
                </button>
              </div>
            </div>
          </div>

          {/* Notifications Toggles */}
          <div style={{ marginBottom: '2rem' }}>
            <h4 style={{ fontSize: '1.05rem', marginBottom: '1rem' }}>Notification Toggles</h4>
            <div className="preference-toggle-list">
              <div className="toggle-item">
                <div className="toggle-info">
                  <h4>Email Notifications</h4>
                  <p>Receive general platform updates and alerts via email.</p>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={preferencesForm.email_notifications}
                    onChange={e => setPreferencesForm({ ...preferencesForm, email_notifications: e.target.checked })}
                  />
                  <span className="slider"></span>
                </label>
              </div>

              <div className="toggle-item">
                <div className="toggle-info">
                  <h4>Verification Job Completion</h4>
                  <p>Notify when bulk email list processing is finished.</p>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={preferencesForm.notify_verification_completed}
                    onChange={e => setPreferencesForm({ ...preferencesForm, notify_verification_completed: e.target.checked })}
                  />
                  <span className="slider"></span>
                </label>
              </div>

              <div className="toggle-item">
                <div className="toggle-info">
                  <h4>Credit Alerts</h4>
                  <p>Notify when remaining workspace credits drop below threshold.</p>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={preferencesForm.notify_credit_alerts}
                    onChange={e => setPreferencesForm({ ...preferencesForm, notify_credit_alerts: e.target.checked })}
                  />
                  <span className="slider"></span>
                </label>
              </div>

              <div className="toggle-item">
                <div className="toggle-info">
                  <h4>Team Invitations</h4>
                  <p>Notify when you are invited to join or manage a workspace team.</p>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={preferencesForm.notify_team_invites}
                    onChange={e => setPreferencesForm({ ...preferencesForm, notify_team_invites: e.target.checked })}
                  />
                  <span className="slider"></span>
                </label>
              </div>

              <div className="toggle-item">
                <div className="toggle-info">
                  <h4>Security Alerts</h4>
                  <p>Notify on new device logins, password resets, or API key changes.</p>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={preferencesForm.notify_security_alerts}
                    onChange={e => setPreferencesForm({ ...preferencesForm, notify_security_alerts: e.target.checked })}
                  />
                  <span className="slider"></span>
                </label>
              </div>
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={savingPreferences}>
            {savingPreferences ? 'Saving Preferences...' : 'Save Preferences'}
          </button>
        </form>
      )}

      {/* SECTION 4: SECURITY & SESSIONS */}
      {activeTab === 'security' && (
        <div>
          {/* Password Section */}
          <div className="profile-section-card">
            <h3><LockKey size={22} /> Security & Password</h3>
            <p className="section-desc">Manage account password and security status.</p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <p style={{ margin: 0, fontWeight: 600 }}>Password Change</p>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Password Last Changed: {aMeta?.password_last_changed ? new Date(aMeta.password_last_changed).toLocaleString() : 'Never'}
                </span>
              </div>

              <button
                type="button"
                className="btn-secondary"
                onClick={handlePasswordReset}
                disabled={passwordResetLoading}
              >
                {passwordResetLoading ? 'Sending Reset Email...' : 'Send Password Reset Email'}
              </button>
            </div>
          </div>

          {/* Active Sessions */}
          <div className="profile-section-card">
            <h3><Desktop size={22} /> Active Sessions</h3>
            <p className="section-desc">Devices currently logged into your account.</p>

            <div className="profile-table-container">
              <table className="profile-table">
                <thead>
                  <tr>
                    <th>Browser / Device</th>
                    <th>IP Address</th>
                    <th>Location</th>
                    <th>Last Activity</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map(s => (
                    <tr key={s.id}>
                      <td>
                        <strong>{s.browser}</strong> ({s.device})
                        {s.is_current && <span className="current-session-badge">Current Session</span>}
                      </td>
                      <td><code>{s.ip_address}</code></td>
                      <td>{s.location}</td>
                      <td>{s.last_activity ? new Date(s.last_activity).toLocaleString() : 'Just now'}</td>
                      <td>
                        {!s.is_current ? (
                          <button
                            type="button"
                            className="btn-secondary btn-small"
                            onClick={() => handleRevokeSession(s.id)}
                            style={{ color: 'var(--danger, #ef4444)' }}
                          >
                            <Trash size={14} /> Revoke
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Active</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Login History */}
          <div className="profile-section-card">
            <h3><Clock size={22} /> Recent Login History</h3>
            <p className="section-desc">Recent login activity on your account.</p>

            <div className="profile-table-container">
              <table className="profile-table">
                <thead>
                  <tr>
                    <th>Date & Time</th>
                    <th>Browser / Device</th>
                    <th>IP Address</th>
                    <th>Location</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {loginHistory.map(h => (
                    <tr key={h.id}>
                      <td>{h.login_time ? new Date(h.login_time).toLocaleString() : 'N/A'}</td>
                      <td>{h.browser} ({h.device})</td>
                      <td><code>{h.ip_address}</code></td>
                      <td>{h.location}</td>
                      <td>
                        <span style={{ color: h.status === 'Success' ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>
                          ● {h.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SECTION 5: ACCOUNT DETAILS */}
      {activeTab === 'account' && (
        <div className="profile-section-card">
          <h3><Key size={22} /> System Account Information</h3>
          <p className="section-desc">Unique identifiers and account verification status metadata.</p>

          <div className="read-only-grid">
            <div className="read-only-item">
              <label>System User ID</label>
              <div className="copy-field">
                <code>{aMeta?.user_id}</code>
                <button
                  type="button"
                  className="btn-secondary btn-small"
                  onClick={() => copyToClipboard(aMeta?.user_id, 'uid')}
                >
                  {copiedId === 'uid' ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>
            </div>

            <div className="read-only-item">
              <label>Firebase UID</label>
              <div className="copy-field">
                <code>{aMeta?.firebase_uid || 'N/A'}</code>
                {aMeta?.firebase_uid && (
                  <button
                    type="button"
                    className="btn-secondary btn-small"
                    onClick={() => copyToClipboard(aMeta?.firebase_uid, 'fbuid')}
                  >
                    {copiedId === 'fbuid' ? <Check size={14} /> : <Copy size={14} />}
                  </button>
                )}
              </div>
            </div>

            <div className="read-only-item">
              <label>Account Created</label>
              <span>{aMeta?.created_at ? new Date(aMeta.created_at).toLocaleString() : 'N/A'}</span>
            </div>

            <div className="read-only-item">
              <label>Last Login</label>
              <span>{aMeta?.last_login ? new Date(aMeta.last_login).toLocaleString() : 'N/A'}</span>
            </div>

            <div className="read-only-item">
              <label>Last Profile Update</label>
              <span>{aMeta?.updated_at ? new Date(aMeta.updated_at).toLocaleString() : 'N/A'}</span>
            </div>

            <div className="read-only-item">
              <label>Email Verification Status</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.25rem' }}>
                <span style={{ color: aMeta?.email_verified ? 'var(--success, #22c55e)' : 'var(--warning, #eab308)', fontWeight: 600 }}>
                  {aMeta?.email_verified ? '● Verified' : '● Pending Verification'}
                </span>
                {!aMeta?.email_verified && (
                  <button type="button" className="btn-secondary btn-small" onClick={resendVerificationEmail}>
                    Resend Email
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}