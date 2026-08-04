import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardSystemHealth } from '../../api/client';
import { Heartbeat, CheckCircle, Warning, Cpu } from '@phosphor-icons/react';

export default function HealthWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardSystemHealth();
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

  const monitors = data?.monitors || [];

  return (
    <WidgetWrapper
      title="System Health & Infrastructure"
      subtitle="Operational status of backend engine & services"
      icon={Heartbeat}
      permission="dashboard.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      actionButton={
        <span className={`profile-badge ${data?.status === 'Healthy' ? 'badge-status-active' : 'badge-status-pending'}`} style={{ fontSize: '0.75rem' }}>
          ● {data?.status || 'Operational'}
        </span>
      }
      className="health-widget-card"
    >
      <div className="health-grid">
        {monitors.map((m, i) => (
          <div className="health-item-card" key={i}>
            <div className="health-item-header">
              <span className="health-name">{m.name}</span>
              <span className="health-status-tag">
                <CheckCircle size={14} color="var(--success, #22c55e)" /> {m.status}
              </span>
            </div>
            <div className="health-latency">
              <Cpu size={14} /> Latency: <strong>{m.latency_ms} ms</strong>
            </div>
          </div>
        ))}
      </div>
    </WidgetWrapper>
  );
}
