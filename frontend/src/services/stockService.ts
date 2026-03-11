import api from "./http";
import type {
  CategoryStock,
  StockMovement,
  AddStockRequest,
  ConfigureAlertsRequest,
} from "../types/stock";

export const getAllStocks = async (): Promise<CategoryStock[]> => {
  try {
    const response = await api.get<CategoryStock[]>("/stock");
    if (!Array.isArray(response.data)) return [];
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const addStock = async (
  categoriaId: number,
  data: AddStockRequest
): Promise<CategoryStock> => {
  try {
    const response = await api.post<CategoryStock>(
      `/stock/${categoriaId}/agregar`,
      data
    );
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error al agregar stock";
    throw new Error(errorMessage);
  }
};

export const configureAlerts = async (
  categoriaId: number,
  data: ConfigureAlertsRequest
): Promise<CategoryStock> => {
  try {
    const response = await api.put<CategoryStock>(
      `/stock/${categoriaId}/alertas`,
      data
    );
    return response.data;
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : "Error al configurar alertas";
    throw new Error(errorMessage);
  }
};

export const getStockMovements = async (
  categoriaId: number,
  limit = 50
): Promise<StockMovement[]> => {
  try {
    const response = await api.get<StockMovement[]>(
      `/stock/${categoriaId}/movimientos`,
      { params: { limit } }
    );
    return response.data;
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : "Error al obtener movimientos";
    throw new Error(errorMessage);
  }
};
