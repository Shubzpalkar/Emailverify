import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardJobs, apiCall } from '../../api/client';
import { ListChecks, ArrowCircleDown, StopCircle } from '@phosphor-icons/react';
import { Link } from 'react-router-dom';
import DownloadModal from '../DownloadModal';
import { useToast } from '../Toast';

export default function JobsWidget() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [downloadJob, setDownloadJob] = useState(null);
  const { showToast } = useToast();

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardJobs();
      setJobs(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWidgetData();
  }, []);

  const handleCancelJob = async (jobId) => {
    try {
      await apiCall(`/jobs/${jobId}/cancel`, { method: 'POST' });
      showToast('Job cancelled successfully');
      fetchWidgetData();
    } catch (err) {
      showToast(err.message || 'Failed to cancel job', 'error');
    }
  };

  const getStatusColor = (status) => {
    if (status === 'completed') return 'var(--success, #22c55e)';
    if (status === 'failed') return 'var(--danger, #ef4444)';
    if (status === 'cancelled') return '#f59e0b';
    return 'var(--primary, #3b82f6)';
  };

  return (
    <>
      <WidgetWrapper
        title="Recent Verification Jobs"
        subtitle="Active & completed email list jobs"
        icon={ListChecks}
        permission="dashboard.view"
        loading={loading}
        error={error}
        onRefresh={fetchWidgetData}
        actionButton={
          <Link to="/verify" className="btn-secondary btn-small">
            + New Verification Job
          </Link>
        }
        className="jobs-widget-card"
      >
        <div className="profile-table-container">
          <table className="profile-table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No verification jobs found. <Link to="/verify">Upload a list</Link> to start.
                  </td>
                </tr>
              ) : (
                jobs.map(j => (
                  <tr key={j.id}>
                    <td><strong>{j.file_name}</strong></td>
                    <td>
                      <span className="profile-badge" style={{
                        background: 'transparent',
                        border: `1px solid ${getStatusColor(j.status)}`,
                        color: getStatusColor(j.status)
                      }}>
                        ● {j.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{j.processed_emails.toLocaleString()} / {j.total_emails.toLocaleString()}</span>
                        <span>{j.progress_percentage}%</span>
                      </div>
                      <div className="progress-track" style={{ height: '4px', marginTop: '4px' }}>
                        <div className="progress-fill" style={{ width: `${j.progress_percentage}%`, background: getStatusColor(j.status) }} />
                      </div>
                    </td>
                    <td>{j.created_at ? new Date(j.created_at).toLocaleDateString() : 'N/A'}</td>
                    <td>
                      {j.status === 'completed' ? (
                        <button
                          className="btn-secondary btn-small"
                          onClick={() => setDownloadJob(j)}
                          title="Download verification report"
                        >
                          <ArrowCircleDown size={16} /> Download
                        </button>
                      ) : (j.status === 'processing' || j.status === 'pending') ? (
                        <button
                          className="btn-secondary btn-small"
                          onClick={() => handleCancelJob(j.id)}
                          style={{ color: 'var(--danger, #ef4444)' }}
                        >
                          <StopCircle size={16} /> Stop
                        </button>
                      ) : j.processed_emails > 0 ? (
                        <button
                          className="btn-secondary btn-small"
                          onClick={() => setDownloadJob(j)}
                        >
                          <ArrowCircleDown size={16} /> Partial Results
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>-</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </WidgetWrapper>

      {downloadJob && (
        <DownloadModal
          job={downloadJob}
          onClose={() => setDownloadJob(null)}
        />
      )}
    </>
  );
}
