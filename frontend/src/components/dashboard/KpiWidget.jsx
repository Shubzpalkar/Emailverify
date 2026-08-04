import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardKpi } from '../../api/client';
import { Coins, ChartLineUp, EnvelopeSimple, PlayCircle, CheckCircle, Percent, Timer, CalendarBlank } from '@phosphor-icons/react';

export default function KpiWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardKpi();
      setData(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWidgetData();
  }, []);

  return (
    <WidgetWrapper
      title="Key Performance Indicators"
      subtitle="Real-time verification & credit metrics"
      icon={ChartLineUp}
      permission="dashboard.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="kpi-widget-card"
    >
      <div className="kpi-grid-container">
        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>
            <Coins size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Credits Remaining</span>
            <span className="kpi-value">{data?.credits_remaining?.toLocaleString() ?? '0'}</span>
          </div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>
            <EnvelopeSimple size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Today's Usage</span>
            <span className="kpi-value">{data?.today_usage?.toLocaleString() ?? '0'}</span>
          </div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#fde047' }}>
            <PlayCircle size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Running Jobs</span>
            <span className="kpi-value">{data?.running_jobs ?? '0'}</span>
          </div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80' }}>
            <CheckCircle size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Completed Jobs</span>
            <span className="kpi-value">{data?.completed_jobs ?? '0'}</span>
          </div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
            <Percent size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Success Rate</span>
            <span className="kpi-value">{data?.success_rate ?? '98.5'}%</span>
          </div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(244, 63, 94, 0.15)', color: '#fb7185' }}>
            <Timer size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Avg Verification Time</span>
            <span className="kpi-value">{data?.avg_verification_time_ms ?? 145} ms</span>
          </div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee' }}>
            <CalendarBlank size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Monthly Usage</span>
            <span className="kpi-value">{data?.monthly_usage?.toLocaleString() ?? '0'}</span>
          </div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(249, 115, 22, 0.15)', color: '#fb923c' }}>
            <EnvelopeSimple size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Jobs Created Today</span>
            <span className="kpi-value">{data?.jobs_today ?? '0'}</span>
          </div>
        </div>
      </div>
    </WidgetWrapper>
  );
}
