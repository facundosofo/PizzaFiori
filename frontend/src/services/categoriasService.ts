import env from "../config/env";
import type { Category } from "../types/category";

export const getCategorias = async (): Promise<Category[]> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/categorias`);
    if (!res.ok) {
      const errorMsg = res.status === 404 
        ? "No se encontraron categorías" 
        : res.status === 500 
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudieron obtener las categorías";
      throw new Error(errorMsg);
    }
    return res.json();
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching categorías:", err);
    throw new Error(errorMessage);
  }
};
