import { useState, useEffect } from 'react';
import { X, CheckCircle, Circle, DownloadSimple } from '@phosphor-icons/react';
import { apiCall } from '../api/client';
import { useToast } from './Toast';
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
  const { showToast } = useToast();
  const jobId = job?.id || job?.job_id;

  const [counts, setCounts] = useState(() => {
    const raw = job?.counts || {};
    return {
      valid: raw.valid ?? raw.deliverable ?? job?.deliverable ?? job?.deliverable_count ?? 0,
      invalid: raw.invalid ?? job?.invalid ?? job?.invalid_count ?? 0,
      risky: raw.risky ?? raw.protected ?? job?.protected ?? job?.protected_count ?? 0,
      catch_all: raw.catch_all ?? job?.catch_all ?? job?.catch_all_count ?? 0,
      disposable: raw.disposable ?? job?.disposable ?? job?.disposable_count ?? 0,
      role_based: raw.role_based ?? raw.role ?? job?.role ?? job?.role_count ?? 0,
      unknown: raw.unknown ?? job?.unknown ?? job?.unknown_count ?? 0
    };
  });

  const [selectedStatuses, setSelectedStatuses] = useState(() => {
    const active = Object.entries(counts)
      .filter(([_, cnt]) => cnt > 0)
      .map(([k]) => k);
    return active.length > 0 ? active : STATUS_CONFIG.map(s => s.key);
  });

  const [selectedColumns, setSelectedColumns] = useState(
    ["email", "status", "domain", "created_at"]
  );

  const [rowCount, setRowCount] = useState(null);
  const [countError, setCountError] = useState('');
  const [countRetry, setCountRetry] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadFormat, setDownloadFormat] = useState(null);

  // Fetch actual status breakdown from backend
  useEffect(() => {
    let isMounted = true;
    async function loadBreakdown() {
      if (!jobId) return;
      try {
        setCountError('');
        const res = await apiCall(`/jobs/${jobId}/download/count`);
        if (isMounted && res.by_status) {
          setCounts(res.by_status);
          const activeKeys = Object.entries(res.by_status)
            .filter(([_, cnt]) => cnt > 0)
            .map(([k]) => k);
          if (activeKeys.length > 0) {
            setSelectedStatuses(activeKeys);
          } else {
            setSelectedStatuses(STATUS_CONFIG.map(s => s.key));
          }
          setRowCount(res.total);
        }
      } catch (err) {
        console.error("Failed to load download counts", err);
        if (isMounted) {
          setCountError(err.message || 'The result count could not be loaded.');
        }
      }
    }
    loadBreakdown();

    return () => { isMounted = false; };
  }, [jobId, countRetry]);

  // Recalculate rowCount when status selections change
  useEffect(() => {
    let isMounted = true;
    const fetchCount = async () => {
      if (!selectedStatuses.length) {
        setRowCount(0);
        setCountError('');
        return;
      }
      setRowCount(null);
      setCountError('');
      try {
        const params = new URLSearchParams();
        params.set("statuses", selectedStatuses.join(","));
        const res = await apiCall(`/jobs/${jobId}/download/count?${params.toString()}`);
        if (isMounted) setRowCount(res.total);
      } catch (err) {
        console.error("Failed to fetch count", err);
        if (isMounted) {
          setCountError(err.message || 'The result count could not be loaded.');
        }
      }
    };

    const timer = setTimeout(fetchCount, 250);
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [selectedStatuses, jobId]);

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

  const handleDownload = async (format) => {
    if (!selectedStatuses.length || !selectedColumns.length || !jobId) return;

    setIsDownloading(true);
    setDownloadFormat(format);

    try {
      const params = new URLSearchParams();
      if (selectedStatuses.length < 7) {
        params.set("statuses", selectedStatuses.join(","));
      }
      if (selectedColumns.length < 7) {
        params.set("columns", selectedColumns.join(","));
      }

      const res = await apiCall(`/jobs/${jobId}/download/${format}?${params.toString()}`);
      const blob = await res.blob();

      let filename = `${(job?.file_name || job?.filename || "emails").replace(/\.[^/.]+$/, "")}_verified.${format}`;
      const disposition = res.headers.get("content-disposition");
      if (disposition && disposition.includes("filename=")) {
        const match = disposition.match(/filename="?([^"]+)"?/);
        if (match && match[1]) filename = match[1];
      }

      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Failed to download file", err);
      showToast(err.message || 'Download failed. Please try again.', 'error');
    } finally {
      setIsDownloading(false);
      setDownloadFormat(null);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="download-modal-title"
        onClick={e => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3 id="download-modal-title" className="modal-title">Download results</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            <X size={20} />
          </button>
        </div>
        <p className="modal-filename">{job?.file_name || job?.filename}</p>

        <section>
          <h4 className="section-title">Filter by status</h4>
          <div className="chips-wrap">
            {STATUS_CONFIG.map(({ key, label, color }) => {
              const count = counts[key] ?? 0;
              const isSelected = selectedStatuses.includes(key);
              return (
                <button
                  key={key}
                  className={`status-chip ${isSelected ? 'selected' : ''} ${count === 0 ? 'empty' : ''}`}
                  style={{ '--chip-color': color }}
                  onClick={() => toggleStatus(key)}
                  disabled={count === 0}
                  aria-pressed={isSelected}
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
          {countError ? (
            <span className="count-empty">
              Could not load results: {countError}{' '}
              <button type="button" className="link-button" onClick={() => setCountRetry(value => value + 1)}>
                Retry
              </button>
            </span>
          ) : rowCount === null ? (
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
            disabled={isDownloading || rowCount === null || rowCount === 0 || Boolean(countError)}
          >
            {isDownloading && downloadFormat === "csv" ? "Preparing..." : "Download CSV"}
          </button>

          <button
            className="btn-download xlsx"
            onClick={() => handleDownload("xlsx")}
            disabled={isDownloading || rowCount === null || rowCount === 0 || Boolean(countError)}
          >
            {isDownloading && downloadFormat === "xlsx" ? "Preparing..." : "Download XLSX"}
          </button>
        </div>
      </div>
    </div>
  );
}
