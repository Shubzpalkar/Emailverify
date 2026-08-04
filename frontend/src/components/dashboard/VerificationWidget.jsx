import { useState, useEffect } from 'react';
import WidgetWrapper from './WidgetWrapper';
import { getDashboardVerificationSummary } from '../../api/client';
import { ShieldCheck, CheckCircle, Warning, XCircle, Question, Trash, UserGear } from '@phosphor-icons/react';

export default function VerificationWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getDashboardVerificationSummary();
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

  const counts = data?.counts || {};
  const pcts = data?.percentages || {};

  const categories = [
    { key: 'deliverable', label: 'Deliverable (Valid)', count: counts.deliverable || 0, pct: pcts.deliverable || 0, color: '#22c55e', icon: CheckCircle },
    { key: 'protected', label: 'Protected / Risky', count: counts.protected || 0, pct: pcts.protected || 0, color: '#f59e0b', icon: Warning },
    { key: 'catch_all', label: 'Catch-All Server', count: counts.catch_all || 0, pct: pcts.catch_all || 0, color: '#8b5cf6', icon: ShieldCheck },
    { key: 'invalid', label: 'Invalid Email', count: counts.invalid || 0, pct: pcts.invalid || 0, color: '#ef4444', icon: XCircle },
    { key: 'disposable', label: 'Disposable Email', count: counts.disposable || 0, pct: pcts.disposable || 0, color: '#ec4899', icon: Trash },
    { key: 'role_based', label: 'Role-Based (admin@)', count: counts.role_based || 0, pct: pcts.role_based || 0, color: '#3b82f6', icon: UserGear },
    { key: 'unknown', label: 'Unknown Status', count: counts.unknown || 0, pct: pcts.unknown || 0, color: '#94a3b8', icon: Question }
  ];

  return (
    <WidgetWrapper
      title="Verification Status Breakdown"
      subtitle="Aggregated results category metrics"
      icon={ShieldCheck}
      permission="dashboard.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="verification-widget-card"
    >
      <div className="verification-widget-grid">
        {categories.map(cat => {
          const CatIcon = cat.icon;
          return (
            <div className="verif-cat-item" key={cat.key}>
              <div className="verif-cat-header">
                <div className="verif-cat-title">
                  <CatIcon size={18} color={cat.color} />
                  <span>{cat.label}</span>
                </div>
                <div className="verif-cat-count">
                  <strong>{cat.count.toLocaleString()}</strong>
                  <span className="verif-cat-pct">({cat.pct}%)</span>
                </div>
              </div>
              <div className="verif-cat-track">
                <div className="verif-cat-fill" style={{ width: `${Math.min(cat.pct, 100)}%`, background: cat.color }} />
              </div>
            </div>
          );
        })}
      </div>
    </WidgetWrapper>
  );
}
