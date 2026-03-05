import api from "./http";
import type { Product, BulkPriceUpdateRequest, BulkPriceUpdateResponse } from "../types/product";

export const createProducto = async (
  data: {
    nombre: string;
    categoria_id: number;
    imagen?: File | null;
    precios?: Array<{ cantidad: number; precio: number }>;
  }
): Promise<Product> => {
  try {
    const formData = new FormData();

    formData.append("nombre", data.nombre);
    formData.append("categoria_id", data.categoria_id.toString());
    if (data.precios) formData.append("precios", JSON.stringify(data.precios));
    if (data.imagen) formData.append("imagen", data.imagen);

    const response = await api.post<Product>("/productos", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const getProductos = async (categoriaId?: number): Promise<Product[]> => {
  try {
    const params: Record<string, any> = { active: true };
    if (categoriaId !== undefined) {
      params.categoria = categoriaId;
    }
    const response = await api.get<Product[]>("/productos", { params });
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const updateProducto = async (
  id: number,
  data: {
    nombre?: string;
    categoria_id?: number;
    imagen?: File | null;
    descripcion?: string;
    activo?: boolean;
    precios?: Array<{ cantidad: number; precio: number }>;
  }
): Promise<Product> => {
  try {
    const formData = new FormData();

    if (data.nombre) formData.append("nombre", data.nombre);
    if (data.categoria_id !== undefined) formData.append("categoria_id", data.categoria_id.toString());
    if (data.descripcion) formData.append("descripcion", data.descripcion);
    if (data.activo !== undefined) formData.append("activo", data.activo.toString());
    if (data.precios) formData.append("precios", JSON.stringify(data.precios));
    if (data.imagen) formData.append("imagen", data.imagen);

    const response = await api.put<Product>(`/productos/${id}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const deactivateProducto = async (id: number): Promise<void> => {
  try {
    await api.patch(`/productos/${id}/desactivar`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const actualizarPreciosMasivos = async (
  data: BulkPriceUpdateRequest
): Promise<BulkPriceUpdateResponse> => {
  try {
    const response = await api.patch<BulkPriceUpdateResponse>(
      "/productos/actualizar-precios",
      data
    );
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};