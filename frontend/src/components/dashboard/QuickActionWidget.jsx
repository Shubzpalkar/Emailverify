import WidgetWrapper from './WidgetWrapper';
import { Lightning, EnvelopeSimple, Key, Users, Gear, TrendUp } from '@phosphor-icons/react';
import { Link } from 'react-router-dom';
import { PermissionGuard } from '../../context/PermissionContext';

export default function QuickActionWidget() {
  return (
    <WidgetWrapper
      title="Quick Actions"
      subtitle="Command shortcuts for key workflows"
      icon={Lightning}
      permission="dashboard.view"
      className="quick-actions-widget-card"
    >
      <div className="quick-actions-grid">
        <Link to="/verify" className="quick-action-item">
          <div className="qa-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>
            <EnvelopeSimple size={20} />
          </div>
          <span>Bulk Verification</span>
        </Link>

        <Link to="/verify" className="quick-action-item">
          <div className="qa-icon" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>
            <EnvelopeSimple size={20} />
          </div>
          <span>Single Verification</span>
        </Link>

        <PermissionGuard permission="api.view">
          <Link to="/settings/keys" className="quick-action-item">
            <div className="qa-icon" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#fde047' }}>
              <Key size={20} />
            </div>
            <span>API Keys</span>
          </Link>
        </PermissionGuard>

        <PermissionGuard permission="team.view">
          <Link to="/account/team" className="quick-action-item">
            <div className="qa-icon" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80' }}>
              <Users size={20} />
            </div>
            <span>Team Members</span>
          </Link>
        </PermissionGuard>

        <PermissionGuard permission="workspace.settings">
          <Link to="/account/workspace-settings" className="quick-action-item">
            <div className="qa-icon" style={{ background: 'rgba(236, 72, 153, 0.15)', color: '#f472b6' }}>
              <Gear size={20} />
            </div>
            <span>Workspace Settings</span>
          </Link>
        </PermissionGuard>
      </div>
    </WidgetWrapper>
  );
}
