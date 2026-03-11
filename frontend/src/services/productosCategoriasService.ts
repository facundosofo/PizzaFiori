import api from "./http";
import type { ProductoCategoria } from "../types/product_category";

export interface CreateProductoCategoriaRequest {
  nombre: string;
}

export interface UpdateProductoCategoriaRequest {
  nombre?: string;
}

export const getProductosCategorias = async (activo?: boolean): Promise<ProductoCategoria[]> => {
  try {
    const params = activo !== undefined ? { activo } : {};
    const response = await api.get<ProductoCategoria[]>("/productos-categorias", { params });
    if (!Array.isArray(response.data)) return [];
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const getProductoCategoriaById = async (id: number): Promise<ProductoCategoria> => {
  try {
    const response = await api.get<ProductoCategoria>(`/productos-categorias/${id}`);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const createProductoCategoria = async (data: CreateProductoCategoriaRequest): Promise<ProductoCategoria> => {
  try {
    const response = await api.post<ProductoCategoria>("/productos-categorias", data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const updateProductoCategoria = async (id: number, data: UpdateProductoCategoriaRequest): Promise<ProductoCategoria> => {
  try {
    const response = await api.put<ProductoCategoria>(`/productos-categorias/${id}`, data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const deactivateProductoCategoria = async (id: number): Promise<void> => {
  try {
    await api.patch(`/productos-categorias/${id}/desactivar`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};
