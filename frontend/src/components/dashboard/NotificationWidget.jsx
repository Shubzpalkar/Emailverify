import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardNotifications } from '../../api/client';
import { Bell, Warning, CheckCircle, Info } from '@phosphor-icons/react';

export default function NotificationWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardNotifications();
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

  const notifs = data?.notifications || [];

  return (
    <WidgetWrapper
      title="Notifications & Alerts"
      subtitle="Workspace notifications and security alerts"
      icon={Bell}
      permission="notifications.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      actionButton={
        data?.unread_count > 0 ? (
          <span className="profile-badge badge-status-pending" style={{ fontSize: '0.75rem' }}>
            {data.unread_count} Unread
          </span>
        ) : null
      }
      className="notification-widget-card"
    >
      <div className="notif-list">
        {notifs.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>No unread notifications.</p>
        ) : (
          notifs.map((n) => (
            <div className={`notif-item ${n.unread ? 'unread' : ''}`} key={n.id}>
              <div className="notif-icon">
                {n.type === 'warning' ? <Warning size={18} color="#ef4444" /> :
                 n.type === 'success' ? <CheckCircle size={18} color="#22c55e" /> : <Info size={18} color="#3b82f6" />}
              </div>
              <div className="notif-body">
                <strong>{n.title}</strong>
                <p>{n.message}</p>
                <span className="notif-time">{n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </WidgetWrapper>
  );
}
