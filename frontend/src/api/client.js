/**
 * Reusable HTTP API Client using fetch with JWT support and automatic token refresh.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

async function request(endpoint, options = {}, isRetry = false) {
  const url = `${BASE_URL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const token = localStorage.getItem('token');
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    credentials: 'include',
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    let data = null;

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      // If 401 Unauthorized, not a refresh endpoint, and not already retried
      if (
        response.status === 401 &&
        !isRetry &&
        !endpoint.includes('auth/login') &&
        !endpoint.includes('auth/refresh')
      ) {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          if (isRefreshing) {
            return new Promise((resolve, reject) => {
              failedQueue.push({ resolve, reject });
            }).then((newToken) => {
              options.headers = {
                ...(options.headers || {}),
                Authorization: `Bearer ${newToken}`,
              };
              return request(endpoint, options, true);
            });
          }

          isRefreshing = true;

          try {
            const refreshUrl = `${BASE_URL.replace(/\/$/, '')}/auth/refresh/`;
            const refreshRes = await fetch(refreshUrl, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh: refreshToken }),
            });

            if (refreshRes.ok) {
              const refreshData = await refreshRes.json();
              const newToken = refreshData.access;
              localStorage.setItem('token', newToken);
              processQueue(null, newToken);
              isRefreshing = false;

              options.headers = {
                ...(options.headers || {}),
                Authorization: `Bearer ${newToken}`,
              };
              return request(endpoint, options, true);
            } else {
              // Refresh failed
              processQueue(new Error('Session expired'), null);
              isRefreshing = false;
              localStorage.removeItem('token');
              localStorage.removeItem('refreshToken');
              localStorage.removeItem('user');
              window.dispatchEvent(new Event('auth:logout'));
            }
          } catch (refreshErr) {
            processQueue(refreshErr, null);
            isRefreshing = false;
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            window.dispatchEvent(new Event('auth:logout'));
          }
        }
      }

      let errorMessage = `Request failed with status ${response.status}`;
      if (data) {
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (typeof data === 'object') {
          const firstKey = Object.keys(data)[0];
          if (firstKey) {
            const val = data[firstKey];
            errorMessage = Array.isArray(val) ? val.join(', ') : String(val);
          }
        }
      }

      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || 'Network error occurred', 0, null);
  }
}

export const apiClient = {
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

export { ApiError };
