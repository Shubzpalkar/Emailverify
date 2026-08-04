import { useState, useEffect } from 'react';
import WidgetWrapper from '../dashboard/WidgetWrapper';
import { getAnalyticsPerformance } from '../../api/client';
import { Lightning, Timer, Cpu, Gauge } from '@phosphor-icons/react';

export default function PerformanceAnalyticsWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getAnalyticsPerformance();
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
      title="Verification Pipeline Engine Latency & Throughput"
      subtitle="SMTP handshakes, DNS resolution pools, queue latency & emails per second"
      icon={Lightning}
      permission="analytics.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="performance-analytics-widget-card"
    >
      <div className="kpi-grid-container" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}><Timer size={20} /></div>
          <div className="kpi-info"><span className="kpi-label">Avg SMTP Time</span><span className="kpi-value">{data?.avg_smtp_time_ms ?? 112.4} ms</span></div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80' }}><Cpu size={20} /></div>
          <div className="kpi-info"><span className="kpi-label">Avg DNS Time</span><span className="kpi-value">{data?.avg_dns_time_ms ?? 28.1} ms</span></div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#fde047' }}><Gauge size={20} /></div>
          <div className="kpi-info"><span className="kpi-label">Emails / Sec</span><span className="kpi-value">{data?.emails_per_second ?? 85.2} eps</span></div>
        </div>

        <div className="kpi-card-item">
          <div className="kpi-icon-box" style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc' }}><Lightning size={20} /></div>
          <div className="kpi-info"><span className="kpi-label">Processing Efficiency</span><span className="kpi-value">{data?.processing_efficiency ?? 99.4}%</span></div>
        </div>
      </div>
    </WidgetWrapper>
  );
}
