/**
 * API Service - HTTP client for backend communication
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.headers = { 'Content-Type': 'application/json' };
  }

  setAuthToken(token) {
    if (token) this.headers['Authorization'] = `Bearer ${token}`;
    else delete this.headers['Authorization'];
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = { ...options, headers: { ...this.headers, ...options.headers } };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(error.message || 'Request failed', response.status, error);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError('Network error', 0, { original: error.message });
    }
  }

  get(endpoint, params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(query ? `${endpoint}?${query}` : endpoint, { method: 'GET' });
  }

  post(endpoint, data) {
    return this.request(endpoint, { method: 'POST', body: JSON.stringify(data) });
  }

  put(endpoint, data) {
    return this.request(endpoint, { method: 'PUT', body: JSON.stringify(data) });
  }

  patch(endpoint, data) {
    return this.request(endpoint, { method: 'PATCH', body: JSON.stringify(data) });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

class ApiError extends Error {
  constructor(message, status, data = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export const api = new ApiService(API_BASE_URL);
export { ApiError };
export default api;
