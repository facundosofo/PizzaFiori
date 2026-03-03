import api from "./http";
import type { ExpenseCategory } from "../types/expense_category";

export interface CreateExpenseCategoryRequest {
  nombre: string;
  descripcion?: string | null;
  padre_id?: number | null;
}

export interface UpdateExpenseCategoryRequest {
  nombre?: string;
  descripcion?: string | null;
  padre_id?: number | null;
}

export const getGastosCategorias = async (padreId?: number | null): Promise<ExpenseCategory[]> => {
  try {
    const params = padreId !== undefined ? { padre_id: padreId } : {};
    const response = await api.get<ExpenseCategory[]>("/gastos-categorias", { params });
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const getGastoCategoriaById = async (id: number): Promise<ExpenseCategory> => {
  try {
    const response = await api.get<ExpenseCategory>(`/gastos-categorias/${id}`);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const createGastoCategoria = async (
  data: CreateExpenseCategoryRequest
): Promise<ExpenseCategory> => {
  try {
    const response = await api.post<ExpenseCategory>("/gastos-categorias", data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const updateGastoCategoria = async (
  id: number,
  data: UpdateExpenseCategoryRequest
): Promise<ExpenseCategory> => {
  try {
    const response = await api.put<ExpenseCategory>(`/gastos-categorias/${id}`, data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const deactivateGastoCategoria = async (id: number): Promise<void> => {
  try {
    await api.patch(`/gastos-categorias/${id}/desactivar`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};
