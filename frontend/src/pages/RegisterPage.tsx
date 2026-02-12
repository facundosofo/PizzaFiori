/**
 * RegisterPage - New user registration form
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/auth.css';
import { validateRegistrationForm } from '../utils/validation';
import { VALIDATION_MESSAGES } from '../constants/validationMessages';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };



  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    const validationError = validateRegistrationForm({
      username: formData.username,
      email: formData.email,
      first_name: formData.first_name,
      last_name: formData.last_name,
      password: formData.password,
      confirmPassword: formData.confirmPassword,
    });
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);

    try {
      await register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
      });

      // Registration successful, redirect to login
      navigate('/login', {
        state: { message: 'Registro exitoso. Por favor inicia sesión.' },
      });
    } catch (err: any) {
      setError(err.message || VALIDATION_MESSAGES.ERROR_REGISTER);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>🍕 Pizza Fiori</h1>
          <p>Crea tu cuenta</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="auth-error">{error}</div>}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">Nombre</label>
              <input
                id="first_name"
                type="text"
                value={formData.first_name}
                onChange={(e) => handleChange('first_name', e.target.value)}
                placeholder="Tu nombre"
                autoComplete="given-name"
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Apellido</label>
              <input
                id="last_name"
                type="text"
                value={formData.last_name}
                onChange={(e) => handleChange('last_name', e.target.value)}
                placeholder="Tu apellido"
                autoComplete="family-name"
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              value={formData.username}
              onChange={(e) => handleChange('username', e.target.value)}
              placeholder="Elige un nombre de usuario"
              autoComplete="username"
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              placeholder="tu@email.com"
              autoComplete="email"
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              placeholder="Mínimo 8 caracteres, 1 mayúscula, 1 número"
              autoComplete="new-password"
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirmar Contraseña</label>
            <input
              id="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => handleChange('confirmPassword', e.target.value)}
              placeholder="Repite tu contraseña"
              autoComplete="new-password"
              disabled={isLoading}
            />
          </div>

          <button type="submit" className="btn-primary" disabled={isLoading}>
            {isLoading ? 'Registrando...' : 'Registrarse'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            ¿Ya tienes cuenta?{' '}
            <Link to="/login" className="auth-link">
              Inicia sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
