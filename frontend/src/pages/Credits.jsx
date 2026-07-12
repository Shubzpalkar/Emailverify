import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCreditsData } from '../api/client';
import { useToast } from '../components/Toast';
import { 
  ArrowLeft, 
  Coins, 
  ChartBar, 
  Clock, 
  ArrowUp, 
  ArrowDown, 
  Spinner,
  ArrowUpRight
} from '@phosphor-icons/react';
import './Credits.css';

export default function Credits() {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [creditsData, setCreditsData] = useState(null);

  useEffect(() => {
    loadCreditsData();
  }, []);

  const loadCreditsData = async () => {
    try {
      setLoading(true);
      const data = await getCreditsData();
      setCreditsData(data);
    } catch (err) {
      showToast(err.message || 'Failed to load credits history', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="credits-loading">
        <Spinner size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  const { current_credits, credits_purchased, credits_consumed, credits_remaining, transactions } = creditsData || {};

  return (
    <section className="container page-enter" style={{ paddingTop: '2.5rem', paddingBottom: '4rem' }}>
      <div className="credits-header">
        <button className="btn-back" onClick={() => navigate('/billing')}>
          <ArrowLeft size={16} /> Back to Billing
        </button>
        <span className="badge mt-2">Credit Ledger</span>
        <h1 className="mt-2">Credits & <span className="text-gradient">Transactions</span></h1>
        <p className="subtitle">Track credit balances, top-ups, usage logs, and transactional records.</p>
      </div>

      {/* Credit Summary Cards */}
      <div className="credits-summary-grid mt-4">
        {/* Current Balance */}
        <div className="glass-card summary-card">
          <div className="summary-card-icon current-icon">
            <Coins size={28} weight="duotone" />
          </div>
          <div className="summary-card-info">
            <span className="summary-card-label">Current Balance</span>
            <h2 className="mt-1 text-gradient">{current_credits?.toLocaleString() || 0}</h2>
            <p className="text-muted text-sm mt-1">Available for immediate verification jobs</p>
          </div>
        </div>

        {/* Total Purchased */}
        <div className="glass-card summary-card">
          <div className="summary-card-icon purchased-icon">
            <ArrowUp size={28} weight="bold" />
          </div>
          <div className="summary-card-info">
            <span className="summary-card-label">Credits Allocated</span>
            <h2 className="mt-1 text-success">+{credits_purchased?.toLocaleString() || 0}</h2>
            <p className="text-muted text-sm mt-1">Total credits purchased + plan allotments</p>
          </div>
        </div>

        {/* Total Consumed */}
        <div className="glass-card summary-card">
          <div className="summary-card-icon consumed-icon">
            <ArrowDown size={28} weight="bold" />
          </div>
          <div className="summary-card-info">
            <span className="summary-card-label">Credits Consumed</span>
            <h2 className="mt-1 text-danger">-{credits_consumed?.toLocaleString() || 0}</h2>
            <p className="text-muted text-sm mt-1">Total credits spent on verification processes</p>
          </div>
        </div>
      </div>

      {/* Credit warning or topup prompt */}
      <div className="glass-card credits-warning-card mt-4">
        <div className="warning-card-info">
          <h4>Low on credits?</h4>
          <p className="text-muted text-sm mt-1">
            Top up your balance instantly with one-time packs starting from ₹299. No recurring fees.
          </p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/subscription')}>
          Buy Credits Pack <ArrowUpRight size={16} className="ml-1" />
        </button>
      </div>

      {/* Credit Transaction History */}
      <div className="mt-5">
        <div className="section-header-row mb-3">
          <Clock size={20} className="text-primary mr-1" />
          <h3>Recent Transactions</h3>
        </div>
        
        <div className="glass-card table-card">
          <div className="table-responsive">
            <table className="credits-table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Transaction ID</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th className="text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {!transactions || transactions.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center py-4 text-muted">
                      No credit transactions recorded yet.
                    </td>
                  </tr>
                ) : (
                  transactions.map((t) => (
                    <tr key={t.id}>
                      <td>{new Date(t.date).toLocaleString()}</td>
                      <td className="font-mono text-sm">{t.id.slice(0, 18)}...</td>
                      <td>
                        <span className={`type-badge type-${t.type.toLowerCase()}`}>
                          {t.type}
                        </span>
                      </td>
                      <td>{t.description}</td>
                      <td className={`font-semibold text-right ${t.amount >= 0 ? 'text-success' : 'text-danger'}`}>
                        {t.amount >= 0 ? `+${t.amount.toLocaleString()}` : t.amount.toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
