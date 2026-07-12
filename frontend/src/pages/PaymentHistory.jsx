import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPaymentsHistory } from '../api/client';
import { useToast } from '../components/Toast';
import { 
  ArrowLeft, 
  DownloadSimple, 
  Spinner, 
  MagnifyingGlass, 
  Funnel,
  CheckCircle,
  Clock,
  XCircle
} from '@phosphor-icons/react';
import './PaymentHistory.css';

export default function PaymentHistory() {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [payments, setPayments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      setLoading(true);
      const data = await getPaymentsHistory();
      setPayments(data);
    } catch (err) {
      showToast(err.message || 'Failed to load transaction history', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Search and Filter Logic
  const filteredPayments = payments.filter((p) => {
    const matchesSearch = 
      (p.transaction_id && p.transaction_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (p.plan && p.plan.toLowerCase().includes(searchQuery.toLowerCase()));
      
    const matchesStatus = 
      statusFilter === 'ALL' || 
      p.status.toUpperCase() === statusFilter;
      
    return matchesSearch && matchesStatus;
  });

  // Pagination Logic
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentPayments = filteredPayments.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredPayments.length / itemsPerPage);

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  const handleDownloadInvoice = (invoiceId) => {
    if (!invoiceId) {
      showToast('Invoice PDF not available for this record', 'error');
      return;
    }
    // Opens print view of invoice PDF in a new tab
    window.open(`/api/billing/invoices/${invoiceId}/download`, '_blank');
  };

  if (loading) {
    return (
      <div className="payment-history-loading">
        <Spinner size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  return (
    <section className="container page-enter" style={{ paddingTop: '2.5rem', paddingBottom: '4rem' }}>
      <div className="payment-history-header">
        <button className="btn-back" onClick={() => navigate('/billing')}>
          <ArrowLeft size={16} /> Back to Billing
        </button>
        <span className="badge mt-2">Transaction Logs</span>
        <h1 className="mt-2">Payment <span className="text-gradient">History</span></h1>
        <p className="subtitle">Audit all ledger transactions, orders, and payment statuses.</p>
      </div>

      {/* Search & Filter Bar */}
      <div className="filter-bar mt-4">
        <div className="search-input-wrapper">
          <MagnifyingGlass size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search by Transaction ID or Plan..." 
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1); // reset to page 1
            }}
          />
        </div>
        
        <div className="filter-select-wrapper">
          <Funnel size={18} className="filter-icon" />
          <select 
            value={statusFilter} 
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="PENDING">Pending</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {/* Transaction Table */}
      <div className="glass-card table-card mt-3">
        <div className="table-responsive">
          <table className="payments-table">
            <thead>
              <tr>
                <th>Payment Date</th>
                <th>Transaction ID</th>
                <th>Plan/Details</th>
                <th>Amount</th>
                <th>Status</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentPayments.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-4 text-muted">
                    No transactions found matching your criteria.
                  </td>
                </tr>
              ) : (
                currentPayments.map((p, idx) => (
                  <tr key={idx}>
                    <td>{new Date(p.payment_date).toLocaleDateString()}</td>
                    <td className="font-mono text-sm">{p.transaction_id || 'N/A'}</td>
                    <td>{p.plan}</td>
                    <td className="font-semibold">
                      {p.currency === 'INR' ? '₹' : p.currency} {p.amount.toLocaleString()}
                    </td>
                    <td>
                      <span className={`status-badge status-${p.status.toLowerCase()}`}>
                        {p.status.toLowerCase() === 'completed' && <CheckCircle size={14} className="mr-1" />}
                        {p.status.toLowerCase() === 'pending' && <Clock size={14} className="mr-1" />}
                        {p.status.toLowerCase() === 'failed' && <XCircle size={14} className="mr-1" />}
                        {p.status}
                      </span>
                    </td>
                    <td className="text-right">
                      {p.status.toLowerCase() === 'completed' ? (
                        <button 
                          className="btn-icon" 
                          title="Download Invoice"
                          onClick={() => handleDownloadInvoice(p.invoice_id)}
                        >
                          <DownloadSimple size={18} />
                        </button>
                      ) : (
                        <span className="text-muted text-sm">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="pagination mt-4">
          <button 
            className="pagination-btn" 
            disabled={currentPage === 1}
            onClick={() => handlePageChange(currentPage - 1)}
          >
            Prev
          </button>
          
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button 
              key={page} 
              className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
              onClick={() => handlePageChange(page)}
            >
              {page}
            </button>
          ))}
          
          <button 
            className="pagination-btn" 
            disabled={currentPage === totalPages}
            onClick={() => handlePageChange(currentPage + 1)}
          >
            Next
          </button>
        </div>
      )}
    </section>
  );
}
