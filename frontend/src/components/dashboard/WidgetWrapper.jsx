import { PermissionGuard } from '../../context/PermissionContext';
import { ArrowClockwise, WarningCircle } from '@phosphor-icons/react';

export default function WidgetWrapper({
  title,
  subtitle,
  icon: Icon,
  permission,
  loading,
  error,
  onRefresh,
  children,
  className = '',
  actionButton = null
}) {
  const content = (
    <div className={`widget-card glass-card ${className}`}>
      <div className="widget-header">
        <div className="widget-title-group">
          {Icon && <Icon size={22} className="widget-icon" />}
          <div>
            <h3>{title}</h3>
            {subtitle && <p className="widget-subtitle">{subtitle}</p>}
          </div>
        </div>

        <div className="widget-actions">
          {actionButton}
          {onRefresh && (
            <button
              className="widget-refresh-btn"
              onClick={onRefresh}
              disabled={loading}
              title="Refresh widget data"
            >
              <ArrowClockwise size={16} className={loading ? 'spinning' : ''} />
            </button>
          )}
        </div>
      </div>

      <div className="widget-body">
        {loading ? (
          <div className="widget-skeleton">
            <div className="skeleton-line full" />
            <div className="skeleton-line half" />
            <div className="skeleton-line three-quarter" />
          </div>
        ) : error ? (
          <div className="widget-error-state">
            <WarningCircle size={28} color="var(--danger, #ef4444)" />
            <p>Unable to load widget data</p>
            {onRefresh && (
              <button className="btn-secondary btn-small" onClick={onRefresh}>
                Retry
              </button>
            )}
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );

  if (permission) {
    return <PermissionGuard permission={permission}>{content}</PermissionGuard>;
  }

  return content;
}
