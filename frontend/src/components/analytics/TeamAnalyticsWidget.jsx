import { useState, useEffect } from 'react';
import WidgetWrapper from '../dashboard/WidgetWrapper';
import { getAnalyticsTeam } from '../../api/client';
import { Users, Trophy } from '@phosphor-icons/react';

export default function TeamAnalyticsWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await getAnalyticsTeam();
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

  const leaderboard = data?.leaderboard || [];

  return (
    <WidgetWrapper
      title="Team Member Productivity & Leaderboard"
      subtitle="Workspace user verification volume & credit efficiency ranking"
      icon={Users}
      permission="team.view"
      loading={loading}
      error={error}
      onRefresh={fetchWidgetData}
      className="team-analytics-widget-card"
    >
      <div className="profile-table-container">
        <table className="profile-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Team Member</th>
              <th>Role</th>
              <th>Jobs Executed</th>
              <th>Emails Verified</th>
              <th>Credits Consumed</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.length === 0 ? (
              <tr><td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No team member activity records found.</td></tr>
            ) : (
              leaderboard.map((member, i) => (
                <tr key={i}>
                  <td>
                    {i === 0 ? <Trophy size={18} color="#f59e0b" weight="fill" /> : <strong>#{i + 1}</strong>}
                  </td>
                  <td><strong>{member.name}</strong></td>
                  <td><span className="profile-badge">{member.role}</span></td>
                  <td>{member.jobs_count}</td>
                  <td><strong>{member.emails_verified?.toLocaleString()}</strong></td>
                  <td>{member.credits_used?.toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </WidgetWrapper>
  );
}
