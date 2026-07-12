import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getInvoices } from '../api/client';
import { useToast } from '../components/Toast';
import { 
  ArrowLeft, 
  DownloadSimple, 
  Spinner, 
  FileText,
  CheckCircle
} from '@phosphor-icons/react';
import './Invoices.css';

export default function Invoices() {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [invoices, setInvoices] = useState([]);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const data = await getInvoices();
      setInvoices(data);
    } catch (err) {
      showToast(err.message || 'Failed to load invoices', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = (invoiceId) => {
    window.open(`/api/billing/invoices/${invoiceId}/download`, '_blank');
  };

  if (loading) {
    return (
      <div className="invoices-loading">
        <Spinner size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  return (
    <section className="container page-enter" style={{ paddingTop: '2.5rem', paddingBottom: '4rem' }}>
      <div className="invoices-header">
        <button className="btn-back" onClick={() => navigate('/billing')}>
          <ArrowLeft size={16} /> Back to Billing
        </button>
        <span className="badge mt-2">Billed Invoices</span>
        <h1 className="mt-2">My <span className="text-gradient">Invoices</span></h1>
        <p className="subtitle">Download historical invoices and review tax details.</p>
      </div>

      <div className="glass-card table-card mt-4">
        <div className="table-responsive">
          <table className="invoices-table">
            <thead>
              <tr>
                <th>Invoice Number</th>
                <th>Invoice Date</th>
                <th>Plan Name</th>
                <th>Subtotal</th>
                <th>Tax (18% GST)</th>
                <th>Total Amount</th>
                <th>Status</th>
                <th className="text-right">Download</th>
              </tr>
            </thead>
            <tbody>
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-4 text-muted">
                    <FileText size={40} className="mx-auto text-muted mb-2 opacity-50" />
                    No invoices generated yet.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => {
                  const subtotal = inv.amount - inv.tax;
                  return (
                    <tr key={inv.id}>
                      <td className="font-semibold text-primary">{inv.invoice_number}</td>
                      <td>{new Date(inv.billing_date).toLocaleDateString()}</td>
                      <td>{inv.plan_name}</td>
                      <td>₹{subtotal.toFixed(2)}</td>
                      <td>₹{inv.tax.toFixed(2)}</td>
                      <td className="font-semibold text-gradient">₹{inv.amount.toLocaleString()}</td>
                      <td>
                        <span className="status-badge status-completed">
                          <CheckCircle size={14} className="mr-1" />
                          {inv.status}
                        </span>
                      </td>
                      <td className="text-right">
                        <button 
                          className="btn-icon" 
                          onClick={() => handleDownloadPdf(inv.id)}
                          title="Download PDF Invoice"
                        >
                          <DownloadSimple size={18} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
