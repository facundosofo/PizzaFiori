/**
 * User Service - Handles user registration and profile operations
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
  created_at: string;
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

class UserService {
  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<User> {
    try {
      const response = await axios.post<{ user: User; message: string }>(
        `${env.API_BASE_URL}/users`,
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
   * Change password for authenticated user
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    try {
      const response = await api.post<{ message: string }>(
        '/users/me/change-password',
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
      const response = await api.get<User>('/users/me');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch user');
    }
  }
}

export default new UserService();
