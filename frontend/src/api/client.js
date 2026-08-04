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
  const controller = new AbortController();
  const timeoutMs = options.timeout || 30000;
  const id = setTimeout(() => controller.abort(new Error('Request timed out')), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      credentials: 'include',
      headers: buildHeaders(options, token),
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    if (error.name === 'AbortError' || error.message?.includes('aborted')) {
      throw new ApiError('Request timed out. Please check your connection and try again.', 408);
    }
    throw error;
  }
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

// Workspace API
export const getWorkspace = () => apiCall('/workspace');
export const updateWorkspace = (data) => apiCall('/workspace', { method: 'PUT', body: JSON.stringify(data) });
export const getWorkspaceSettings = () => apiCall('/workspace/settings');
export const updateWorkspaceSettings = (data) => apiCall('/workspace/settings', { method: 'PUT', body: JSON.stringify(data) });
export const getFullWorkspaceSettings = () => apiCall('/workspace/full-settings');
export const updateWorkspaceGeneral = (data) => apiCall('/workspace/general', { method: 'PUT', body: JSON.stringify(data) });
export const uploadWorkspaceLogo = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiCall('/workspace/branding/logo', { method: 'POST', body: formData });
};
export const updateWorkspaceBranding = (data) => apiCall('/workspace/branding', { method: 'PUT', body: JSON.stringify(data) });
export const updateWorkspaceVerificationSettings = (data) => apiCall('/workspace/verification-settings', { method: 'PUT', body: JSON.stringify(data) });
export const updateWorkspaceNotificationSettings = (data) => apiCall('/workspace/notification-settings', { method: 'PUT', body: JSON.stringify(data) });
export const updateWorkspaceSecuritySettings = (data) => apiCall('/workspace/security-settings', { method: 'PUT', body: JSON.stringify(data) });
export const forceLogoutWorkspaceUsers = () => apiCall('/workspace/force-logout-all', { method: 'POST' });
export const getWorkspaceTeamSummary = () => apiCall('/workspace/team-summary');
export const getWorkspaceCreditSummary = () => apiCall('/workspace/credit-summary');
export const getWorkspaceAuditSummary = () => apiCall('/workspace/audit-summary');
export const deleteWorkspaceDanger = (data) => apiCall('/workspace/delete-danger', { method: 'DELETE', body: JSON.stringify(data) });

// Team Members API
export const getTeamMembers = (params) => {
  const query = new URLSearchParams(params).toString();
  return apiCall(`/members?${query}`);
};
export const addTeamMember = (data) => apiCall('/members', { method: 'POST', body: JSON.stringify(data) });
export const updateTeamMember = (id, data) => apiCall(`/members/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const removeTeamMember = (id) => apiCall(`/members/${id}`, { method: 'DELETE' });

// Invitation API
export const inviteTeamMember = (data) => apiCall('/members/invite', { method: 'POST', body: JSON.stringify(data) });
export const resendInvite = (id) => apiCall(`/members/resend/${id}`, { method: 'POST' });
export const cancelInvite = (id) => apiCall(`/members/invite/${id}`, { method: 'DELETE' });
export const validateInvite = (token) => apiCall(`/members/invite/validate/${token}`);
export const acceptInvite = (token, data) => apiCall(`/members/invite/${token}/accept`, { method: 'POST', body: JSON.stringify(data) });

// User Profile API
export const getProfile = () => apiCall('/profile');
export const updateProfile = (data) => apiCall('/profile', { method: 'PUT', body: JSON.stringify(data) });
export const uploadAvatar = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiCall('/profile/avatar', { method: 'POST', body: formData });
};
export const getPreferences = () => apiCall('/profile/preferences');
export const updatePreferences = (data) => apiCall('/profile/preferences', { method: 'PUT', body: JSON.stringify(data) });
export const getSessions = () => apiCall('/profile/sessions');
export const revokeSession = (sessionId) => apiCall(`/profile/sessions/${sessionId}`, { method: 'DELETE' });
export const getLoginHistory = () => apiCall('/profile/login-history');
export const recordPasswordChange = () => apiCall('/profile/change-password', { method: 'POST' });