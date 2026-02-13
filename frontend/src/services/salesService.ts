import api from "./http";
import type { Sale, SaleCreateRequest } from "../types/sale";
import type { SaleItemWithDetails } from "../types/sale_item";
import { formatDateYMD } from "../utils/formatters";

interface SalesResponse {
  items: Sale[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * Fetch all sales with pagination and optional date filters
 */
export const getSales = async (
  skip: number = 0,
  limit: number = 10,
  dateFrom?: Date | null,
  dateTo?: Date | null
): Promise<SalesResponse> => {
  try {
    // Build query params
    const params: Record<string, string> = {
      skip: skip.toString(),
      limit: limit.toString(),
    };

    // Add date filters if provided
    if (dateFrom) {
      params.fecha_desde = formatDateYMD(dateFrom); // Format: YYYY-MM-DD
    }
    if (dateTo) {
      params.fecha_hasta = formatDateYMD(dateTo); // Format: YYYY-MM-DD
    }

    const response = await api.get<SalesResponse>("/ventas", { params });
    return response.data;
    return data as SalesResponse;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
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
    const response = await api.get<Sale & { items: SaleItemWithDetails[] }>(`/ventas/${id}`);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

/**
 * Create a new sale
 */
export const createSale = async (data: SaleCreateRequest): Promise<Sale> => {
  try {
    const response = await api.post<Sale>("/ventas", data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
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
    const response = await api.put<Sale>(`/ventas/${id}`, data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

/**
 * Delete a sale
 */
export const deleteSale = async (id: number): Promise<void> => {
  try {
    await api.delete(`/ventas/${id}`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

