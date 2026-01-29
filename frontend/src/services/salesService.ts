import env from "../config/env";
import type { Sale, SaleCreateRequest } from "../types/sale";
import type { SaleItemWithDetails } from "../types/sale_item";

interface SalesResponse {
  items: Sale[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * Fetch all sales with pagination
 */
export const getSales = async (skip: number = 0, limit: number = 10): Promise<SalesResponse> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ventas?skip=${skip}&limit=${limit}`);
    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "No se encontraron ventas"
        : res.status === 500
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudieron obtener las ventas";
      throw new Error(errorMsg);
    }
    const data = await res.json();
    return data as SalesResponse;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching sales:", err);
    throw new Error(errorMessage);
  }
};

/**
 * Fetch a single sale by ID
 * Backend now returns items with product/offer names included via hybrid properties
 */
export const getSaleById = async (
  id: number
): Promise<Sale & { items: SaleItemWithDetails[] }> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ventas/${id}`);
    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Venta no encontrada"
        : res.status === 500
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo obtener la venta";
      throw new Error(errorMsg);
    }
    
    const sale = (await res.json()) as Sale & { items: SaleItemWithDetails[] };

    return sale;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching sale by ID:", err);
    throw new Error(errorMessage);
  }
};

/**
 * Create a new sale
 */
export const createSale = async (data: SaleCreateRequest): Promise<Sale> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ventas`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorMsg = res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 500
        ? "Error al crear la venta. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo crear la venta";
      throw new Error(errorMsg);
    }
    return (await res.json()) as Sale;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error creating sale:", err);
    throw new Error(errorMessage);
  }
};

/**
 * Update an existing sale
 */
export const updateSale = async (
  id: number,
  data: SaleCreateRequest
): Promise<Sale> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ventas/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Venta no encontrada"
        : res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 500
        ? "Error al actualizar la venta. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo actualizar la venta";
      throw new Error(errorMsg);
    }
    return (await res.json()) as Sale;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error updating sale:", err);
    throw new Error(errorMessage);
  }
};

/**
 * Delete a sale
 */
export const deleteSale = async (id: number): Promise<void> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ventas/${id}`, {
      method: "DELETE",
    });

    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Venta no encontrada"
        : res.status === 500
        ? "Error al eliminar la venta. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo eliminar la venta";
      throw new Error(errorMsg);
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error deleting sale:", err);
    throw new Error(errorMessage);
  }
};

