/**
 * Authentication Service - Handles login, registration, logout, and user state
 */

import axios from 'axios';
import env from '../config/env';
import api from './http';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  token: string;
  expires_in: number; // seconds
  expires_at: number; // timestamp ms
  user: User;
  message: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

class AuthService {
  /**
   * Login user with username and password (sent as Basic Auth header)
   * Stores JWT token and user data in localStorage
   */
  async login(username: string, password: string): Promise<User> {
    try {
      // Encode credentials in Base64 ONLY for this request (not stored)
      const credentials = btoa(`${username}:${password}`);

      const response = await axios.post<LoginResponse>(
        `${env.API_BASE_URL}/auth/login`,
        null, // No body
        {
          headers: {
            Authorization: `Basic ${credentials}`,
          },
          withCredentials: true,
        }
      );

      const { token, expires_in, expires_at, user } = response.data;

      // Store ONLY the token, not credentials
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('token_expires_in', expires_in.toString());
      localStorage.setItem('token_expires_at', expires_at.toString());

      console.log('Login successful:', user.username);

      return user;
    } catch (error: any) {
      if (error.response?.status === 423) {
        throw new Error('Account locked due to too many failed attempts. Try again later.');
      } else if (error.response?.status === 401) {
        throw new Error('Invalid credentials. Please try again.');
      } else if (error.response?.status === 403) {
        throw new Error('Account is inactive. Contact support.');
      }

      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  }

  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<User> {
    try {
      const response = await axios.post<{ user: User; message: string }>(
        `${env.API_BASE_URL}/auth/register`,
        data
      );

      console.log('Registration successful:', response.data.message);

      return response.data.user;
    } catch (error: any) {
      if (error.response?.status === 409) {
        throw new Error(error.response.data.detail || 'Username or email already exists');
      } else if (error.response?.status === 422) {
        throw new Error(error.response.data.detail || 'Invalid password or data');
      }

      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  }

  /**
   * Logout current user (invalidates all tokens in server)
   * Clears localStorage
   */
  async logout(): Promise<void> {
    try {
      // Call server logout endpoint to invalidate token
      await api.post('/auth/logout');
    } catch (error) {
      console.warn('Logout request failed, clearing local storage anyway');
    } finally {
      // Always clear local auth data
      this.clearAuth();
    }
  }

  /**
   * Change password for authenticated user
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    try {
      const response = await api.post<{ message: string }>(
        '/auth/change-password',
        {
          old_password: oldPassword,
          new_password: newPassword,
        }
      );

      console.log('Password changed successfully:', response.data.message);
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Invalid old password');
      } else if (error.response?.status === 422) {
        throw new Error(error.response.data.detail || 'Invalid new password');
      }

      throw new Error(error.response?.data?.detail || 'Failed to change password');
    }
  }

  /**
   * Get current authenticated user info
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await api.get<User>('/auth/me');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch user');
    }
  }

  /**
   * Get stored user from localStorage
   */
  getStoredUser(): User | null {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  /**
   * Alias for getStoredUser - Get user from localStorage
   */
  getUser(): User | null {
    return this.getStoredUser();
  }

  /**
   * Get stored token from localStorage
   */
  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  /**
   * Check if user is authenticated (has valid non-expired token)
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    // Check if token is expired
    if (this.isTokenExpired()) {
      this.clearAuth();
      return false;
    }

    return true;
  }

  /**
   * Check if token is expired
   */
  isTokenExpired(): boolean {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return true;

    return Date.now() > parseInt(expiresAt);
  }

  /**
   * Check if token is expiring soon (within threshold minutes)
   */
  isTokenExpiringSoon(minutesThreshold: number = 5): boolean {
    const timeLeft = this.getTimeUntilExpiry();
    const thresholdMs = minutesThreshold * 60 * 1000;

    return timeLeft < thresholdMs && timeLeft > 0;
  }

  /**
   * Get time until token expiry in milliseconds
   */
  getTimeUntilExpiry(): number {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return 0;

    return Math.max(0, parseInt(expiresAt) - Date.now());
  }

  /**
   * Clear all auth data from localStorage
   */
  clearAuth(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    localStorage.removeItem('token_expires_in');
    localStorage.removeItem('token_expires_at');
  }
}

export default new AuthService();
