import api from "./http";
import type { Expense } from "../types/expense";
import { formatDateYMD } from "../utils/formatters";

export interface CreateExpenseRequest {
  categoria_gasto_id: number;
  descripcion?: string | null;
  monto: number;
  fecha_pago: Date | string;
}

export interface UpdateExpenseRequest {
  categoria_gasto_id?: number;
  descripcion?: string | null;
  monto?: number;
  fecha_pago?: Date | string;
}

export const getGastos = async (
  fechaDesde?: Date | null,
  fechaHasta?: Date | null,
  categoriaGastoId?: number | null
): Promise<Expense[]> => {
  try {
    const params: Record<string, string> = {};

    if (fechaDesde) {
      params.fecha_desde = formatDateYMD(fechaDesde);
    }

    if (fechaHasta) {
      params.fecha_hasta = formatDateYMD(fechaHasta);
    }

    if (categoriaGastoId) {
      params.categoria_gasto_id = categoriaGastoId.toString();
    }

    const response = await api.get<Expense[]>("/gastos", { params });
    if (!Array.isArray(response.data)) return [];
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const getGastoById = async (id: number): Promise<Expense> => {
  try {
    const response = await api.get<Expense>(`/gastos/${id}`);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const createGasto = async (data: CreateExpenseRequest): Promise<Expense> => {
  try {
    const payload = {
      ...data,
      fecha_pago: data.fecha_pago instanceof Date
        ? formatDateYMD(data.fecha_pago)
        : data.fecha_pago,
    };
    const response = await api.post<Expense>("/gastos", payload);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const updateGasto = async (
  id: number,
  data: UpdateExpenseRequest
): Promise<Expense> => {
  try {
    const payload = {
      ...data,
      fecha_pago: data.fecha_pago instanceof Date
        ? formatDateYMD(data.fecha_pago)
        : data.fecha_pago,
    };
    const response = await api.put<Expense>(`/gastos/${id}`, payload);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const deleteGasto = async (id: number): Promise<void> => {
  try {
    await api.delete(`/gastos/${id}`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};
