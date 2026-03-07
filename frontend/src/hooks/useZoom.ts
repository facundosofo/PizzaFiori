import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { ZOOM_BREAKPOINTS } from "../config/zoomConfig";

/**
 * Aplica zoom adaptativo según la resolución de pantalla y la ruta actual.
 * Debe usarse dentro de un componente que esté bajo un <Router>.
 */
export function useZoom() {
  const { pathname } = useLocation();

  useEffect(() => {
    const screenWidth = window.screen.width;

    const breakpoint = ZOOM_BREAKPOINTS.find((bp) => screenWidth <= bp.maxWidth);
    if (!breakpoint) return;

    const zoom =
      breakpoint.pageOverrides[pathname] !== undefined
        ? breakpoint.pageOverrides[pathname]
        : breakpoint.defaultZoom;

    document.documentElement.style.zoom = String(zoom);
    document.documentElement.style.setProperty("--zoom", String(zoom));
    // Compensa 100vh: los elementos que usan var(--app-height) rellenan la pantalla correctamente.
    // Ej: zoom=0.67 → --app-height=149.25vh; renderizado al 0.67× eso equivale a 100vh visual.
    document.documentElement.style.setProperty(
      "--app-height",
      zoom === 1 ? "100vh" : `${100 / zoom}vh`
    );

    return () => {
      document.documentElement.style.zoom = "1";
      document.documentElement.style.removeProperty("--zoom");
      document.documentElement.style.removeProperty("--app-height");
    };
  }, [pathname]);
}
