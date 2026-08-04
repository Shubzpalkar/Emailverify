import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardCredits } from '../../api/client';
import { Coins, Warning, Sparkle } from '@phosphor-icons/react';
import { Link } from 'react-router-dom';

export default function CreditWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardCredits();
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
      title="Credit Allocation & Usage"
      subtitle="Workspace credit pool metrics"
      icon={Coins}
      permission="credits.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      actionButton={
        <Link to="/billing" className="btn-primary btn-small">
          <Sparkle size={14} /> Buy Credits
        </Link>
      }
    >
      <div className="credit-widget-content">
        <div className="credit-stat-row">
          <div>
            <span className="stat-num">{data?.remaining_credits?.toLocaleString() ?? 0}</span>
            <span className="stat-sub">Remaining Credits</span>
          </div>
          <div>
            <span className="stat-num">{data?.used_credits?.toLocaleString() ?? 0}</span>
            <span className="stat-sub">Used Credits</span>
          </div>
          <div>
            <span className="stat-num">{data?.total_credits?.toLocaleString() ?? 0}</span>
            <span className="stat-sub">Total Allotted</span>
          </div>
        </div>

        <div className="credit-progress-bar-wrapper">
          <div className="progress-label">
            <span>Pool Capacity Remaining</span>
            <span>{data?.percent_remaining ?? 100}%</span>
          </div>
          <div className="progress-track">
            <div
              className={`progress-fill ${data?.is_low ? 'low-alert' : ''}`}
              style={{ width: `${Math.min(data?.percent_remaining ?? 100, 100)}%` }}
            />
          </div>
        </div>

        {data?.is_low && (
          <div className="credit-low-warning">
            <Warning size={18} color="#ef4444" />
            <span>Low Credit Alert! Credits are below threshold ({data.low_credit_threshold}).</span>
          </div>
        )}
      </div>
    </WidgetWrapper>
  );
}
