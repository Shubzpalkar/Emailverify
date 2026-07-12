import { getToken } from '../firebase/auth';

// Centralized API client with Firebase bearer auth
const API_BASE = '/api';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function parseError(res) {
  let errorMsg = 'An error occurred';
  try {
    const errorData = await res.json();
    errorMsg = errorData.detail || errorMsg;
  } catch { /* ignore */ }
  return errorMsg;
}

function buildHeaders(options, token) {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  if (options.headers?.['Content-Type'] === 'application/x-www-form-urlencoded') {
    delete headers['Content-Type'];
  }

  return {
    ...headers,
    ...options.headers,
  };
}

async function request(endpoint, options, forceRefresh = false) {
  const token = await getToken(forceRefresh);
  return fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: buildHeaders(options, token),
  });
}

export async function apiCall(endpoint, options = {}) {
  let res = await request(endpoint, options);

  if (res.status === 401) {
    res = await request(endpoint, options, true);
  }

  if (!res.ok) {
    throw new ApiError(await parseError(res), res.status);
  }

  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return res.json();
  }
  return res;
}

// Superadmin API
export const getAdmins = () => apiCall('/superadmin/admins');
export const createAdmin = (data) => apiCall('/superadmin/admins', { method: 'POST', body: JSON.stringify(data) });
export const updateAdminCredits = (adminId, amount) => apiCall(`/superadmin/admins/${adminId}/credits`, { method: 'PATCH', body: JSON.stringify({ amount }) });
export const suspendAdmin = (adminId) => apiCall(`/superadmin/admins/${adminId}/suspend`, { method: 'PATCH' });
export const getAdminUsers = (adminId) => apiCall(`/superadmin/admins/${adminId}/users`);
export const getSuperadminDashboard = () => apiCall('/superadmin/dashboard');
export const getAllUsers = () => apiCall('/superadmin/users');
export const impersonateUser = (userId) => apiCall(`/superadmin/impersonate/${userId}`);

// Admin API
export const getMyUsers = () => apiCall('/admin/users');
export const createUser = (data) => apiCall('/admin/users', { method: 'POST', body: JSON.stringify(data) });
export const updateUserCredits = (userId, amount) => apiCall(`/admin/users/${userId}/credits`, { method: 'PATCH', body: JSON.stringify({ amount }) });
export const updateUserTier = (userId, tier) => apiCall(`/admin/users/${userId}/tier`, { method: 'PATCH', body: JSON.stringify({ tier }) });
export const suspendUser = (userId) => apiCall(`/admin/users/${userId}/suspend`, { method: 'PATCH' });
export const getAdminDashboard = () => apiCall('/admin/dashboard');
export const getMyJobs = () => apiCall('/admin/jobs');

// API Keys
export const getAPIKeys = () => apiCall('/settings/keys');
export const createAPIKey = (name) => apiCall('/settings/keys', { method: 'POST', body: JSON.stringify({ name }) });
export const revokeAPIKey = (keyId) => apiCall(`/settings/keys/${keyId}`, { method: 'DELETE' });

// Billing API
export const getPlans = () => apiCall('/billing/plans');
export const getBillingDashboard = () => apiCall('/billing/dashboard');
export const createCheckoutSession = (planName, creditsPack = null) => 
  apiCall('/billing/create-checkout', { 
    method: 'POST', 
    body: JSON.stringify({ plan_name: planName, credits_pack: creditsPack }) 
  });
export const verifyPayment = (checkoutSessionId, paymentId = null, subscriptionId = null) => 
  apiCall('/billing/verify-payment', { 
    method: 'POST', 
    body: JSON.stringify({ 
      checkout_session_id: checkoutSessionId, 
      dodo_payment_id: paymentId, 
      dodo_subscription_id: subscriptionId 
    }) 
  });
export const cancelSubscription = () => apiCall('/billing/cancel-subscription', { method: 'POST' });
export const getInvoices = () => apiCall('/billing/invoices');
export const getPaymentsHistory = () => apiCall('/billing/payments');
export const getCreditsData = () => apiCall('/billing/credits');
export const getCustomerPortalUrl = () => apiCall('/billing/customer-portal');
export const getAdminBillingStats = () => apiCall('/billing/admin-stats');