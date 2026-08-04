import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import {
  getVerificationJobsSummary, getVerificationJobs, retryJob, archiveJob,
  deleteJob, bulkJobAction
} from '../api/client';
import JobSummaryCards from '../components/history/JobSummaryCards';
import JobFilters from '../components/history/JobFilters';
import JobTable from '../components/history/JobTable';
import JobDetailsDrawer from '../components/history/JobDetailsDrawer';
import DownloadModal from '../components/DownloadModal';
import { Link } from 'react-router-dom';
import { Plus, ListChecks } from '@phosphor-icons/react';
import './History.css';

export default function History() {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);

  const [jobs, setJobs] = useState([]);
  const [tableLoading, setTableLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Filters State
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [resultFilter, setResultFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const [selectedJobIds, setSelectedJobIds] = useState([]);

  // Drawer / Modals State
  const [selectedJobForDrawer, setSelectedJobForDrawer] = useState(null);
  const [downloadModalJob, setDownloadModalJob] = useState(null);

  const canManage = user?.role === 'admin' || user?.role === 'superadmin' || user?.role === 'manager';

  const fetchSummary = async () => {
    try {
      setSummaryLoading(true);
      const res = await getVerificationJobsSummary();
      setSummary(res);
    } catch {
      /* silent fallback */
    } finally {
      setSummaryLoading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      setTableLoading(true);
      const res = await getVerificationJobs({
        search,
        status: statusFilter,
        date: dateFilter,
        result: resultFilter,
        sort: sortBy,
        page,
        limit: 15
      });
      setJobs(res.jobs || []);
      setTotal(res.total || 0);
      setPages(res.pages || 1);
    } catch (err) {
      showToast(err.message || 'Failed to load verification jobs', 'error');
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [search, statusFilter, dateFilter, resultFilter, sortBy, page]);

  const handleRetryJob = async (jobId) => {
    try {
      await retryJob(jobId);
      showToast('Verification job re-queued for processing');
      fetchJobs();
      fetchSummary();
    } catch (err) {
      showToast(err.message || 'Failed to retry job', 'error');
    }
  };

  const handleArchiveJob = async (jobId) => {
    try {
      const res = await archiveJob(jobId);
      showToast(res.message);
      fetchJobs();
      fetchSummary();
    } catch (err) {
      showToast(err.message || 'Failed to archive job', 'error');
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this verification job?')) return;
    try {
      await deleteJob(jobId);
      showToast('Verification job deleted');
      fetchJobs();
      fetchSummary();
    } catch (err) {
      showToast(err.message || 'Failed to delete job', 'error');
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedJobIds.length === 0) return;
    if (action === 'delete' && !window.confirm(`Are you sure you want to delete ${selectedJobIds.length} selected job(s)?`)) return;

    try {
      await bulkJobAction(action, selectedJobIds);
      showToast(`Bulk ${action} executed successfully`);
      setSelectedJobIds([]);
      fetchJobs();
      fetchSummary();
    } catch (err) {
      showToast(err.message || 'Failed to execute bulk action', 'error');
    }
  };

  return (
    <div className="history-container page-enter">
      {/* Header */}
      <div className="history-header">
        <div>
          <h2>Enterprise Job Management Center</h2>
          <p>Monitor, filter, manage, and diagnose all email list verification jobs.</p>
        </div>
        <Link to="/verify" className="btn-primary">
          <Plus size={18} /> New Verification Job
        </Link>
      </div>

      {/* Top 8 Metric Summary Cards */}
      <JobSummaryCards summary={summary} loading={summaryLoading} />

      {/* Filters & Bulk Operations Toolbar */}
      <JobFilters
        search={search} setSearch={setSearch}
        statusFilter={statusFilter} setStatusFilter={setStatusFilter}
        dateFilter={dateFilter} setDateFilter={setDateFilter}
        resultFilter={resultFilter} setResultFilter={setResultFilter}
        sortBy={sortBy} setSortBy={setSortBy}
        selectedCount={selectedJobIds.length}
        onBulkAction={handleBulkAction}
        onRefresh={() => { fetchJobs(); fetchSummary(); }}
        canManage={canManage}
      />

      {/* Main Interactive Table */}
      <JobTable
        jobs={jobs}
        loading={tableLoading}
        selectedJobIds={selectedJobIds}
        setSelectedJobIds={setSelectedJobIds}
        onSelectJob={(j) => setSelectedJobForDrawer(j)}
        onDownloadJob={(j) => setDownloadModalJob(j)}
        onRetryJob={handleRetryJob}
        onArchiveJob={handleArchiveJob}
        onDeleteJob={handleDeleteJob}
        page={page}
        pages={pages}
        total={total}
        onPageChange={setPage}
        canManage={canManage}
      />

      {/* Job Details & Diagnostics Slide-over Drawer */}
      {selectedJobForDrawer && (
        <JobDetailsDrawer
          jobId={selectedJobForDrawer.id}
          onClose={() => setSelectedJobForDrawer(null)}
          onRefreshList={() => { fetchJobs(); fetchSummary(); }}
          canManage={canManage}
        />
      )}

      {/* Download Modal */}
      {downloadModalJob && (
        <DownloadModal
          job={downloadModalJob}
          onClose={() => setDownloadModalJob(null)}
        />
      )}
    </div>
  );
}
