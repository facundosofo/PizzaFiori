import env from "../config/env";
import type { Offer } from "../types/offer";

/**
 * Fetch all active offers
 */
export const getOfertas = async (): Promise<Offer[]> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas?active=true`);
    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "No se encontraron ofertas"
        : res.status === 500
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudieron obtener las ofertas";
      throw new Error(errorMsg);
    }
    const data = await res.json();
    return data as Offer[];
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching ofertas:", err);
    throw new Error(errorMessage);
  }
};
