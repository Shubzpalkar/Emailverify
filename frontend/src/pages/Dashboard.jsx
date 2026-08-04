import WelcomeWidget from '../components/dashboard/WelcomeWidget';
import KpiWidget from '../components/dashboard/KpiWidget';
import CreditWidget from '../components/dashboard/CreditWidget';
import VerificationWidget from '../components/dashboard/VerificationWidget';
import JobsWidget from '../components/dashboard/JobsWidget';
import AnalyticsWidget from '../components/dashboard/AnalyticsWidget';
import ActivityWidget from '../components/dashboard/ActivityWidget';
import WorkspaceActivityWidget from '../components/dashboard/WorkspaceActivityWidget';
import NotificationWidget from '../components/dashboard/NotificationWidget';
import HealthWidget from '../components/dashboard/HealthWidget';
import QuickActionWidget from '../components/dashboard/QuickActionWidget';
import WorkspaceSummaryWidget from '../components/dashboard/WorkspaceSummaryWidget';
import './Dashboard.css';

export default function Dashboard() {
  return (
    <div className="dashboard-container page-enter">
      <div className="dashboard-grid">
        {/* Row 1: Welcome Header & Quick Actions */}
        <div className="col-8">
          <WelcomeWidget />
        </div>
        <div className="col-4">
          <QuickActionWidget />
        </div>

        {/* Row 2: KPI Cards */}
        <div className="col-12">
          <KpiWidget />
        </div>

        {/* Row 3: Verification Jobs & Credit Summary */}
        <div className="col-8">
          <JobsWidget />
        </div>
        <div className="col-4">
          <CreditWidget />
        </div>

        {/* Row 4: Verification Status Breakdown & Workspace Overview */}
        <div className="col-6">
          <VerificationWidget />
        </div>
        <div className="col-6">
          <WorkspaceSummaryWidget />
        </div>

        {/* Row 5: Analytics & Verification Trends */}
        <div className="col-12">
          <AnalyticsWidget />
        </div>

        {/* Row 6: Personal Activity & Workspace Audit Logs */}
        <div className="col-6">
          <ActivityWidget />
        </div>
        <div className="col-6">
          <WorkspaceActivityWidget />
        </div>

        {/* Row 7: Notifications & System Health Infrastructure */}
        <div className="col-6">
          <NotificationWidget />
        </div>
        <div className="col-6">
          <HealthWidget />
        </div>
      </div>
    </div>
  );
}
