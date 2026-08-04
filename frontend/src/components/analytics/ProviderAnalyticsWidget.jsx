import { useState, useEffect } from 'react';
import WidgetWrapper from '../dashboard/WidgetWrapper';
import { getAnalyticsProvider } from '../../api/client';
import { Cpu, ShieldCheck, Timer } from '@phosphor-icons/react';

export default function ProviderAnalyticsWidget({ timeframe }) {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getAnalyticsProvider(timeframe);
      setProviders(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWidgetData();
  }, [timeframe]);

  return (
    <WidgetWrapper
      title="Provider Intelligence & Latency Performance"
      subtitle="SMTP handshakes & defense wall response metrics by mail provider"
      icon={Cpu}
      permission="analytics.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="provider-analytics-widget-card"
    >
      <div className="health-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
        {providers.map((p, i) => (
          <div className="health-item-card" key={i}>
            <div className="health-item-header">
              <span className="health-name">{p.provider}</span>
              <span className="health-status-tag" style={{ color: 'var(--primary)' }}>
                {p.count.toLocaleString()} emails
              </span>
            </div>
            <div style={{ fontSize: '0.82rem', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <div>Protected Rate: <strong>{p.protected_rate}%</strong></div>
              <div>Catch-All Rate: <strong>{p.catch_all_rate}%</strong></div>
              <div className="health-latency">
                <Timer size={14} /> SMTP: <strong>{p.avg_smtp_ms} ms</strong> | DNS: <strong>{p.avg_dns_ms} ms</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </WidgetWrapper>
  );
}
