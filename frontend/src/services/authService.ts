/**
 * Authentication Service - Handles login, registration, logout, and user state
 */

import axios from 'axios';
import env from '../config/env';
import api from './http';
import { translateErrorMessage } from '../constants/validationMessages';

export interface User {
  username: string;
  [key: string]: any;
}

export interface LoginResponse {
  token: string;
  expires_in: number; // seconds
  expires_at: number; // timestamp ms
  user: User;
  message: string;
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
      // Translate error messages from backend
      const errorMessage = error.response?.data?.detail || 'Login failed';
      throw new Error(translateErrorMessage(errorMessage));
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
