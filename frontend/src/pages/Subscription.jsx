import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getBillingDashboard, createCheckoutSession, getPlans } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import { 
  Check, 
  Minus, 
  Sparkle, 
  Coins, 
  ArrowLeft,
  Spinner
} from '@phosphor-icons/react';
import './Subscription.css';

export default function Subscription() {
  const { showToast } = useToast();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [currentPlan, setCurrentPlan] = useState('Free');
  const [plans, setPlans] = useState(null);
  const [buyingPlan, setBuyingPlan] = useState(null);
  const [buyingPack, setBuyingPack] = useState(null);

  useEffect(() => {
    loadPlansAndDashboard();
  }, []);

  const loadPlansAndDashboard = async () => {
    try {
      setLoading(true);
      const dashboard = await getBillingDashboard();
      setCurrentPlan(dashboard.plan || 'Free');
      
      const plansData = await getPlans();
      setPlans(plansData);
    } catch (err) {
      showToast(err.message || 'Failed to load subscription configurations', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planName) => {
    if (planName === 'Free') {
      showToast('You are already on the Free tier.', 'info');
      return;
    }
    
    try {
      setBuyingPlan(planName);
      const res = await createCheckoutSession(planName);
      
      showToast('Redirecting to secure checkout...', 'success');
      
      if (res.checkout_url.startsWith('http')) {
        window.location.href = res.checkout_url;
      } else {
        // Mock checkout route locally
        navigate(res.checkout_url);
      }
    } catch (err) {
      showToast(err.message || 'Failed to generate checkout session', 'error');
    } finally {
      setBuyingPlan(null);
    }
  };

  const handleBuyCredits = async (packName) => {
    try {
      setBuyingPack(packName);
      const res = await createCheckoutSession(null, packName);
      
      showToast('Redirecting to secure checkout...', 'success');
      
      if (res.checkout_url.startsWith('http')) {
        window.location.href = res.checkout_url;
      } else {
        // Mock checkout route locally
        navigate(res.checkout_url);
      }
    } catch (err) {
      showToast(err.message || 'Failed to initiate purchase', 'error');
    } finally {
      setBuyingPack(null);
    }
  };

  if (loading) {
    return (
      <div className="subscription-loading-container">
        <Spinner size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  // Define details matching PRD specs
  const plansDetails = [
    {
      name: 'Free',
      price: '₹0',
      period: 'forever',
      credits: '100 Credits',
      maxUpload: '1,000 emails',
      apiAccess: false,
      bulkVerification: true,
      support: 'Community',
      speed: 'Normal',
      teams: '1 User',
      cta: 'Start Free',
      features: ['100 Free Credits', 'Single Email Check', 'Bulk CSV Verification', 'Community Forum Support', 'Normal Speed Processing']
    },
    {
      name: 'Starter',
      price: '₹999',
      period: 'month',
      credits: '50,000 Credits',
      maxUpload: '100,000 emails',
      apiAccess: false,
      bulkVerification: true,
      support: 'Email Support',
      speed: 'Normal',
      teams: '1 User',
      cta: 'Upgrade Starter',
      features: ['50,000 Monthly Credits', 'Bulk File Uploads', '99.2% Accuracy Guarantee', 'Standard Email Support', 'Normal Speed Processing']
    },
    {
      name: 'Growth',
      price: '₹4,999',
      period: 'month',
      credits: '500,000 Credits',
      maxUpload: '1,000,000 emails',
      apiAccess: true,
      bulkVerification: true,
      support: 'Priority 24/7',
      speed: 'Fast (Multi-thread)',
      teams: '3 Users Allowed',
      cta: 'Upgrade Growth',
      features: ['500,000 Monthly Credits', 'Developer REST API Access', '1,000,000 max upload rows', 'Priority Helpdesk Support', 'Fast Multi-threaded Processing', 'Up to 3 Team Members'],
      popular: true
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: 'custom',
      credits: 'Unlimited Scale',
      maxUpload: 'Unlimited',
      apiAccess: true,
      bulkVerification: true,
      support: 'Dedicated Manager',
      speed: 'Instant (Multi-IP)',
      teams: 'Unlimited Users',
      cta: 'Contact Sales',
      features: ['Custom Credit Allotments', 'Unlimited CSV File Uploads', 'Full Developer API Customizations', 'Dedicated SLA Commitments', '24/7 Phone & Dedicated Manager Support', 'Unlimited Team Collaborators']
    }
  ];

  return (
    <section className="container page-enter" style={{ paddingTop: '2.5rem', paddingBottom: '5rem' }}>
      <div className="subscription-header">
        <button className="btn-back" onClick={() => navigate('/billing')}>
          <ArrowLeft size={16} /> Back to Billing
        </button>
        <span className="badge mt-2">SaaS Pricing plans</span>
        <h1 className="mt-2">Choose the <span className="text-gradient">Right Plan</span></h1>
        <p className="subtitle">Unlock limits, integrate APIs, and clean lists with enterprise speed.</p>
      </div>

      {/* Subscription cards */}
      <div className="plans-grid mt-4">
        {plansDetails.map((p) => {
          const isActive = currentPlan === p.name;
          const isEnterprise = p.name === 'Enterprise';
          const isFree = p.name === 'Free';
          
          return (
            <div key={p.name} className={`glass-card plan-card ${p.popular ? 'plan-popular' : ''} ${isActive ? 'plan-active' : ''}`}>
              {p.popular && (
                <div className="popular-tag">
                  <Sparkle size={14} weight="fill" /> MOST POPULAR
                </div>
              )}
              
              <div className="plan-name-row">
                <h3>{p.name}</h3>
                {isActive && <span className="active-badge">Active Plan</span>}
              </div>
              
              <div className="plan-price-row mt-2">
                <span className="price-number">{p.price}</span>
                {p.period !== 'forever' && p.period !== 'custom' && <span className="price-period">/{p.period}</span>}
              </div>
              
              <p className="credits-amount mt-1">{p.credits}</p>
              
              {/* Plan Action Button */}
              {isEnterprise ? (
                <a href="mailto:sales@emailverif.com" className="btn-secondary btn-full text-center mt-3">
                  Contact Sales
                </a>
              ) : isActive ? (
                <button className="btn-secondary btn-full mt-3" disabled>
                  Current Plan
                </button>
              ) : (
                <button 
                  className={`btn-full mt-3 ${p.popular ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => handleSubscribe(p.name)}
                  disabled={buyingPlan !== null}
                >
                  {buyingPlan === p.name ? (
                    <Spinner size={16} className="animate-spin mx-auto" />
                  ) : (
                    p.cta
                  )}
                </button>
              )}

              {/* Feature Specifications Table */}
              <div className="plan-specs mt-3">
                <div className="spec-row">
                  <span className="spec-label">Max Upload:</span>
                  <span className="spec-val">{p.maxUpload}</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">API Access:</span>
                  <span className="spec-val">{p.apiAccess ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">Verification Speed:</span>
                  <span className="spec-val">{p.speed}</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">Support Level:</span>
                  <span className="spec-val">{p.support}</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">Team Members:</span>
                  <span className="spec-val">{p.teams}</span>
                </div>
              </div>
              
              <hr className="divider mt-3" />
              
              <ul className="features-list mt-3">
                {p.features.map((f, idx) => (
                  <li key={idx}>
                    <Check size={16} weight="bold" className="text-success" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {/* One-Time Addons purchase */}
      <div className="credits-purchase-section mt-5">
        <div className="section-title text-center">
          <Coins size={36} weight="duotone" className="text-success" />
          <h2 className="mt-1">Need Extra Credits?</h2>
          <p className="text-muted">Purchase one-time credit topups that roll over forever.</p>
        </div>

        <div className="packs-grid mt-4">
          <div className="glass-card pack-card">
            <h4>10,000 Credits</h4>
            <div className="price-row mt-2">
              <span className="pack-price">₹299</span>
              <span className="text-muted text-sm">one-time payment</span>
            </div>
            <p className="text-muted mt-2">Ideal for quick single-list cleanup. Roll over indefinitely.</p>
            <button 
              className="btn-secondary btn-full mt-3" 
              onClick={() => handleBuyCredits('10k')}
              disabled={buyingPack !== null}
            >
              {buyingPack === '10k' ? <Spinner size={16} className="animate-spin mx-auto" /> : 'Buy 10k Credits'}
            </button>
          </div>

          <div className="glass-card pack-card featured-pack">
            <span className="best-value-badge">BEST VALUE</span>
            <h4>50,000 Credits</h4>
            <div className="price-row mt-2">
              <span className="pack-price">₹999</span>
              <span className="text-muted text-sm">one-time payment</span>
            </div>
            <p className="text-muted mt-2">Most popular choice for regular campaigns. Instant allocation.</p>
            <button 
              className="btn-primary btn-full mt-3" 
              onClick={() => handleBuyCredits('50k')}
              disabled={buyingPack !== null}
            >
              {buyingPack === '50k' ? <Spinner size={16} className="animate-spin mx-auto" /> : 'Buy 50k Credits'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
