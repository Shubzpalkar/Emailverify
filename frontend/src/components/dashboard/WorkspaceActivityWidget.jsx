import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardWorkspaceActivity } from '../../api/client';
import { Buildings, UserPlus, Warning, Gear } from '@phosphor-icons/react';

export default function WorkspaceActivityWidget() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardWorkspaceActivity();
      setActivities(res);
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
      title="Workspace Audit Activity"
      subtitle="Team member invites, role changes & settings events"
      icon={Buildings}
      permission="workspace.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="workspace-activity-widget-card"
    >
      <div className="activity-timeline">
        {activities.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>No recent workspace audit activities.</p>
        ) : (
          activities.map((act) => (
            <div className="timeline-item" key={act.id}>
              <div className="timeline-dot" style={{ background: 'var(--primary, #3b82f6)' }}>
                <Gear size={12} color="#fff" />
              </div>
              <div className="timeline-content">
                <strong>{act.action}</strong>
                <p>{act.details}</p>
                <span className="timeline-time">By {act.actor} • {act.timestamp ? new Date(act.timestamp).toLocaleString() : 'N/A'}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </WidgetWrapper>
  );
}
