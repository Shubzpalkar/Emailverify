import { CalendarBlank, DownloadSimple } from '@phosphor-icons/react';

export default function AnalyticsGlobalFilterBar({
  timeframe,
  setTimeframe,
  onExportReport
}) {
  return (
    <div className="analytics-filter-bar glass-card">
      <div className="filter-group-left">
        <CalendarBlank size={18} color="var(--primary)" />
        <span className="filter-bar-label">Time Period:</span>
        <div className="segmented-control">
          <button
            className={`segmented-btn ${timeframe === 'today' ? 'active' : ''}`}
            onClick={() => setTimeframe('today')}
          >
            Today
          </button>
          <button
            className={`segmented-btn ${timeframe === '7days' ? 'active' : ''}`}
            onClick={() => setTimeframe('7days')}
          >
            Last 7 Days
          </button>
          <button
            className={`segmented-btn ${timeframe === '30days' ? 'active' : ''}`}
            onClick={() => setTimeframe('30days')}
          >
            Last 30 Days
          </button>
          <button
            className={`segmented-btn ${timeframe === 'month' ? 'active' : ''}`}
            onClick={() => setTimeframe('month')}
          >
            This Month
          </button>
          <button
            className={`segmented-btn ${timeframe === 'year' ? 'active' : ''}`}
            onClick={() => setTimeframe('year')}
          >
            This Year
          </button>
        </div>
      </div>

      <div className="filter-group-right">
        <button className="btn-secondary btn-small" onClick={() => onExportReport('csv')}>
          <DownloadSimple size={16} /> Export CSV
        </button>
        <button className="btn-secondary btn-small" onClick={() => onExportReport('json')}>
          <DownloadSimple size={16} /> Export JSON
        </button>
      </div>
    </div>
  );
}
