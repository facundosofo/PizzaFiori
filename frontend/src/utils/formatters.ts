/**
 * Format a number as currency in Argentine Pesos (ARS)
 */
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format a date string (ISO format) to DD/MM/YYYY
 */
export const formatDateDisplay = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  } catch (err) {
    console.error("Error formatting date:", err);
    return isoString;
  }
};

/**
 * Format a date string to ISO format for API (YYYY-MM-DD HH:mm:ss)
 */
export const formatDateAPI = (date: Date): string => {
  try {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (err) {
    console.error("Error formatting date for API:", err);
    return date.toISOString();
  }
};

/**
 * Format a Date to YYYY-MM-DD (useful for query params)
 */
export const formatDateYMD = (date: Date): string => {
  try {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  } catch (err) {
    console.error("Error formatting date (YMD):", err);
    return date.toISOString().split('T')[0];
  }
};

/**
 * Parse a currency-like input string (e.g. "$ 1.234,56") to number
 */
export const parseCurrencyInput = (value: string): number => {
  return Number(
    value
      .replace(/\$/g, "")
      .replace(/\./g, "")
      .replace(",", ".")
      .trim()
  );
};

/**
 * Parse DD/MM/YYYY string to Date object
 */
export const parseDate = (ddmmyyyy: string): Date | null => {
  try {
    const parts = ddmmyyyy.split('/');
    if (parts.length !== 3) return null;
    
    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1; // months are 0-indexed
    const year = parseInt(parts[2], 10);
    
    if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
    
    return new Date(year, month, day);
  } catch (err) {
    console.error("Error parsing date:", err);
    return null;
  }
};

/**
 * Validate date range (from <= to, no future dates)
 */
export const validateDateRange = (from: Date | null, to: Date | null): string | null => {
  const now = new Date();
  now.setHours(23, 59, 59, 999); // Set to end of today
  
  if (from && from > now) {
    return "La fecha 'Desde' no puede ser futura";
  }
  
  if (to && to > now) {
    return "La fecha 'Hasta' no puede ser futura";
  }
  
  if (from && to && from > to) {
    return "La fecha 'Desde' debe ser anterior o igual a 'Hasta'";
  }
  
  return null;
};
