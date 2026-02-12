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

      return response.data.user;
    } catch (error: any) {
      // Error messages are already translated by the axios interceptor
      throw new Error(error.response?.data?.detail || 'Error al registrar usuario');
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
    } catch (error: any) {
      // Error messages are already translated by the axios interceptor
      throw new Error(error.response?.data?.detail || 'Error al cambiar la contraseña');
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
      // Error messages are already translated by the axios interceptor
      throw new Error(error.response?.data?.detail || 'Error al cargar usuario');
    }
  }
}

export default new UserService();
