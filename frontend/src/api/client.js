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
