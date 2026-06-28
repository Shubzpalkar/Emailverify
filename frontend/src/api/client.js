// Centralized API client with cookie-based auth
const API_BASE = '/api';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export async function apiCall(endpoint, options = {}) {
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  // For FormData (file upload) content-type must not be forced to json
  if (options.body instanceof FormData) {
    delete defaultHeaders['Content-Type'];
  }

  // For url-encoded data
  if (options.headers?.['Content-Type'] === 'application/x-www-form-urlencoded') {
    delete defaultHeaders['Content-Type'];
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!res.ok) {
    let errorMsg = 'An error occurred';
    try {
      const errorData = await res.json();
      errorMsg = errorData.detail || errorMsg;
    } catch (e) { /* ignore */ }
    throw new ApiError(errorMsg, res.status);
  }

  // Handle empty responses
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

// Password Reset
export const forgotPassword = (email) => apiCall('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) });
export const resetPassword = (data) => apiCall('/auth/reset-password', { method: 'POST', body: JSON.stringify(data) });

// API Keys
export const getAPIKeys = () => apiCall('/settings/keys');
export const createAPIKey = (name) => apiCall('/settings/keys', { method: 'POST', body: JSON.stringify({ name }) });
export const revokeAPIKey = (keyId) => apiCall(`/settings/keys/${keyId}`, { method: 'DELETE' });
