/**
 * UserManagementPage - Admin panel for managing users
 */

import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';
import type { User } from '../services/userService';
import userManagementService from '../services/userManagementService';
import type { CreateUserRequest } from '../services/userManagementService';
import '../styles/user-management.css';
import '../styles/shared/page-header.css';
import { validateUserCreationForm } from '../utils/validation';
import { VALIDATION_MESSAGES } from '../constants/validationMessages';
import * as Icons from '../components/shared/Icons';

const UserManagementPage = () => {
  const { user: currentUser, isLoading: authLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'USER',
  });

  // Check if current user is admin
  const isAdmin = currentUser?.role === 'ADMIN';

  useEffect(() => {
    if (!success) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setSuccess('');
    }, 1500);

    return () => window.clearTimeout(timeoutId);
  }, [success]);

  useEffect(() => {
    if (isAdmin) {
      loadUsers();
    }
  }, [isAdmin]);

  const loadUsers = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await userManagementService.getAllUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err.message || VALIDATION_MESSAGES.ERROR_LOADING);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof CreateUserRequest, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };



  const handleCreateUser = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const validationError = validateUserCreationForm({
      username: formData.username,
      email: formData.email,
      first_name: formData.first_name,
      last_name: formData.last_name,
      password: formData.password,
    });
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      await userManagementService.createUser(formData);
      setSuccess(`${VALIDATION_MESSAGES.SUCCESS_USER_CREATED}: ${formData.username}`);
      setFormData({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        role: 'USER',
      });
      setShowCreateForm(false);
      loadUsers();
    } catch (err: any) {
      setError(err.message || VALIDATION_MESSAGES.ERROR_CREATING);
    }
  };

  const handleUnlockUser = async (userId: number) => {
    setError('');
    setSuccess('');
    try {
      await userManagementService.unlockUser(userId);
      setSuccess(VALIDATION_MESSAGES.SUCCESS_USER_UNLOCKED);
      loadUsers();
    } catch (err: any) {
      setError(err.message || VALIDATION_MESSAGES.ERROR_SAVING);
    }
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    if (!window.confirm(`¿Estás seguro de eliminar al usuario "${username}"? Esta acción no se puede deshacer.`)) {
      return;
    }

    setError('');
    setSuccess('');
    try {
      await userManagementService.deleteUser(userId);
      setSuccess(`${VALIDATION_MESSAGES.SUCCESS_USER_DELETED}: ${username}`);
      loadUsers();
    } catch (err: any) {
      setError(err.message || VALIDATION_MESSAGES.ERROR_DELETING);
    }
  };

  if (authLoading) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <Icons.ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-management-container">
      <div className="page-header">
        <h1 className="page-title">Gestión de Usuarios</h1>
        <button
          className="btn-primary"
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Cancelar' : '+ Crear Usuario'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {showCreateForm && (
        <div className="create-user-form">
          <h2>Crear Nuevo Usuario</h2>
          <form onSubmit={handleCreateUser}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="first_name">Nombre</label>
                <input
                  id="first_name"
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => handleChange('first_name', e.target.value)}
                  placeholder="Nombre"
                />
              </div>
              <div className="form-group">
                <label htmlFor="last_name">Apellido</label>
                <input
                  id="last_name"
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => handleChange('last_name', e.target.value)}
                  placeholder="Apellido"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="username">Usuario</label>
                <input
                  id="username"
                  type="text"
                  value={formData.username}
                  onChange={(e) => handleChange('username', e.target.value)}
                  placeholder="Usuario"
                />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  placeholder="email@ejemplo.com"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="password">Contraseña</label>
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  placeholder="Mínimo 8 caracteres, 1 mayúscula, 1 número"
                />
              </div>
              <div className="form-group">
                <label htmlFor="role">Rol</label>
                <select
                  id="role"
                  value={formData.role}
                  onChange={(e) => handleChange('role', e.target.value)}
                >
                  <option value="USER">Usuario</option>
                  <option value="ADMIN">Administrador</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn-primary">
              Crear Usuario
            </button>
          </form>
        </div>
      )}

      <div className="users-table-container">
        {isLoading ? (
          <p>Cargando usuarios...</p>
        ) : (
          <table className="users-table">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Email</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => {
                const isLocked = user.locked_until && new Date(user.locked_until) > new Date();
                return (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>
                    {user.first_name} {user.last_name}
                  </td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`role-badge role-${user.role.toLowerCase()}`}>
                      {user.role === 'ADMIN' ? 'ADMINISTRADOR' : 'USUARIO'}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge status-${isLocked ? 'locked' : 'active'}`}>
                      {isLocked ? 'BLOQUEADO' : 'ACTIVO'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn-action btn-unlock"
                        onClick={() => handleUnlockUser(user.id)}
                        disabled={!isLocked}
                        title={isLocked ? "Desbloquear cuenta" : "Usuario activo"}
                      >
                        <Icons.KeyIcon size={16} color="#22c55e" />
                      </button>
                      <button
                        className="btn-action btn-delete"
                        onClick={() => handleDeleteUser(user.id, user.username)}
                        disabled={user.id === currentUser?.id}
                        title="Eliminar usuario"
                      >
                        <Icons.TrashIcon size={16} color="#ef4444" />
                      </button>
                    </div>
                  </td>
                </tr>
              )})}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default UserManagementPage;
