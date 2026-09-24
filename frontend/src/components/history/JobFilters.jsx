import { MagnifyingGlass, Funnel, Archive, Trash, ArrowClockwise } from '@phosphor-icons/react';

export default function JobFilters({
  search, setSearch,
  statusFilter, setStatusFilter,
  dateFilter, setDateFilter,
  resultFilter, setResultFilter,
  sortBy, setSortBy,
  selectedCount,
  onBulkAction,
  onRefresh,
  canManage
}) {
  return (
    <div className="job-filters-container">
      {/* Top Search & Filter Bar */}
      <div className="job-filters-row">
        <div className="search-box-wrapper">
          <MagnifyingGlass size={18} className="search-icon" />
          <input
            type="text"
            className="form-input search-input"
            aria-label="Search verification jobs"
            placeholder="Search by Job ID, File Name, User or Workspace..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="filter-controls-group">
          {/* Status Filter */}
          <select
            className="form-select filter-select"
            aria-label="Filter by job status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">Status: All</option>
            <option value="completed">Completed</option>
            <option value="running">Running</option>
            <option value="queued">Queued</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
            <option value="archived">Archived</option>
          </select>

          {/* Date Filter */}
          <select
            className="form-select filter-select"
            aria-label="Filter by date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
          >
            <option value="all">Date: All Time</option>
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="7days">Last 7 Days</option>
            <option value="30days">Last 30 Days</option>
          </select>

          {/* Result Category Filter */}
          <select
            className="form-select filter-select"
            aria-label="Filter by result category"
            value={resultFilter}
            onChange={(e) => setResultFilter(e.target.value)}
          >
            <option value="all">Results: All</option>
            <option value="deliverable">Deliverable</option>
            <option value="protected">Protected / Risky</option>
            <option value="catch_all">Catch-All</option>
            <option value="invalid">Invalid</option>
            <option value="unknown">Unknown</option>
          </select>

          {/* Sort By */}
          <select
            className="form-select filter-select"
            aria-label="Sort verification jobs"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="newest">Sort: Newest First</option>
            <option value="oldest">Sort: Oldest First</option>
            <option value="emails">Sort: Total Emails</option>
            <option value="credits">Sort: Credits Used</option>
            <option value="duration">Sort: Duration</option>
          </select>

          <button className="btn-secondary btn-small" onClick={onRefresh} title="Refresh jobs list" aria-label="Refresh jobs list">
            <ArrowClockwise size={16} />
          </button>
        </div>
      </div>

      {/* Bulk Action Toolbar */}
      {selectedCount > 0 && (
        <div className="bulk-actions-bar">
          <span><strong>{selectedCount}</strong> job(s) selected</span>
          <div className="bulk-buttons">
            {canManage && (
              <>
                <button className="btn-secondary btn-small" onClick={() => onBulkAction('archive')}>
                  <Archive size={14} /> Archive Selected
                </button>
                <button className="btn-secondary btn-small" onClick={() => onBulkAction('retry')}>
                  <ArrowClockwise size={14} /> Retry Selected
                </button>
                <button className="btn-secondary btn-small" onClick={() => onBulkAction('delete')} style={{ color: '#ef4444' }}>
                  <Trash size={14} /> Delete Selected
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
