/**
 * Zoom adaptativo por resolución de pantalla.
 *
 * Cómo funciona:
 *  - Se detecta el ancho del monitor físico (window.screen.width), una sola vez al cargar.
 *  - Se busca el primer entry donde screen.width <= maxWidth.
 *  - Si la ruta actual tiene un pageOverride, ese valor tiene prioridad sobre defaultZoom.
 *  - El zoom se aplica vía document.documentElement.style.zoom (idéntico al Ctrl+scroll del navegador).
 *
 * Cómo modificar:
 *  - Agregar filas al array para nuevas resoluciones.
 *  - Agregar rutas al pageOverrides del breakpoint correspondiente.
 *  - Los entries deben estar ordenados de menor a mayor maxWidth.
 */

export interface ZoomBreakpoint {
  /** Ancho máximo de pantalla (inclusive) en px. Usar Infinity para el último entry. */
  maxWidth: number;
  /** Zoom base para esta resolución (1.0 = 100%). */
  defaultZoom: number;
  /** Overrides por ruta. La clave es el pathname exacto (e.g. "/auditoria"). */
  pageOverrides: Record<string, number>;
}

export const ZOOM_BREAKPOINTS: ZoomBreakpoint[] = [
  // Notebook (1366x768, 1280x800, etc.)
  {
    maxWidth: 1366,
    defaultZoom: 0.67,
    pageOverrides: {},
  },
  // Monitores intermedios (1440p, etc.)
  {
    maxWidth: 1440,
    defaultZoom: 0.8,
    pageOverrides: {},
  },
  // Monitores grandes (1920p y más)
  {
    maxWidth: Infinity,
    defaultZoom: 1.0,
    pageOverrides: {},
  },
];
