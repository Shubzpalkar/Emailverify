import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Coins, EnvelopeSimple, ArrowCircleDown } from '@phosphor-icons/react';
import { apiCall } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import DownloadModal from '../components/DownloadModal';
import './Dashboard.css';

export default function Dashboard() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [metrics, setMetrics] = useState(null);
  const [downloadJob, setDownloadJob] = useState(null);
  const pollRef = useRef(null);

  const loadDashboard = async () => {
    try {
      const data = await apiCall('/dashboard/metrics');
      setMetrics(data);

      // Set up polling if any jobs are processing
      const needsPoll = data.recent_jobs?.some(j => j.status === 'processing' || j.status === 'pending');
      if (needsPoll && !pollRef.current) {
        pollRef.current = setInterval(loadDashboard, 5000);
      } else if (!needsPoll && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch {
      showToast('Failed to load dashboard', 'error');
    }
  };

  useEffect(() => {
    loadDashboard();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const getStatusColor = (status) => {
    if (status === 'completed') return 'var(--success)';
    if (status === 'failed') return 'var(--error)';
    return 'var(--primary)';
  };

  return (
    <section className="container page-enter" style={{ paddingTop: '1rem' }}>
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h2>Overview</h2>
          <p>Overview of your recently processed lists</p>
        </div>
        <div className="credits-box glass-card">
          <Coins size={32} weight="fill" color="#fbbf24" />
          <div>
            <span className="label">Credits Available</span>
            <span className="value">{metrics?.credit_pool?.toLocaleString() ?? '...'}</span>
          </div>
          <Link to="/verify" className="btn-primary btn-small">Top up</Link>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card glass-card">
          <div className="stat-icon">
            <EnvelopeSimple size={28} weight="duotone" />
          </div>
          <div className="stat-info">
            <span className="label">Total Verified</span>
            <span className="value">{metrics?.total_verified?.toLocaleString() ?? '...'}</span>
          </div>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="recent-jobs glass-card">
        <div className="card-header">
          <h3>Recent Jobs</h3>
          <Link to="/verify" className="btn-secondary btn-small">New Job</Link>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {!metrics?.recent_jobs?.length ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>
                    No jobs yet. <Link to="/verify">Upload a list</Link> to start.
                  </td>
                </tr>
              ) : (
                metrics.recent_jobs.map(job => (
                  <tr key={job.id}>
                    <td><strong>{job.file_name}</strong></td>
                    <td>
                      <span
                        className="tag"
                        style={{
                          background: 'transparent',
                          border: `1px solid ${getStatusColor(job.status)}`,
                          color: getStatusColor(job.status),
                        }}
                      >
                        {job.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontSize: '0.8rem' }}>
                        {job.processed_emails.toLocaleString()} / {job.total_emails.toLocaleString()}
                      </div>
                      <div className="progress-bar" style={{ height: '4px', margin: '2px 0 0 0' }}>
                        <div className="progress" style={{ width: `${job.progress_percentage}%` }} />
                      </div>
                    </td>
                    <td>{new Date(job.created_at).toLocaleDateString()}</td>
                    <td>
                      {job.status === 'completed' ? (
                        <button
                          className="btn-icon"
                          title="Download results"
                          onClick={() => setDownloadJob(job)}
                        >
                          <ArrowCircleDown size={20} />
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Processing...</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {downloadJob && (
        <DownloadModal
          job={downloadJob}
          onClose={() => setDownloadJob(null)}
        />
      )}
    </section>
  );
}
