import api from "./http";
import type {
  CategoryStock,
  StockListResponse,
  StockMovement,
  AddStockRequest,
  ConfigureAlertsRequest,
  ProductStock,
  CategoryConfigItem,
} from "../types/stock";

export const getAllStocks = async (): Promise<StockListResponse> => {
  try {
    const response = await api.get<StockListResponse>("/stock");
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const getStockConfig = async (): Promise<CategoryConfigItem[]> => {
  try {
    const response = await api.get<CategoryConfigItem[]>("/stock/config");
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error al obtener configuración";
    throw new Error(errorMessage);
  }
};

export const saveStockConfig = async (
  configs: Pick<CategoryConfigItem, "categoria_id" | "stock_visible" | "stock_por_producto">[]
): Promise<void> => {
  try {
    await api.put("/stock/config", { configs });
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error al guardar configuración";
    throw new Error(errorMessage);
  }
};

export const getProductStocks = async (categoriaId: number): Promise<ProductStock[]> => {
  try {
    const response = await api.get<ProductStock[]>(`/stock/${categoriaId}/productos`);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error al obtener stock por producto";
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

export const addProductStock = async (
  productoId: number,
  data: AddStockRequest
): Promise<ProductStock> => {
  try {
    const response = await api.post<ProductStock>(
      `/stock/productos/${productoId}/agregar`,
      data
    );
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error al agregar stock de producto";
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

export const configureProductAlerts = async (
  productoId: number,
  data: ConfigureAlertsRequest
): Promise<ProductStock> => {
  try {
    const response = await api.put<ProductStock>(
      `/stock/productos/${productoId}/alertas`,
      data
    );
    return response.data;
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : "Error al configurar alertas de producto";
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

