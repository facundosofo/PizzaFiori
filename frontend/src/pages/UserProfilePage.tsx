/**
 * UserProfilePage - User profile and password change
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';
import userService from '../services/userService';
import '../styles/profile.css';
import { validatePasswordChangeForm } from '../utils/validation';
import { VALIDATION_MESSAGES } from '../constants/validationMessages';
import * as Icons from "../components/shared/Icons";

const UserProfilePage = () => {
  const { user } = useAuth();
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handlePasswordChange = (field: string, value: string) => {
    setPasswordForm((prev) => ({ ...prev, [field]: value }));
    setError('');
    setSuccess('');
  };



  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const validationError = validatePasswordChangeForm({
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword,
      confirmPassword: passwordForm.confirmPassword,
    });
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);

    try {
      await userService.changePassword(
        passwordForm.oldPassword,
        passwordForm.newPassword
      );

      setSuccess(VALIDATION_MESSAGES.SUCCESS_PASSWORD_CHANGED);
      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
      setIsChangingPassword(false);
    } catch (err: any) {
      setError(err.message || VALIDATION_MESSAGES.ERROR_CHANGE_PASSWORD);
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
          <p className="profile-role">{user.role === 'ADMIN' ? 'ADMINISTRADOR' : 'USUARIO'}</p>
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
                  <div className="input-with-icon">
                    <input
                      id="oldPassword"
                      type={showOldPassword ? 'text' : 'password'}
                      value={passwordForm.oldPassword}
                      onChange={(e) => handlePasswordChange('oldPassword', e.target.value)}
                      placeholder="Ingresa tu contraseña actual"
                      autoComplete="current-password"
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowOldPassword(!showOldPassword)}
                      aria-label={showOldPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                      tabIndex={-1}
                    >
                      {showOldPassword ? <Icons.EyeOffIcon size={18} /> : <Icons.EyeIcon size={18} />}
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <div className="label-with-tooltip">
                    <label htmlFor="newPassword">Nueva Contraseña</label>
                    <div className="info-tooltip">
                      <Icons.InfoIcon className="info-icon" />
                      <div className="tooltip-content">
                        Minimo 8 caracteres, 1 mayuscula, 1 numero
                      </div>
                    </div>
                  </div>
                  <div className="input-with-icon">
                    <input
                      id="newPassword"
                      type={showNewPassword ? 'text' : 'password'}
                      value={passwordForm.newPassword}
                      onChange={(e) => handlePasswordChange('newPassword', e.target.value)}
                      placeholder="Mínimo 8 caracteres, 1 mayúscula, 1 número"
                      autoComplete="new-password"
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      aria-label={showNewPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                      tabIndex={-1}
                    >
                      {showNewPassword ? <Icons.EyeOffIcon size={18} /> : <Icons.EyeIcon size={18} />}
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirmar Nueva Contraseña</label>
                  <div className="input-with-icon">
                    <input
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={passwordForm.confirmPassword}
                      onChange={(e) => handlePasswordChange('confirmPassword', e.target.value)}
                      placeholder="Repite tu nueva contraseña"
                      autoComplete="new-password"
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      aria-label={showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                      tabIndex={-1}
                    >
                      {showConfirmPassword ? <Icons.EyeOffIcon size={18} /> : <Icons.EyeIcon size={18} />}
                    </button>
                  </div>
                </div>

                <div className="form-buttons">
                  <button
                    type="button"
                    className="form-cancel-btn"
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
