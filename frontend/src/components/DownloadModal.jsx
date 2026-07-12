import { useState, useEffect } from 'react';
import { X, CheckCircle, Circle, DownloadSimple } from '@phosphor-icons/react';
import { apiCall } from '../api/client';
import './DownloadModal.css';

const STATUS_CONFIG = [
  { key: "valid",      label: "Valid",      color: "#4CAF82" },
  { key: "invalid",    label: "Invalid",    color: "#E8707A" },
  { key: "risky",      label: "Risky",      color: "#F5A623" },
  { key: "catch_all",  label: "Catch-all",  color: "#7B8FD4" },
  { key: "disposable", label: "Disposable", color: "#B0A0E0" },
  { key: "role_based", label: "Role-based", color: "#85C1E9" },
  { key: "unknown",    label: "Unknown",    color: "#C8C8C8" },
];

const COLUMN_CONFIG = [
  { key: "email",         label: "Email address" },
  { key: "status",        label: "Status" },
  { key: "domain",        label: "Domain" },
  { key: "is_role",       label: "Is Role" },
  { key: "is_disposable", label: "Is Disposable" },
  { key: "smtp_result",   label: "SMTP Result" },
  { key: "created_at",    label: "Verified At" },
];

export default function DownloadModal({ job, onClose }) {
  const [selectedStatuses, setSelectedStatuses] = useState(
    Object.entries(job.counts || {})
      .filter(([_, count]) => count > 0)
      .map(([status]) => status)
  );

  const [selectedColumns, setSelectedColumns] = useState(
    ["email", "status", "domain", "created_at"]
  );

  const [rowCount, setRowCount] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadFormat, setDownloadFormat] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchCount = async () => {
      if (!selectedStatuses.length) {
        setRowCount(0);
        return;
      }
      setRowCount(null);
      try {
        const params = new URLSearchParams();
        params.set("statuses", selectedStatuses.join(","));
        const res = await apiCall(`/jobs/${job.id || job.job_id}/download/count?${params.toString()}`);
        if (isMounted) setRowCount(res.total);
      } catch (err) {
        console.error("Failed to fetch count", err);
      }
    };

    const timer = setTimeout(fetchCount, 300);
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [selectedStatuses, job.id, job.job_id]);

  const toggleStatus = (key) => {
    setSelectedStatuses(prev => 
      prev.includes(key) ? prev.filter(s => s !== key) : [...prev, key]
    );
  };

  const toggleColumn = (key) => {
    if (key === 'email') return; // Email is mandatory
    setSelectedColumns(prev => 
      prev.includes(key) ? prev.filter(c => c !== key) : [...prev, key]
    );
  };

  const handleDownload = (format) => {
    if (!selectedStatuses.length || !selectedColumns.length) return;

    setIsDownloading(true);
    setDownloadFormat(format);

    const params = new URLSearchParams();
    if (selectedStatuses.length < 7) {
      params.set("statuses", selectedStatuses.join(","));
    }
    if (selectedColumns.length < 7) {
      params.set("columns", selectedColumns.join(","));
    }

    const url = `/api/jobs/${job.id || job.job_id}/download/${format}?${params.toString()}`;

    const link = document.createElement("a");
    link.href = url;
    link.download = "";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => {
      setIsDownloading(false);
      setDownloadFormat(null);
    }, 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Download results</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            <X size={20} />
          </button>
        </div>
        <p className="modal-filename">{job.file_name || job.filename}</p>

        <section>
          <h4 className="section-title">Filter by status</h4>
          <div className="chips-wrap">
            {STATUS_CONFIG.map(({ key, label, color }) => {
              const count = job.counts?.[key] || 0;
              const isSelected = selectedStatuses.includes(key);
              return (
                <button
                  key={key}
                  className={`status-chip ${isSelected ? 'selected' : ''} ${count === 0 ? 'empty' : ''}`}
                  style={{ '--chip-color': color }}
                  onClick={() => count > 0 && toggleStatus(key)}
                  disabled={count === 0}
                >
                  <span className="chip-dot" />
                  {label}
                  <span className="chip-count">{count}</span>
                </button>
              );
            })}
          </div>
        </section>

        <section>
          <h4 className="section-title">Select columns</h4>
          <div className="columns-grid">
            {COLUMN_CONFIG.map(({ key, label }) => (
              <label 
                key={key} 
                className={`col-check ${key === 'email' ? 'disabled' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedColumns.includes(key)}
                  onChange={() => toggleColumn(key)}
                  disabled={key === 'email'}
                />
                {label}
              </label>
            ))}
          </div>
        </section>

        <div className="count-row">
          {rowCount === null ? (
            <span className="count-loading">Calculating...</span>
          ) : rowCount === 0 ? (
            <span className="count-empty">No results match the selected filters.</span>
          ) : (
            <span className="count-display">
              {rowCount.toLocaleString()} rows will be downloaded
            </span>
          )}
        </div>

        <div className="download-btns">
          <button
            className="btn-download csv"
            onClick={() => handleDownload("csv")}
            disabled={isDownloading || rowCount === 0}
          >
            {isDownloading && downloadFormat === "csv" ? "Preparing..." : "Download CSV"}
          </button>

          <button
            className="btn-download xlsx"
            onClick={() => handleDownload("xlsx")}
            disabled={isDownloading || rowCount === 0}
          >
            {isDownloading && downloadFormat === "xlsx" ? "Preparing..." : "Download XLSX"}
          </button>
        </div>
      </div>
    </div>
  );
}
