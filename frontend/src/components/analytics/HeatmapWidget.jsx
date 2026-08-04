import { useState, useEffect } from 'react';
import WidgetWrapper from '../dashboard/WidgetWrapper';
import { getAnalyticsHeatmaps } from '../../api/client';
import { CalendarBlank } from '@phosphor-icons/react';

export default function HeatmapWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getAnalyticsHeatmaps();
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

  const matrix = data?.matrix || [];

  return (
    <WidgetWrapper
      title="24x7 Verification Activity Heatmap"
      subtitle="Peak verification traffic & schedule intensity matrix"
      icon={CalendarBlank}
      permission="analytics.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="heatmap-widget-card"
    >
      <div className="heatmap-matrix-wrapper" style={{ overflowX: 'auto' }}>
        <table className="heatmap-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
          <thead>
            <tr>
              <th style={{ padding: '4px', color: 'var(--text-muted)' }}>Day</th>
              {[...Array(24)].map((_, h) => (
                <th key={h} style={{ padding: '4px', color: 'var(--text-muted)', textAlign: 'center' }}>{h}h</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={i}>
                <td style={{ padding: '4px', fontWeight: 600, color: 'var(--text-muted)' }}>{row.day}</td>
                {row.hours.map((val, h) => {
                  const opacity = Math.max(val / 100, 0.08);
                  return (
                    <td key={h} style={{ padding: '2px' }}>
                      <div
                        style={{
                          height: '20px',
                          borderRadius: '4px',
                          background: `rgba(59, 130, 246, ${opacity})`,
                          border: '1px solid rgba(255,255,255,0.04)'
                        }}
                        title={`${row.day} @ ${h}:00 - Activity Score: ${val}`}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </WidgetWrapper>
  );
}
