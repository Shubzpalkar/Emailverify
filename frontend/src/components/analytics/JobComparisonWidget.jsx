import { useState, useEffect } from 'react';
import WidgetWrapper from '../dashboard/WidgetWrapper';
import { compareAnalyticsJobs, getVerificationJobs } from '../../api/client';
import { GitDiff, ArrowRight } from '@phosphor-icons/react';

export default function JobComparisonWidget() {
  const [jobsList, setJobsList] = useState([]);
  const [jobAId, setJobAId] = useState('');
  const [jobBId, setJobBId] = useState('');
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function loadJobs() {
      try {
        const res = await getVerificationJobs({ limit: 10 });
        const list = res.jobs || [];
        setJobsList(list);
        if (list.length >= 2) {
          setJobAId(list[0].id);
          setJobBId(list[1].id);
        }
      } catch { /* ignore fallback */ }
    }
    loadJobs();
  }, []);

  const fetchComparison = async () => {
    if (!jobAId || !jobBId) return;
    try {
      setLoading(true);
      setError(false);
      const res = await compareAnalyticsJobs(jobAId, jobBId);
      setComparison(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (jobAId && jobBId) {
      fetchComparison();
    }
  }, [jobAId, jobBId]);

  const ja = comparison?.job_a || {};
  const jb = comparison?.job_b || {};
  const delta = comparison?.delta || {};

  return (
    <WidgetWrapper
      title="Job Side-by-Side Comparison Matrix"
      subtitle="Compare deliverability, invalid rates & credit efficiency between two verification jobs"
      icon={GitDiff}
      permission="analytics.view"
      loading={loading}
      error={error}
      onRefresh={fetchComparison}
      className="job-comparison-widget-card"
    >
      <div className="job-comp-selectors" style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem' }}>
        <div className="form-group" style={{ flex: 1 }}>
          <label>Select Job A</label>
          <select className="form-select" value={jobAId} onChange={(e) => setJobAId(e.target.value)}>
            {jobsList.map((j) => (
              <option key={j.id} value={j.id}>{j.file_name} ({j.id.slice(0, 8)})</option>
            ))}
          </select>
        </div>

        <div className="form-group" style={{ flex: 1 }}>
          <label>Select Job B</label>
          <select className="form-select" value={jobBId} onChange={(e) => setJobBId(e.target.value)}>
            {jobsList.map((j) => (
              <option key={j.id} value={j.id}>{j.file_name} ({j.id.slice(0, 8)})</option>
            ))}
          </select>
        </div>
      </div>

      <div className="profile-table-container">
        <table className="profile-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Job A ({ja.name})</th>
              <th>Job B ({jb.name})</th>
              <th>Variance Delta</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Total Emails Verified</td>
              <td>{ja.total?.toLocaleString()}</td>
              <td>{jb.total?.toLocaleString()}</td>
              <td><strong>{((jb.total || 0) - (ja.total || 0)).toLocaleString()}</strong></td>
            </tr>
            <tr>
              <td>Deliverable Rate</td>
              <td><span style={{ color: '#22c55e' }}>{ja.deliverable_pct}%</span></td>
              <td><span style={{ color: '#22c55e' }}>{jb.deliverable_pct}%</span></td>
              <td>
                <span style={{ color: delta.deliverable_diff >= 0 ? '#22c55e' : '#ef4444', fontWeight: 700 }}>
                  {delta.deliverable_diff >= 0 ? `+${delta.deliverable_diff}` : delta.deliverable_diff}%
                </span>
              </td>
            </tr>
            <tr>
              <td>Invalid Rate</td>
              <td><span style={{ color: '#ef4444' }}>{ja.invalid_pct}%</span></td>
              <td><span style={{ color: '#ef4444' }}>{jb.invalid_pct}%</span></td>
              <td>
                <span style={{ color: delta.invalid_diff <= 0 ? '#22c55e' : '#ef4444', fontWeight: 700 }}>
                  {delta.invalid_diff >= 0 ? `+${delta.invalid_diff}` : delta.invalid_diff}%
                </span>
              </td>
            </tr>
            <tr>
              <td>Credits Consumed</td>
              <td>{ja.credits}</td>
              <td>{jb.credits}</td>
              <td><strong>{((jb.credits || 0) - (ja.credits || 0))}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </WidgetWrapper>
  );
}
