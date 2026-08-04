import { ListChecks, PlayCircle, Clock, CheckCircle, XCircle, Archive, CalendarBlank, Coins } from '@phosphor-icons/react';

export default function JobSummaryCards({ summary, loading }) {
  const cards = [
    { label: 'Total Jobs', value: summary?.total_jobs ?? 0, icon: ListChecks, color: '#3b82f6' },
    { label: 'Running Jobs', value: summary?.running_jobs ?? 0, icon: PlayCircle, color: '#8b5cf6' },
    { label: 'Queued Jobs', value: summary?.queued_jobs ?? 0, icon: Clock, color: '#eab308' },
    { label: 'Completed Jobs', value: summary?.completed_jobs ?? 0, icon: CheckCircle, color: '#22c55e' },
    { label: 'Failed Jobs', value: summary?.failed_jobs ?? 0, icon: XCircle, color: '#ef4444' },
    { label: 'Archived Jobs', value: summary?.archived_jobs ?? 0, icon: Archive, color: '#94a3b8' },
    { label: "Today's Verifications", value: summary?.today_verifications ?? 0, icon: CalendarBlank, color: '#06b6d4' },
    { label: 'Credits Used Today', value: summary?.credits_used_today ?? 0, icon: Coins, color: '#f97316' }
  ];

  if (loading) {
    return (
      <div className="summary-cards-grid animate-pulse" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))' }}>
        {[...Array(8)].map((_, i) => (
          <div key={i} className="summary-card-item" style={{ height: '70px', background: 'rgba(255,255,255,0.03)' }} />
        ))}
      </div>
    );
  }

  return (
    <div className="summary-cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', marginBottom: '1.5rem' }}>
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div className="summary-card-item" key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label>{c.label}</label>
              <Icon size={18} color={c.color} />
            </div>
            <span className="metric-val" style={{ fontSize: '1.3rem' }}>{c.value.toLocaleString()}</span>
          </div>
        );
      })}
    </div>
  );
}
