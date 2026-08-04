import { useState, useEffect } from 'react';
import WidgetWrapper from '../dashboard/WidgetWrapper';
import { getAnalyticsDomain } from '../../api/client';
import { Globe, Warning, Lightning } from '@phosphor-icons/react';

export default function DomainAnalyticsWidget({ timeframe }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getAnalyticsDomain(timeframe);
      setData(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWidgetData();
  }, [timeframe]);

  const topDomains = data?.top_domains || [];
  const worstDomains = data?.worst_domains || [];

  return (
    <WidgetWrapper
      title="Domain Quality & Performance Intelligence"
      subtitle="Deliverability metrics per domain target"
      icon={Globe}
      permission="analytics.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="domain-analytics-widget-card"
    >
      <div className="analytics-sub-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div className="analytics-box">
          <span className="analytics-box-title" style={{ color: 'var(--success, #22c55e)' }}>
            <Globe size={18} /> Top Verified Domains
          </span>
          <div className="profile-table-container">
            <table className="profile-table">
              <thead>
                <tr>
                  <th>Domain</th>
                  <th>Verified</th>
                  <th>Deliverable %</th>
                  <th>Invalid %</th>
                </tr>
              </thead>
              <tbody>
                {topDomains.map((d, i) => (
                  <tr key={i}>
                    <td><strong>{d.domain}</strong></td>
                    <td>{d.verified.toLocaleString()}</td>
                    <td><span style={{ color: '#22c55e' }}>{d.deliverable_pct}%</span></td>
                    <td><span style={{ color: '#ef4444' }}>{d.invalid_pct}%</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="analytics-box">
          <span className="analytics-box-title" style={{ color: 'var(--danger, #ef4444)' }}>
            <Warning size={18} /> High Risk & Disposable Domains
          </span>
          <div className="profile-table-container">
            <table className="profile-table">
              <thead>
                <tr>
                  <th>Domain</th>
                  <th>Verified</th>
                  <th>Invalid Rate</th>
                </tr>
              </thead>
              <tbody>
                {worstDomains.map((d, i) => (
                  <tr key={i}>
                    <td><strong>{d.domain}</strong></td>
                    <td>{d.verified.toLocaleString()}</td>
                    <td><span style={{ color: '#ef4444', fontWeight: 700 }}>{d.invalid_pct}%</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </WidgetWrapper>
  );
}
