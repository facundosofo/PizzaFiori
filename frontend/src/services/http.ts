/**
 * HTTP Client with Axios - Configured with JWT Bearer token interceptors
 */

import axios from 'axios';
import type { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import env from '../config/env';
import { translateErrorMessage } from '../constants/validationMessages';

function extractErrorText(data: unknown): string {
  if (!data || typeof data !== 'object') return '';

  const payload = data as Record<string, unknown>;
  const detail = payload.detail;
  const message = payload.message;

  if (typeof detail === 'string') return detail.toLowerCase();
  if (typeof message === 'string') return message.toLowerCase();

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && 'msg' in item) {
          const msg = (item as Record<string, unknown>).msg;
          return typeof msg === 'string' ? msg : '';
        }
        return '';
      })
      .join(' ')
      .toLowerCase();
  }

  return '';
}

function isTokenAuthError(error: AxiosError): boolean {
  const text = extractErrorText(error.response?.data);

  // Logout only when 401 is clearly due to JWT/session auth.
  return [
    'invalid or expired token',
    'signature has expired',
    'missing authentication token',
    'www-authenticate',
    'bearer',
    'token',
    'user not found',
  ].some((tokenHint) => text.includes(tokenHint));
}

// Create Axios instance
const api = axios.create({
  baseURL: env.API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor: Add JWT Bearer token to all requests
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Check if token is expired BEFORE sending request (proactive check)
    const expiresAt = localStorage.getItem('token_expires_at');
    if (expiresAt && Date.now() > parseInt(expiresAt)) {
      clearAuth();
      window.location.href = '/login';
      return Promise.reject(new Error('Token expired'));
    }

    // Add Bearer token to Authorization header
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor: Handle authentication errors (401) and forbidden (403)
 * Also translates error messages from English to Spanish
 */
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // Translate error message if present
    if (error.response?.data) {
      const data = error.response.data as any;
      
      // Handle FastAPI error format (detail field)
      if (data.detail) {
        if (typeof data.detail === 'string') {
          data.detail = translateErrorMessage(data.detail);
        } else if (Array.isArray(data.detail)) {
          // Handle validation errors array
          data.detail = data.detail.map((item: any) => {
            if (typeof item === 'string') {
              return translateErrorMessage(item);
            }
            if (item.msg) {
              return { ...item, msg: translateErrorMessage(item.msg) };
            }
            return item;
          });
        }
      }
      
      // Handle generic message field
      if (data.message && typeof data.message === 'string') {
        data.message = translateErrorMessage(data.message);
      }
    }

    // Handle authentication errors
    if (error.response?.status === 401 && isTokenAuthError(error)) {
      // Only force logout on token/session related 401 responses.
      clearAuth();
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      // Forbidden - insufficient permissions
    }

    return Promise.reject(error);
  }
);

/**
 * Clear all authentication data from localStorage
 */
function clearAuth(): void {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user');
  localStorage.removeItem('token_expires_in');
  localStorage.removeItem('token_expires_at');
}

export default api;
