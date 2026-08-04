import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardWorkspaceSummary } from '../../api/client';
import { Buildings, Users, Sparkle, Coins } from '@phosphor-icons/react';
import { Link } from 'react-router-dom';

export default function WorkspaceSummaryWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardWorkspaceSummary();
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
      title="Workspace Summary"
      subtitle="Organization profile & active team pool"
      icon={Buildings}
      permission="workspace.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      actionButton={
        <Link to="/account/workspace" className="btn-secondary btn-small">
          Manage
        </Link>
      }
      className="workspace-summary-widget-card"
    >
      <div className="ws-summary-content">
        <div className="ws-sum-row">
          <label>Workspace Name</label>
          <strong>{data?.workspace_name || 'My Workspace'}</strong>
        </div>
        <div className="ws-sum-row">
          <label>Company</label>
          <span>{data?.company_name || 'My Company'}</span>
        </div>
        <div className="ws-sum-row">
          <label>Active Plan</label>
          <span className="profile-badge badge-plan">
            <Sparkle size={12} /> {data?.plan || 'Free'}
          </span>
        </div>
        <div className="ws-sum-row">
          <label>Team Members</label>
          <span style={{ fontWeight: 600 }}><Users size={14} /> {data?.members || 1} Members</span>
        </div>
        <div className="ws-sum-row">
          <label>Credits Remaining</label>
          <span style={{ fontWeight: 600, color: 'var(--primary, #3b82f6)' }}>
            <Coins size={14} /> {data?.credits?.toLocaleString() ?? 0}
          </span>
        </div>
      </div>
    </WidgetWrapper>
  );
}
