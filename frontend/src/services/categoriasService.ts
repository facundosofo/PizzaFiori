import api from "./http";
import type { Category } from "../types/category";

export interface CreateCategoryRequest {
  nombre: string;
}

export interface UpdateCategoryRequest {
  nombre?: string;
}

export const getCategorias = async (activo?: boolean): Promise<Category[]> => {
  try {
    const params = activo !== undefined ? { activo } : {};
    const response = await api.get<Category[]>("/categorias", { params });
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const getCategoriaById = async (id: number): Promise<Category> => {
  try {
    const response = await api.get<Category>(`/categorias/${id}`);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const createCategoria = async (data: CreateCategoryRequest): Promise<Category> => {
  try {
    const response = await api.post<Category>("/categorias", data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const updateCategoria = async (id: number, data: UpdateCategoryRequest): Promise<Category> => {
  try {
    const response = await api.put<Category>(`/categorias/${id}`, data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const deactivateCategoria = async (id: number): Promise<void> => {
  try {
    await api.patch(`/categorias/${id}/desactivar`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};
