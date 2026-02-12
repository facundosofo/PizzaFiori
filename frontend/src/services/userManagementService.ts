/**
 * User Management Service - Admin operations for user management
 */

import api from './http';
import type { User } from './authService';

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: string;
}

export interface UpdateUserRequest {
  first_name?: string;
  last_name?: string;
  email?: string;
  role?: string;
  is_active?: boolean;
}

class UserManagementService {
  /**
   * Get all users (Admin only)
   */
  async getAllUsers(): Promise<User[]> {
    try {
      const response = await api.get<User[]>('/users');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch users');
    }
  }

  /**
   * Create a new user (Admin only)
   */
  async createUser(data: CreateUserRequest): Promise<User> {
    try {
      const response = await api.post<{ user: User; message: string }>('/users', data);
      return response.data.user;
    } catch (error: any) {
      if (error.response?.status === 409) {
        throw new Error('El usuario o email ya existe');
      } else if (error.response?.status === 422) {
        throw new Error(error.response.data.detail || 'Datos inválidos');
      }
      throw new Error(error.response?.data?.detail || 'Error al crear usuario');
    }
  }

  /**
   * Update a user (Admin only)
   */
  async updateUser(userId: number, data: UpdateUserRequest): Promise<User> {
    try {
      const response = await api.put<User>(`/users/${userId}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al actualizar usuario');
    }
  }

  /**
   * Delete a user (Admin only)
   */
  async deleteUser(userId: number): Promise<void> {
    try {
      await api.delete(`/users/${userId}`);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al eliminar usuario');
    }
  }

  /**
   * Unlock a locked user account (Admin only)
   */
  async unlockUser(userId: number): Promise<User> {
    try {
      const response = await api.post<User>(`/users/${userId}/unlock`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al desbloquear usuario');
    }
  }
}

export default new UserManagementService();
