import { ArrowCircleDown, StopCircle, ArrowClockwise, Archive, Trash, Eye } from '@phosphor-icons/react';

export default function JobTable({
  jobs,
  loading,
  selectedJobIds,
  setSelectedJobIds,
  onSelectJob,
  onDownloadJob,
  onRetryJob,
  onArchiveJob,
  onDeleteJob,
  page,
  pages,
  total,
  onPageChange,
  canManage
}) {
  const getStatusColor = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'completed') return 'var(--success, #22c55e)';
    if (s === 'failed') return 'var(--danger, #ef4444)';
    if (s === 'cancelled') return '#f59e0b';
    if (s === 'archived') return '#94a3b8';
    return 'var(--primary, #3b82f6)';
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedJobIds(jobs.map(j => j.id));
    } else {
      setSelectedJobIds([]);
    }
  };

  const handleSelectOne = (id) => {
    if (selectedJobIds.includes(id)) {
      setSelectedJobIds(selectedJobIds.filter(i => i !== id));
    } else {
      setSelectedJobIds([...selectedJobIds, id]);
    }
  };

  if (loading) {
    return (
      <div className="profile-table-container">
        <table className="profile-table">
          <thead>
            <tr>
              <th><input type="checkbox" disabled /></th>
              <th>Job ID / File</th>
              <th>Uploaded By</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Credits</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {[...Array(5)].map((_, i) => (
              <tr key={i} className="animate-pulse">
                <td colSpan="7" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
                  <div className="skeleton-line full" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="job-table-wrapper">
      <div className="profile-table-container">
        <table className="profile-table sticky-header-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}>
                <input
                  type="checkbox"
                  checked={jobs.length > 0 && selectedJobIds.length === jobs.length}
                  onChange={handleSelectAll}
                />
              </th>
              <th>Job ID / File Name</th>
              <th>Uploaded By</th>
              <th>Status / Stage</th>
              <th>Progress</th>
              <th>Results Breakdown</th>
              <th>Credits</th>
              <th>Upload Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ padding: '0' }}>
                  <div className="table-empty-state">
                    <div className="empty-state-icon">
                      <ListChecks size={36} color="var(--primary)" />
                    </div>
                    <h4>No verification jobs found</h4>
                    <p>No jobs match your filter criteria, or you haven't uploaded any verification lists yet.</p>
                  </div>
                </td>
              </tr>
            ) : (
              jobs.map(j => {
                const isSelected = selectedJobIds.includes(j.id);
                return (
                  <tr key={j.id} className={`job-row ${isSelected ? 'row-selected' : ''}`}>
                    <td>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleSelectOne(j.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
                    <td onClick={() => onSelectJob(j)} style={{ cursor: 'pointer' }}>
                      <strong className="job-filename">{j.file_name}</strong>
                      <span className="job-id-sub">{j.id}</span>
                    </td>
                    <td>
                      <span className="job-uploader">{j.uploaded_by}</span>
                      <span className="job-ws-sub">{j.workspace_name}</span>
                    </td>
                    <td>
                      <span className="profile-badge" style={{
                        background: 'transparent',
                        border: `1px solid ${getStatusColor(j.status)}`,
                        color: getStatusColor(j.status)
                      }}>
                        ● {j.status}
                      </span>
                      <span className="job-stage-sub">{j.stage || 'Completed'}</span>
                    </td>
                    <td style={{ minWidth: '130px' }}>
                      <div style={{ fontSize: '0.78rem', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{j.processed_emails.toLocaleString()} / {j.total_emails.toLocaleString()}</span>
                        <span>{j.progress_percentage}%</span>
                      </div>
                      <div className="progress-track" style={{ height: '4px', marginTop: '3px' }}>
                        <div className="progress-fill" style={{ width: `${j.progress_percentage}%`, background: getStatusColor(j.status) }} />
                      </div>
                    </td>
                    <td>
                      <div className="verif-mini-bar">
                        <span title={`Deliverable: ${j.deliverable}`} style={{ color: '#22c55e' }}>{j.deliverable}</span> /
                        <span title={`Protected: ${j.protected}`} style={{ color: '#f59e0b' }}>{j.protected}</span> /
                        <span title={`Invalid: ${j.invalid}`} style={{ color: '#ef4444' }}>{j.invalid}</span>
                      </div>
                    </td>
                    <td><strong>{j.credits_used}</strong></td>
                    <td>{j.upload_date ? new Date(j.upload_date).toLocaleDateString() : 'N/A'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button
                          className="btn-icon"
                          title="View job details"
                          onClick={() => onSelectJob(j)}
                        >
                          <Eye size={16} />
                        </button>
                        {j.status === 'completed' || j.processed_emails > 0 ? (
                          <button
                            className="btn-icon"
                            title="Download reports"
                            onClick={() => onDownloadJob(j)}
                          >
                            <ArrowCircleDown size={16} />
                          </button>
                        ) : null}
                        {canManage && (j.status === 'failed' || j.status === 'cancelled') && (
                          <button
                            className="btn-icon"
                            title="Retry failed job"
                            onClick={() => onRetryJob(j.id)}
                          >
                            <ArrowClockwise size={16} />
                          </button>
                        )}
                        {canManage && (
                          <button
                            className="btn-icon"
                            title="Archive job"
                            onClick={() => onArchiveJob(j.id)}
                          >
                            <Archive size={16} color={j.is_archived ? 'var(--primary)' : 'inherit'} />
                          </button>
                        )}
                        {canManage && (
                          <button
                            className="btn-icon"
                            title="Delete job"
                            onClick={() => onDeleteJob(j.id)}
                            style={{ color: '#ef4444' }}
                          >
                            <Trash size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {pages > 1 && (
        <div className="table-pagination-footer">
          <span>Showing Page <strong>{page}</strong> of <strong>{pages}</strong> ({total} total jobs)</span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn-secondary btn-small" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              Previous
            </button>
            <button className="btn-secondary btn-small" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
