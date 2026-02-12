import api from "./http";
import type { Category } from "../types/category";

export const getCategorias = async (): Promise<Category[]> => {
  try {
    const response = await api.get<Category[]>("/categorias");
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching categorías:", err);
    throw new Error(errorMessage);
  }
};
