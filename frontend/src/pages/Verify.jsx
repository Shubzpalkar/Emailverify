import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadSimple } from '@phosphor-icons/react';
import { apiCall } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import './Verify.css';

export default function Verify() {
  const { updateCredits } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Bulk upload state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [dragOver, setDragOver] = useState(false);

  // Single verify state
  const [singleEmail, setSingleEmail] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [singleResult, setSingleResult] = useState(null);

  // --- File Upload ---
  const handleFile = async (file) => {
    if (!file.name.match(/\.(csv|xls|xlsx|txt)$/i)) {
      return showToast('Invalid file format', 'error');
    }
    if (file.size > 500 * 1024 * 1024) {
      return showToast('File too large (max 500MB)', 'error');
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setUploadProgress(`Uploading ${file.name}...`);

    try {
      const res = await apiCall('/jobs/upload', {
        method: 'POST',
        body: formData,
      });
      setUploadProgress(`Job started! Processing ${res.total_emails.toLocaleString()} emails.`);
      showToast('Job started successfully');
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (err) {
      showToast(err.message || 'Upload failed', 'error');
      setUploading(false);
      setUploadProgress('');
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  };

  // --- Single Verify ---
  const handleSingleVerify = async (e) => {
    e.preventDefault();
    setVerifying(true);
    setSingleResult(null);

    try {
      const res = await apiCall('/verify', {
        method: 'POST',
        body: JSON.stringify({ email: singleEmail }),
      });
      setSingleResult(res);
      updateCredits(-1);
    } catch (err) {
      showToast(err.message || 'Verification failed', 'error');
    } finally {
      setVerifying(false);
    }
  };

  const getStatusColor = (status) => {
    const map = {
      valid: 'var(--success)',
      invalid: 'var(--error)',
      disposable: 'var(--error)',
      risky: 'var(--warning)',
      catch_all: 'var(--warning)',
      role_based: 'var(--warning)',
      unknown: 'var(--text-muted)',
    };
    return map[status] || 'gray';
  };

  return (
    <section className="container page-enter" style={{ paddingTop: '1rem' }}>
      <div className="verify-layout">
        {/* Bulk Upload */}
        <div className="bulk-verify glass-card">
          <h3>Bulk Verification</h3>
          <p>Upload a .CSV, .TXT, or .XLSX file to verify multiple emails.</p>

          {!uploading ? (
            <div
              className={`upload-area ${dragOver ? 'dragover' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
            >
              <UploadSimple size={48} color="var(--primary)" />
              <p><strong>Click to upload</strong> or drag and drop</p>
              <p className="upload-hint">CSV, TXT, XLSX (Max 5M emails / 500MB)</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.txt,.xlsx,.xls"
                style={{ display: 'none' }}
                onChange={e => { if (e.target.files.length) handleFile(e.target.files[0]); }}
              />
            </div>
          ) : (
            <div className="upload-status">
              <div className="progress-bar">
                <div className="progress" style={{ width: '100%' }} />
              </div>
              <p className="progress-text">{uploadProgress}</p>
            </div>
          )}
        </div>

        {/* Single Verify */}
        <div className="single-verify glass-card">
          <h3>Single Verification</h3>
          <p>Verify a single email address instantly.</p>
          <form onSubmit={handleSingleVerify} className="single-form">
            <input
              type="email"
              placeholder="name@company.com"
              value={singleEmail}
              onChange={e => setSingleEmail(e.target.value)}
              required
            />
            <button type="submit" className="btn-primary" disabled={verifying}>
              {verifying ? 'Verifying...' : 'Verify'}
            </button>
          </form>

          {singleResult && (
            <div className="result-box">
              <div className="result-header">
                <strong>{singleResult.email}</strong>
                <span
                  className="tag"
                  style={{ background: getStatusColor(singleResult.status), color: 'white' }}
                >
                  {singleResult.status.toUpperCase()}
                </span>
              </div>
              <div className="result-details">
                <p>Domain: {singleResult.domain || 'N/A'}</p>
                <p>Role Account: {singleResult.role_based ? 'Yes' : 'No'}</p>
                <p>Disposable: {singleResult.disposable ? 'Yes' : 'No'}</p>
                {singleResult.confidence !== undefined && (
                  <p>Confidence: {(singleResult.confidence * 100).toFixed(0)}%</p>
                )}
                {singleResult.smtp_result && (
                  <p className="smtp-result">{singleResult.smtp_result}</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
