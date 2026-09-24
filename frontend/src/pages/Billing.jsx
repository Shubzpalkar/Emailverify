import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  getBillingDashboard, 
  cancelSubscription, 
  verifyPayment, 
  getCustomerPortalUrl 
} from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import { 
  CreditCard, 
  CheckCircle, 
  Clock, 
  ArrowUpRight, 
  Coins, 
  ChartBar,
  ShieldCheck,
  XCircle,
  Spinner
} from '@phosphor-icons/react';
import './Billing.css';

export default function Billing() {
  const { showToast } = useToast();
  const { checkAuth } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [verifyingPayment, setVerifyingPayment] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    const isMock = searchParams.get('mock_checkout');
    
    if (sessionId) {
      handleVerifyPayment(sessionId);
    } else {
      loadBillingDashboard();
    }
  }, [searchParams]);

  const loadBillingDashboard = async () => {
    try {
      setLoading(true);
      const data = await getBillingDashboard();
      setDashboardData(data);
    } catch (err) {
      showToast(err.message || 'Failed to load billing metrics', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyPayment = async (sessionId) => {
    try {
      setVerifyingPayment(true);
      showToast('Verifying payment and allocating credits...', 'info');
      
      // Call backend to verify and apply credits
      const res = await verifyPayment(sessionId);
      
      showToast('Payment verified successfully! Credits added.', 'success');
      
      // Refresh Auth Context to update credits in Navbar
      await checkAuth();
      
      // Clean query params
      setSearchParams({});
    } catch (err) {
      showToast(err.message || 'Payment verification failed', 'error');
      setSearchParams({});
      loadBillingDashboard();
    } finally {
      setVerifyingPayment(false);
    }
  };

  const handleCancelSub = async () => {
    try {
      setCancelling(true);
      await cancelSubscription();
      showToast('Subscription cancelled successfully.');
      setShowCancelModal(false);
      await checkAuth();
      loadBillingDashboard();
    } catch (err) {
      showToast(err.message || 'Failed to cancel subscription', 'error');
    } finally {
      setCancelling(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      showToast('Opening billing portal...', 'info');
      const res = await getCustomerPortalUrl();
      if (res.portal_url.startsWith('http')) {
        window.open(res.portal_url, '_blank');
      } else {
        // Mock portal
        showToast('Redirected to local billing summary.');
      }
    } catch (err) {
      showToast(err.message || 'Failed to load portal URL', 'error');
    }
  };

  if (verifyingPayment) {
    return (
      <div className="billing-loading-container page-enter">
        <div className="glass-card loading-card text-center">
          <Spinner size={64} className="animate-spin text-gradient-primary" />
          <h2 className="mt-4">Verifying Transaction</h2>
          <p className="text-muted mt-2">Please do not refresh or close this tab. We are allocating your credits.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="billing-loading-container">
        <Spinner size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  const { plan, status, credits_remaining, credits_used_this_month, auto_renew, expiry_date } = dashboardData || {};

  return (
    <section className="container page-enter" style={{ paddingTop: '2.5rem', paddingBottom: '4rem' }}>
      <div className="billing-header">
        <div>
          <span className="badge">Billing Portal</span>
          <h1 className="mt-2">Subscription & <span className="text-gradient">Billing</span></h1>
          <p className="subtitle">Manage subscription tiers, credit allocations, and billing settings.</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary btn-small" onClick={() => navigate('/payment-history')}>
            <Clock size={16} className="mr-1" /> History
          </button>
          <button className="btn-secondary btn-small" onClick={() => navigate('/invoices')}>
            <ShieldCheck size={16} className="mr-1" /> Invoices
          </button>
        </div>
      </div>

      {/* Metric Summaries Grid */}
      <div className="billing-grid mt-4">
        {/* Plan card */}
        <div className="glass-card metric-card">
          <div className="metric-icon plan-icon">
            <CreditCard size={28} weight="duotone" />
          </div>
          <div className="metric-info">
            <span className="metric-label">Current Subscription</span>
            <div className="plan-badge-row mt-1">
              <h3>{plan}</h3>
              <span className={`status-pill ${status === 'active' ? 'status-active' : 'status-inactive'}`}>
                {status === 'active' ? 'Active' : 'Expired'}
              </span>
            </div>
            <p className="text-muted text-sm mt-2">
              {expiry_date ? `Expires/Renews on: ${new Date(expiry_date).toLocaleDateString()}` : 'No expiration date'}
            </p>
          </div>
        </div>

        {/* Credits Remaining Card */}
        <div
          className="glass-card metric-card"
          onClick={() => navigate('/credits')}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              navigate('/credits');
            }
          }}
          role="link"
          tabIndex="0"
          style={{ cursor: 'pointer' }}
        >
          <div className="metric-icon credits-icon">
            <Coins size={28} weight="duotone" />
          </div>
          <div className="metric-info">
            <span className="metric-label">Credits Remaining</span>
            <h2 className="mt-1 text-gradient">{credits_remaining?.toLocaleString() || 0}</h2>
            <p className="text-muted text-sm mt-2">Click to view transactions ledger</p>
          </div>
        </div>

        {/* Usage This Month */}
        <div className="glass-card metric-card">
          <div className="metric-icon usage-icon">
            <ChartBar size={28} weight="duotone" />
          </div>
          <div className="metric-info">
            <span className="metric-label">Used This Month</span>
            <h2 className="mt-1 text-muted">{credits_used_this_month?.toLocaleString() || 0}</h2>
            <p className="text-muted text-sm mt-2">Based on checks in the last 30 days</p>
          </div>
        </div>
      </div>

      {/* Auto-renew section */}
      <div className="glass-card billing-action-card mt-4">
        <div className="action-card-info">
          <h4>Subscription Actions</h4>
          <p className="text-muted text-sm mt-1">
            Auto Renewal is currently: <strong>{auto_renew ? 'Enabled' : 'Disabled'}</strong>
          </p>
        </div>
        <div className="action-buttons">
          <button className="btn-primary" onClick={() => navigate('/subscription')}>
            Upgrade Plan <ArrowUpRight size={16} className="ml-1" />
          </button>
          {status === 'active' && plan !== 'Free' && (
            <button className="btn-secondary text-danger" onClick={() => setShowCancelModal(true)}>
              Cancel Subscription
            </button>
          )}
          <button className="btn-secondary" onClick={handleManageSubscription}>
            Manage Subscription
          </button>
        </div>
      </div>

      {/* Cancel Subscription Confirmation Modal */}
      {showCancelModal && (
        <div className="modal-overlay">
          <div className="glass-card modal-content text-center" role="dialog" aria-modal="true" aria-labelledby="cancel-subscription-title">
            <XCircle size={64} className="text-danger mx-auto" />
            <h3 id="cancel-subscription-title" className="mt-4">Cancel Subscription</h3>
            <p className="text-muted mt-2">
              Are you sure you want to cancel your auto renewal? You will retain access to your plan and credit balance until the end of the current billing cycle.
            </p>
            <div className="modal-actions mt-4">
              <button className="btn-secondary" onClick={() => setShowCancelModal(false)}>
                Keep Plan
              </button>
              <button className="btn-primary btn-danger" onClick={handleCancelSub} disabled={cancelling}>
                {cancelling ? <Spinner className="animate-spin" /> : 'Yes, Cancel Renewal'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
