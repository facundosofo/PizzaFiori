/**
 * UserProfilePage - User profile and password change
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';
import authService from '../services/authService';
import '../styles/profile.css';

const UserProfilePage = () => {
  const { user } = useAuth();
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handlePasswordChange = (field: string, value: string) => {
    setPasswordForm((prev) => ({ ...prev, [field]: value }));
    setError('');
    setSuccess('');
  };

  const validatePasswordForm = (): string | null => {
    if (!passwordForm.oldPassword) return 'La contraseña actual es requerida';
    if (!passwordForm.newPassword) return 'La nueva contraseña es requerida';
    if (passwordForm.newPassword.length < 8)
      return 'La contraseña debe tener al menos 8 caracteres';
    if (!/[A-Z]/.test(passwordForm.newPassword))
      return 'La contraseña debe contener al menos una mayúscula';
    if (!/[0-9]/.test(passwordForm.newPassword))
      return 'La contraseña debe contener al menos un número';
    if (passwordForm.newPassword !== passwordForm.confirmPassword)
      return 'Las contraseñas no coinciden';
    if (passwordForm.oldPassword === passwordForm.newPassword)
      return 'La nueva contraseña debe ser diferente a la actual';
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const validationError = validatePasswordForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);

    try {
      await authService.changePassword(
        passwordForm.oldPassword,
        passwordForm.newPassword
      );

      setSuccess('Contraseña actualizada exitosamente');
      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
      setIsChangingPassword(false);
    } catch (err: any) {
      setError(err.message || 'Error al cambiar la contraseña');
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="profile-container">
        <p>Cargando perfil...</p>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-avatar">
            {user.first_name.charAt(0).toUpperCase()}
            {user.last_name.charAt(0).toUpperCase()}
          </div>
          <h1>
            {user.first_name} {user.last_name}
          </h1>
          <p className="profile-role">{user.role}</p>
        </div>

        <div className="profile-info">
          <div className="info-row">
            <span className="info-label">Usuario:</span>
            <span className="info-value">{user.username}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Email:</span>
            <span className="info-value">{user.email}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Estado:</span>
            <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
              {user.is_active ? 'Activo' : 'Inactivo'}
            </span>
          </div>
          <div className="info-row">
            <span className="info-label">Cuenta creada:</span>
            <span className="info-value">
              {new Date(user.created_at).toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
          </div>
        </div>

        <div className="profile-actions">
          {!isChangingPassword ? (
            <button
              className="btn-primary"
              onClick={() => setIsChangingPassword(true)}
            >
              Cambiar Contraseña
            </button>
          ) : (
            <div className="password-form">
              <h2>Cambiar Contraseña</h2>

              {error && <div className="form-error">{error}</div>}
              {success && <div className="form-success">{success}</div>}

              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="oldPassword">Contraseña Actual</label>
                  <input
                    id="oldPassword"
                    type="password"
                    value={passwordForm.oldPassword}
                    onChange={(e) => handlePasswordChange('oldPassword', e.target.value)}
                    placeholder="Ingresa tu contraseña actual"
                    autoComplete="current-password"
                    disabled={isLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="newPassword">Nueva Contraseña</label>
                  <input
                    id="newPassword"
                    type="password"
                    value={passwordForm.newPassword}
                    onChange={(e) => handlePasswordChange('newPassword', e.target.value)}
                    placeholder="Mínimo 8 caracteres, 1 mayúscula, 1 número"
                    autoComplete="new-password"
                    disabled={isLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirmar Nueva Contraseña</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={passwordForm.confirmPassword}
                    onChange={(e) => handlePasswordChange('confirmPassword', e.target.value)}
                    placeholder="Repite tu nueva contraseña"
                    autoComplete="new-password"
                    disabled={isLoading}
                  />
                </div>

                <div className="form-buttons">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => {
                      setIsChangingPassword(false);
                      setPasswordForm({
                        oldPassword: '',
                        newPassword: '',
                        confirmPassword: '',
                      });
                      setError('');
                      setSuccess('');
                    }}
                    disabled={isLoading}
                  >
                    Cancelar
                  </button>
                  <button type="submit" className="btn-primary" disabled={isLoading}>
                    {isLoading ? 'Guardando...' : 'Guardar Cambios'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;
