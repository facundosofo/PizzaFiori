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
    // Avoid timezone shifts for date-only strings (YYYY-MM-DD).
    const date = /^\d{4}-\d{2}-\d{2}$/.test(isoString)
      ? (() => {
          const [year, month, day] = isoString.split("-").map((part) => Number(part));
          return new Date(year, month - 1, day);
        })()
      : new Date(isoString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  } catch (err) {
    return isoString;
  }
};

/**
 * Format a date string (ISO format) to DD/MM/YYYY HH:mm
 */
export const formatDateTimeDisplay = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  } catch (err) {
    return isoString;
  }
};

/**
 * Format a Date to local ISO datetime string (YYYY-MM-DDTHH:mm:ss) without UTC conversion.
 * Use this instead of toISOString() to preserve Argentina (server) local time.
 */
export const formatLocalISO = (date: Date): string => {
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  );
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
    return formatLocalISO(date).replace('T', ' ');
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
    return formatLocalISO(date).split('T')[0];
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
