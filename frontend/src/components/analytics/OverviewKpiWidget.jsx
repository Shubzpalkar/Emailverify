import { useState, useEffect } from 'react';
import WidgetWrapper from '../dashboard/WidgetWrapper';
import { getAnalyticsOverview } from '../../api/client';
import { EnvelopeSimple, CheckCircle, Warning, ShieldCheck, XCircle, Question, Coins, Timer, TrendUp } from '@phosphor-icons/react';

export default function OverviewKpiWidget({ timeframe }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getAnalyticsOverview(timeframe);
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

  const cards = [
    { label: 'Total Verified', value: data?.total_emails_verified?.toLocaleString() ?? '0', icon: EnvelopeSimple, color: '#3b82f6' },
    { label: 'Deliverable %', value: `${data?.deliverable_percentage ?? 0}%`, icon: CheckCircle, color: '#22c55e' },
    { label: 'Protected %', value: `${data?.protected_percentage ?? 0}%`, icon: Warning, color: '#f59e0b' },
    { label: 'Catch-All %', value: `${data?.catch_all_percentage ?? 0}%`, icon: ShieldCheck, color: '#8b5cf6' },
    { label: 'Invalid %', value: `${data?.invalid_percentage ?? 0}%`, icon: XCircle, color: '#ef4444' },
    { label: 'Unknown %', value: `${data?.unknown_percentage ?? 0}%`, icon: Question, color: '#94a3b8' },
    { label: 'Credits Used', value: data?.credits_used?.toLocaleString() ?? '0', icon: Coins, color: '#f97316' },
    { label: 'Avg Verification Speed', value: `${data?.avg_verification_time_ms ?? 0} ms`, icon: Timer, color: '#ec4899' },
    { label: 'Monthly Growth', value: `+${data?.monthly_growth ?? 0}%`, icon: TrendUp, color: '#10b981' }
  ];

  return (
    <WidgetWrapper
      title="Executive BI Overview"
      subtitle="Aggregated verification volume, quality ratios & growth"
      icon={TrendUp}
      permission="analytics.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="overview-kpi-widget-card"
    >
      <div className="kpi-grid-container" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div className="kpi-card-item" key={i}>
              <div className="kpi-icon-box" style={{ background: `rgba(255,255,255,0.05)`, color: c.color }}>
                <Icon size={20} />
              </div>
              <div className="kpi-info">
                <span className="kpi-label">{c.label}</span>
                <span className="kpi-value">{c.value}</span>
              </div>
            </div>
          );
        })}
      </div>
    </WidgetWrapper>
  );
}
