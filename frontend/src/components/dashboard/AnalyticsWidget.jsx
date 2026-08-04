import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardAnalytics } from '../../api/client';
import { TrendUp, Globe, Cpu } from '@phosphor-icons/react';

export default function AnalyticsWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [timeframe, setTimeframe] = useState('daily');

  const fetchWidgetData = async (tf = timeframe) => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardAnalytics(tf);
      setData(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWidgetData(timeframe);
  }, [timeframe]);

  const maxCredit = Math.max(...(data?.trend?.map(t => t.credits) || [100]), 10);

  return (
    <WidgetWrapper
      title="Analytics & Verification Trends"
      subtitle="Usage velocity and domain provider intelligence"
      icon={TrendUp}
      permission="analytics.view"
      loading={loading}
      error={error}
      onRefresh={() => fetchWidgetData(timeframe)}
      actionButton={
        <div className="segmented-control" style={{ padding: '2px' }}>
          <button
            className={`segmented-btn ${timeframe === 'daily' ? 'active' : ''}`}
            onClick={() => setTimeframe('daily')}
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.78rem' }}
          >
            Daily
          </button>
          <button
            className={`segmented-btn ${timeframe === 'weekly' ? 'active' : ''}`}
            onClick={() => setTimeframe('weekly')}
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.78rem' }}
          >
            Weekly
          </button>
        </div>
      }
      className="analytics-widget-card"
    >
      <div className="analytics-widget-content">
        {/* Trend Bar Chart */}
        <div className="trend-chart-wrapper">
          <span className="analytics-section-title">Verification Credit Usage Trend</span>
          <div className="bar-chart-flex">
            {data?.trend?.map((item, i) => {
              const hPct = Math.min((item.credits / maxCredit) * 100, 100);
              return (
                <div key={i} className="bar-column">
                  <div className="bar-track">
                    <div className="bar-fill" style={{ height: `${Math.max(hPct, 8)}%` }} title={`${item.label}: ${item.credits} credits`} />
                  </div>
                  <span className="bar-label">{item.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Domains & Providers Grid */}
        <div className="analytics-sub-grid">
          <div className="analytics-box">
            <span className="analytics-box-title"><Globe size={16} /> Top Verified Domains</span>
            <div className="analytics-list">
              {data?.top_domains?.map((d, i) => (
                <div key={i} className="analytics-list-item">
                  <span>{d.domain}</span>
                  <strong>{d.count.toLocaleString()} emails</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="analytics-box">
            <span className="analytics-box-title"><Cpu size={16} /> Provider Intelligence</span>
            <div className="analytics-list">
              {data?.top_providers?.map((p, i) => (
                <div key={i} className="analytics-list-item">
                  <span>{p.provider}</span>
                  <strong>{p.percentage}%</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </WidgetWrapper>
  );
}
