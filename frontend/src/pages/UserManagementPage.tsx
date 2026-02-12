/**
 * UserManagementPage - Admin panel for managing users
 */

import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';
import type { User } from '../services/authService';
import userManagementService from '../services/userManagementService';
import type { CreateUserRequest } from '../services/userManagementService';
import '../styles/user-management.css';

const UserManagementPage = () => {
  const { user: currentUser } = useAuth();
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
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'SUPER_ADMIN';

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
      setError(err.message || 'Error al cargar usuarios');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof CreateUserRequest, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const validateForm = (): string | null => {
    if (!formData.username.trim()) return 'El usuario es requerido';
    if (!formData.email.trim()) return 'El email es requerido';
    if (!formData.first_name.trim()) return 'El nombre es requerido';
    if (!formData.last_name.trim()) return 'El apellido es requerido';
    if (!formData.password) return 'La contraseña es requerida';
    if (formData.password.length < 8) return 'La contraseña debe tener al menos 8 caracteres';
    if (!/[A-Z]/.test(formData.password)) return 'La contraseña debe contener al menos una mayúscula';
    if (!/[0-9]/.test(formData.password)) return 'La contraseña debe contener al menos un número';
    return null;
  };

  const handleCreateUser = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      await userManagementService.createUser(formData);
      setSuccess(`Usuario ${formData.username} creado exitosamente`);
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
      setError(err.message || 'Error al crear usuario');
    }
  };

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    setError('');
    setSuccess('');
    try {
      await userManagementService.updateUser(userId, { is_active: !currentStatus });
      setSuccess(`Usuario ${!currentStatus ? 'activado' : 'desactivado'} exitosamente`);
      loadUsers();
    } catch (err: any) {
      setError(err.message || 'Error al cambiar estado del usuario');
    }
  };

  const handleUnlockUser = async (userId: number) => {
    setError('');
    setSuccess('');
    try {
      await userManagementService.unlockUser(userId);
      setSuccess('Usuario desbloqueado exitosamente');
      loadUsers();
    } catch (err: any) {
      setError(err.message || 'Error al desbloquear usuario');
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
      setSuccess(`Usuario ${username} eliminado exitosamente`);
      loadUsers();
    } catch (err: any) {
      setError(err.message || 'Error al eliminar usuario');
    }
  };

  if (!isAdmin) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <h1>⛔ Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-management-container">
      <div className="user-management-header">
        <h1>👥 Gestión de Usuarios</h1>
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
                  <option value="MODERATOR">Moderador</option>
                  <option value="ADMIN">Administrador</option>
                  {currentUser?.role === 'SUPER_ADMIN' && (
                    <option value="SUPER_ADMIN">Super Admin</option>
                  )}
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
                <th>ID</th>
                <th>Nombre</th>
                <th>Usuario</th>
                <th>Email</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>
                    {user.first_name} {user.last_name}
                  </td>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`role-badge role-${user.role.toLowerCase()}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn-action btn-toggle"
                        onClick={() => handleToggleActive(user.id, user.is_active)}
                        disabled={user.id === currentUser?.id}
                        title={user.is_active ? 'Desactivar' : 'Activar'}
                      >
                        {user.is_active ? '🔒' : '🔓'}
                      </button>
                      <button
                        className="btn-action btn-unlock"
                        onClick={() => handleUnlockUser(user.id)}
                        title="Desbloquear cuenta"
                      >
                        🔑
                      </button>
                      <button
                        className="btn-action btn-delete"
                        onClick={() => handleDeleteUser(user.id, user.username)}
                        disabled={user.id === currentUser?.id}
                        title="Eliminar usuario"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default UserManagementPage;
