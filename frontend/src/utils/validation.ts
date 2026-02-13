/**
 * Validation Utilities - Reusable validation functions
 */

import { VALIDATION_MESSAGES } from '../constants/validationMessages';

/**
 * Validates a password against all password requirements
 * @returns null if valid, error message if invalid
 */
export const validatePassword = (password: string): string | null => {
  if (!password) {
    return VALIDATION_MESSAGES.REQUIRED_PASSWORD;
  }
  
  if (password.length < 8) {
    return VALIDATION_MESSAGES.PASSWORD_MIN_LENGTH;
  }
  
  if (!/[A-Z]/.test(password)) {
    return VALIDATION_MESSAGES.PASSWORD_REQUIRE_UPPERCASE;
  }
  
  if (!/[0-9]/.test(password)) {
    return VALIDATION_MESSAGES.PASSWORD_REQUIRE_NUMBER;
  }
  
  return null;
};

/**
 * Validates password confirmation
 * @returns null if valid, error message if invalid
 */
export const validatePasswordMatch = (
  password: string,
  confirmPassword: string
): string | null => {
  if (password !== confirmPassword) {
    return VALIDATION_MESSAGES.PASSWORD_MISMATCH;
  }
  
  return null;
};

/**
 * Validates that new password is different from old password
 * @returns null if valid, error message if invalid
 */
export const validatePasswordChange = (
  oldPassword: string,
  newPassword: string
): string | null => {
  if (!oldPassword) {
    return VALIDATION_MESSAGES.REQUIRED_CURRENT_PASSWORD;
  }
  
  if (!newPassword) {
    return VALIDATION_MESSAGES.REQUIRED_NEW_PASSWORD;
  }
  
  if (oldPassword === newPassword) {
    return VALIDATION_MESSAGES.PASSWORD_SAME_AS_OLD;
  }
  
  return null;
};

/**
 * Validates email format
 * @returns null if valid, error message if invalid
 */
export const validateEmail = (email: string): string | null => {
  if (!email || !email.trim()) {
    return VALIDATION_MESSAGES.REQUIRED_EMAIL;
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return VALIDATION_MESSAGES.EMAIL_INVALID;
  }
  
  return null;
};

/**
 * Validates username
 * @returns null if valid, error message if invalid
 */
export const validateUsername = (username: string): string | null => {
  if (!username || !username.trim()) {
    return VALIDATION_MESSAGES.REQUIRED_USERNAME;
  }
  
  if (username.length < 3) {
    return 'El nombre de usuario debe tener al menos 3 caracteres';
  }
  
  if (username.length > 50) {
    return 'El nombre de usuario no puede exceder 50 caracteres';
  }
  
  if (!/^[a-zA-Z0-9]+$/.test(username)) {
    return 'El nombre de usuario solo puede contener letras y números';
  }
  
  return null;
};

/**
 * Validates first or last name
 * @returns null if valid, error message if invalid
 */
export const validateName = (
  value: string,
  fieldName: string
): string | null => {
  if (!value || !value.trim()) {
    return `${fieldName} es requerido`;
  }
  
  if (value.length > 50) {
    return `${fieldName} no puede exceder 50 caracteres`;
  }
  
  return null;
};

/**
 * Validates required text field
 * @returns null if valid, error message if invalid
 */
export const validateRequired = (
  value: string,
  fieldName: string
): string | null => {
  if (!value || !value.trim()) {
    return `${fieldName} es requerido`;
  }
  
  return null;
};

/**
 * Validates login form (username and password)
 * @returns null if valid, error message if invalid
 */
export const validateLoginForm = (
  username: string,
  password: string
): string | null => {
  if (!username.trim() || !password.trim()) {
    return VALIDATION_MESSAGES.REQUIRED_USERNAME_PASSWORD;
  }
  
  return null;
};

/**
 * Validates user registration form
 * @returns null if valid, error message if invalid
 */
export const validateRegistrationForm = (data: {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  confirmPassword: string;
}): string | null => {
  // Username validation
  const usernameError = validateUsername(data.username);
  if (usernameError) return usernameError;
  
  // Email validation
  const emailError = validateEmail(data.email);
  if (emailError) return emailError;
  
  // First name validation
  const firstNameError = validateName(data.first_name, 'Nombre');
  if (firstNameError) return firstNameError;
  
  // Last name validation
  const lastNameError = validateName(data.last_name, 'Apellido');
  if (lastNameError) return lastNameError;
  
  // Password validation
  const passwordError = validatePassword(data.password);
  if (passwordError) return passwordError;
  
  // Password match
  const matchError = validatePasswordMatch(data.password, data.confirmPassword);
  if (matchError) return matchError;
  
  return null;
};

/**
 * Validates user creation form (for admin)
 * @returns null if valid, error message if invalid
 */
export const validateUserCreationForm = (data: {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}): string | null => {
  // Username validation
  const usernameError = validateUsername(data.username);
  if (usernameError) return usernameError;
  
  // Email validation
  const emailError = validateEmail(data.email);
  if (emailError) return emailError;
  
  // First name validation
  const firstNameError = validateName(data.first_name, 'Nombre');
  if (firstNameError) return firstNameError;
  
  // Last name validation
  const lastNameError = validateName(data.last_name, 'Apellido');
  if (lastNameError) return lastNameError;
  
  // Password validation
  const passwordError = validatePassword(data.password);
  if (passwordError) return passwordError;
  
  return null;
};

/**
 * Validates password change form
 * @returns null if valid, error message if invalid
 */
export const validatePasswordChangeForm = (data: {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}): string | null => {
  // Check old and new passwords
  const changeError = validatePasswordChange(data.oldPassword, data.newPassword);
  if (changeError) return changeError;
  
  // Validate new password strength
  const passwordError = validatePassword(data.newPassword);
  if (passwordError) return passwordError;
  
  // Check password match
  const matchError = validatePasswordMatch(data.newPassword, data.confirmPassword);
  if (matchError) return matchError;
  
  return null;
};
