/**
 * Validation Messages - Centralized error and validation messages
 * All user-facing validation messages in Spanish
 */

export const VALIDATION_MESSAGES = {
  // Required fields
  REQUIRED_USERNAME: 'El usuario es requerido',
  REQUIRED_EMAIL: 'El email es requerido',
  REQUIRED_PASSWORD: 'La contraseña es requerida',
  REQUIRED_CURRENT_PASSWORD: 'La contraseña actual es requerida',
  REQUIRED_NEW_PASSWORD: 'La nueva contraseña es requerida',
  REQUIRED_FIRST_NAME: 'El nombre es requerido',
  REQUIRED_LAST_NAME: 'El apellido es requerido',
  REQUIRED_USERNAME_PASSWORD: 'Por favor ingresa usuario y contraseña',

  // Password validations
  PASSWORD_MIN_LENGTH: 'La contraseña debe tener al menos 8 caracteres',
  PASSWORD_REQUIRE_UPPERCASE: 'La contraseña debe contener al menos una mayúscula',
  PASSWORD_REQUIRE_NUMBER: 'La contraseña debe contener al menos un número',
  PASSWORD_MISMATCH: 'Las contraseñas no coinciden',
  PASSWORD_SAME_AS_OLD: 'La nueva contraseña debe ser diferente a la actual',

  // Email validations
  EMAIL_INVALID: 'El email no es válido',

  // Generic errors
  ERROR_LOADING: 'Error al cargar los datos',
  ERROR_SAVING: 'Error al guardar los cambios',
  ERROR_DELETING: 'Error al eliminar',
  ERROR_CREATING: 'Error al crear',

  // Authentication errors
  ERROR_LOGIN: 'Error al iniciar sesión',
  ERROR_REGISTER: 'Error al registrarse',
  ERROR_CHANGE_PASSWORD: 'Error al cambiar la contraseña',
  ERROR_UNAUTHORIZED: 'No estás autorizado para realizar esta acción',

  // Success messages
  SUCCESS_PASSWORD_CHANGED: 'Contraseña actualizada exitosamente',
  SUCCESS_USER_CREATED: 'Usuario creado exitosamente',
  SUCCESS_USER_UNLOCKED: 'Usuario desbloqueado exitosamente',
  SUCCESS_USER_DELETED: 'Usuario eliminado exitosamente',

  // Other
  ERROR_NETWORK: 'Error de conexión. Verifica tu conexión a internet.',
  ERROR_SERVER: 'Error del servidor. Intenta nuevamente más tarde.',
  ERROR_UNKNOWN: 'Ocurrió un error inesperado',
} as const;

/**
 * Maps backend error messages (in English) to Spanish
 */
export const ERROR_MESSAGE_MAP: Record<string, string> = {
  // Authentication errors
  'Invalid credentials': 'Credenciales inválidas',
  'Invalid credentials. Please try again.': 'Credenciales inválidas. Por favor intenta nuevamente.',
  'Invalid username or password': 'Usuario o contraseña incorrectos',
  'User not found': 'Usuario no encontrado',
  'User is locked': 'Usuario bloqueado. Contacta al administrador',
  'Account locked due to too many failed attempts': 'Cuenta bloqueada por múltiples intentos fallidos',
  'Account locked due to too many failed attempts. Try again later.': 'Cuenta bloqueada por múltiples intentos fallidos. Intenta más tarde.',
  
  // Password errors
  'Password must be at least 8 characters': VALIDATION_MESSAGES.PASSWORD_MIN_LENGTH,
  'Password must contain at least one uppercase letter': VALIDATION_MESSAGES.PASSWORD_REQUIRE_UPPERCASE,
  'Password must contain at least one number': VALIDATION_MESSAGES.PASSWORD_REQUIRE_NUMBER,
  'Incorrect current password': 'La contraseña actual es incorrecta',
  'Current password is incorrect': 'La contraseña actual es incorrecta',
  
  // User management errors
  'Username or email already exists': 'El usuario o email ya existe',
  'Username already exists': 'El usuario ya existe',
  'Email already exists': 'El email ya existe',
  
  // Generic errors
  'Invalid request': 'Solicitud inválida',
  'Not found': 'No encontrado',
  'Forbidden': 'No tienes permisos para realizar esta acción',
  'Unauthorized': VALIDATION_MESSAGES.ERROR_UNAUTHORIZED,
  'Internal server error': VALIDATION_MESSAGES.ERROR_SERVER,
  'Service unavailable': 'Servicio no disponible. Intenta más tarde.',
  
  // Network errors
  'Network Error': VALIDATION_MESSAGES.ERROR_NETWORK,
  'timeout exceeded': 'Tiempo de espera agotado',
};

/**
 * Translates an error message from English to Spanish
 * Returns the original message if no translation is found
 */
export const translateErrorMessage = (message: string): string => {
  // Try exact match first
  if (ERROR_MESSAGE_MAP[message]) {
    return ERROR_MESSAGE_MAP[message];
  }
  
  // Try partial matches for common patterns
  const lowerMessage = message.toLowerCase();
  
  // Authentication errors
  if (lowerMessage.includes('invalid credentials')) {
    return 'Credenciales inválidas. Por favor intenta nuevamente.';
  }
  
  if (lowerMessage.includes('account locked') || lowerMessage.includes('too many failed attempts')) {
    return 'Cuenta bloqueada por múltiples intentos fallidos. Intenta más tarde.';
  }
  
  // Password validations
  if (lowerMessage.includes('password')) {
    if (message.includes('at least 8')) return VALIDATION_MESSAGES.PASSWORD_MIN_LENGTH;
    if (message.includes('uppercase')) return VALIDATION_MESSAGES.PASSWORD_REQUIRE_UPPERCASE;
    if (message.includes('number')) return VALIDATION_MESSAGES.PASSWORD_REQUIRE_NUMBER;
  }
  
  // User management
  if (lowerMessage.includes('already exists')) {
    return 'El registro ya existe';
  }
  
  if (lowerMessage.includes('not found')) {
    return 'No encontrado';
  }
  
  // Return original message if no translation found
  return message;
};
