import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardWelcome } from '../../api/client';
import { HandWaving, Sparkle, UserCircle, Buildings, Clock } from '@phosphor-icons/react';

export default function WelcomeWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardWelcome();
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
      title="Command Center"
      icon={HandWaving}
      permission="dashboard.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="welcome-widget-card"
    >
      <div className="welcome-content">
        <h2>Welcome back, {data?.user_name || 'User'}!</h2>
        <p className="welcome-desc">
          Managing <strong>{data?.workspace_name || 'Workspace'}</strong> Command Center
        </p>

        <div className="welcome-tags">
          <span className="badge-item role-badge">
            <UserCircle size={14} /> {data?.role}
          </span>
          <span className="badge-item plan-badge">
            <Sparkle size={14} /> {data?.plan} Plan
          </span>
          <span className="badge-item workspace-badge">
            <Buildings size={14} /> {data?.workspace_name}
          </span>
          {data?.last_login && (
            <span className="badge-item time-badge">
              <Clock size={14} /> Last Login: {new Date(data.last_login).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>
      </div>
    </WidgetWrapper>
  );
}
