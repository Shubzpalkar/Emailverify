import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardActivity } from '../../api/client';
import { Clock, CheckCircle, PlayCircle, StopCircle } from '@phosphor-icons/react';

export default function ActivityWidget() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardActivity();
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
      title="Recent Activity Timeline"
      subtitle="Personal verification event log"
      icon={Clock}
      permission="dashboard.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="activity-widget-card"
    >
      <div className="activity-timeline">
        {activities.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>No recent activity records.</p>
        ) : (
          activities.map((act) => (
            <div className="timeline-item" key={act.id}>
              <div className="timeline-dot" style={{
                background: act.type?.includes('Completed') ? 'var(--success, #22c55e)' :
                            act.type?.includes('Cancelled') ? 'var(--danger, #ef4444)' : 'var(--primary, #3b82f6)'
              }}>
                {act.type?.includes('Completed') ? <CheckCircle size={12} color="#fff" /> : <PlayCircle size={12} color="#fff" />}
              </div>
              <div className="timeline-content">
                <strong>{act.title}</strong>
                <p>{act.details}</p>
                <span className="timeline-time">{act.timestamp ? new Date(act.timestamp).toLocaleString() : 'Just now'}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </WidgetWrapper>
  );
}
