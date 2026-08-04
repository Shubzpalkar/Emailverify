import { useState } from 'react';
import { useToast } from '../components/Toast';
import { exportAnalyticsReport } from '../api/client';
import AnalyticsGlobalFilterBar from '../components/analytics/AnalyticsGlobalFilterBar';
import OverviewKpiWidget from '../components/analytics/OverviewKpiWidget';
import DomainAnalyticsWidget from '../components/analytics/DomainAnalyticsWidget';
import ProviderAnalyticsWidget from '../components/analytics/ProviderAnalyticsWidget';
import JobComparisonWidget from '../components/analytics/JobComparisonWidget';
import HeatmapWidget from '../components/analytics/HeatmapWidget';
import TeamAnalyticsWidget from '../components/analytics/TeamAnalyticsWidget';
import PerformanceAnalyticsWidget from '../components/analytics/PerformanceAnalyticsWidget';
import SystemAnalyticsWidget from '../components/analytics/SystemAnalyticsWidget';
import './Analytics.css';

export default function Analytics() {
  const { showToast } = useToast();
  const [timeframe, setTimeframe] = useState('30days');

  const handleExportReport = async (format) => {
    try {
      await exportAnalyticsReport(format, timeframe);
      showToast(`Analytics summary exported as ${format.toUpperCase()}`);
    } catch (err) {
      showToast(err.message || 'Export failed', 'error');
    }
  };

  return (
    <div className="analytics-container page-enter">
      {/* Header */}
      <div className="analytics-header">
        <div>
          <h2>Enterprise Analytics & Business Intelligence Center</h2>
          <p>Real-time data quality ratios, domain/provider intelligence & performance metrics.</p>
        </div>
      </div>

      {/* Global Sticky Filter Bar */}
      <AnalyticsGlobalFilterBar
        timeframe={timeframe}
        setTimeframe={setTimeframe}
        onExportReport={handleExportReport}
      />

      {/* Analytics Command Center Grid */}
      <div className="analytics-grid">
        {/* Row 1: Executive KPI Overview */}
        <div className="col-12">
          <OverviewKpiWidget timeframe={timeframe} />
        </div>

        {/* Row 2: Domain Quality & Performance Intelligence */}
        <div className="col-12">
          <DomainAnalyticsWidget timeframe={timeframe} />
        </div>

        {/* Row 3: Provider Handshake & Latency Intelligence */}
        <div className="col-12">
          <ProviderAnalyticsWidget timeframe={timeframe} />
        </div>

        {/* Row 4: Side-by-Side Job Comparison Matrix */}
        <div className="col-12">
          <JobComparisonWidget />
        </div>

        {/* Row 5: 24x7 Activity Heatmap Matrix */}
        <div className="col-12">
          <HeatmapWidget />
        </div>

        {/* Row 6: Team Productivity Leaderboard */}
        <div className="col-12">
          <TeamAnalyticsWidget />
        </div>

        {/* Row 7: Engine Latency & Throughput */}
        <div className="col-6">
          <PerformanceAnalyticsWidget />
        </div>

        {/* Row 8: Infrastructure Performance (Admin/Superadmin) */}
        <div className="col-6">
          <SystemAnalyticsWidget />
        </div>
      </div>
    </div>
  );
}
