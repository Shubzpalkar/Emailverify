import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check } from '@phosphor-icons/react';
import './Pricing.css';

export default function Pricing() {
  const [activeFaq, setActiveFaq] = useState(null);

  const plans = [
    {
      name: 'Free',
      price: '₹0',
      period: 'forever',
      description: 'Perfect for testing and small volume verification.',
      credits: '100 Credits',
      features: ['CSV Upload', 'Dashboard Analytics', 'Single Email Verify', 'SMTP Checking'],
      cta: 'Start Free',
      link: '/signup',
      popular: false
    },
    {
      name: 'Starter',
      price: '₹999',
      period: 'month',
      description: 'Ideal for growing startups and content creators.',
      credits: '50,000 Credits',
      features: ['Bulk Verification', 'Email Support', '99% Accuracy Guarantee', 'Dashboard Analytics'],
      cta: 'Buy Now',
      link: '/signup',
      popular: false
    },
    {
      name: 'Growth',
      price: '₹4,999',
      period: 'month',
      description: 'For teams needing high volume and API automation.',
      credits: '500,000 Credits',
      features: ['API Access', 'Priority Support', 'Team Multi-users', 'Smart Cache System'],
      cta: 'Buy Now',
      link: '/signup',
      popular: true
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: 'custom',
      description: 'Dedicated resources for large-scale operations.',
      credits: 'Unlimited Scale',
      features: ['Dedicated Support', 'Custom SLA', 'Custom Billing Options', 'On-premise Deployment'],
      cta: 'Contact Sales',
      link: 'mailto:sales@emailverif.com',
      popular: false
    }
  ];



  const faqs = [
    {
      q: 'How accurate is verification?',
      a: 'Our verification engine achieves over 99% accuracy by performing multi-step verification including MX record validation, syntax checks, and real-time SMTP connection tests.'
    },
    {
      q: 'How does SMTP verification work?',
      a: 'We connect directly to the recipient mail server and initiate an SMTP conversation without sending an actual email. This tells us whether the mailbox exists and can accept mail.'
    },
    {
      q: 'Do credits expire?',
      a: 'Free credits are provided once upon signup. Paid plan credits roll over for 12 months as long as your subscription is active, so you never lose what you bought.'
    },
    {
      q: 'Is API available?',
      a: 'Yes, API access is available starting from the Growth plan. We provide clean RESTful endpoints and generate secure API keys in the settings panel.'
    },
    {
      q: 'Is my data secure?',
      a: 'Absolutely. We do not store your verified email lists after processing. All lists are stored in a transient DuckDB database instance and automatically purged after download.'
    }
  ];

  const toggleFaq = (index) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  return (
    <div className="pricing-page page-enter">
      <div className="pricing-header">
        <span className="badge">Simple Pricing</span>
        <h1>Plans for teams of <span className="text-gradient">all sizes.</span></h1>
        <p className="subtitle">Choose the perfect plan for your cold email campaigns and newsletter list cleaning.</p>
      </div>

      {/* Pricing Cards Grid */}
      <section className="pricing-grid container">
        {plans.map((plan, idx) => (
          <div key={idx} className={`pricing-card glass-card ${plan.popular ? 'popular-card' : ''}`}>
            {plan.popular && <span className="popular-badge">Most Popular</span>}
            <div className="pricing-card-header">
              <h3>{plan.name}</h3>
              <p className="plan-desc">{plan.description}</p>
              <div className="plan-price-box">
                <span className="price-val">{plan.price}</span>
                {plan.period !== 'custom' && <span className="price-period">/{plan.period}</span>}
              </div>
              <span className="plan-credits">{plan.credits}</span>
            </div>
            
            <div className="card-body">
              <ul className="plan-features">
                {plan.features.map((feat, fIdx) => (
                  <li key={fIdx}>
                    <Check size={18} weight="bold" className="icon-check" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card-footer">
              <Link to={plan.link} className={`btn-full ${plan.popular ? 'btn-primary' : 'btn-secondary'}`}>
                {plan.cta}
              </Link>
            </div>
          </div>
        ))}
      </section>



      {/* FAQ Section */}
      <section id="faq" className="faq-section container">
        <div className="faq-header">
          <span className="badge">FAQ</span>
          <h2>Frequently Asked <span className="text-gradient">Questions</span></h2>
          <p>Everything you need to know about the product and pricing.</p>
        </div>
        <div className="faq-list">
          {faqs.map((faq, idx) => (
            <div key={idx} className="faq-item glass-card">
              <button className="faq-question" onClick={() => toggleFaq(idx)}>
                <span>{faq.q}</span>
                <span className={`faq-icon ${activeFaq === idx ? 'open' : ''}`}>+</span>
              </button>
              <div className={`faq-answer ${activeFaq === idx ? 'show' : ''}`}>
                <p>{faq.a}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

