import env from "../config/env";
import type { Product } from "../types/product";

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

    const res = await fetch(`${env.API_BASE_URL}/productos`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errorMsg = res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 500
        ? "Error al crear el producto. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo crear el producto";
      throw new Error(errorMsg);
    }
    return (await res.json()) as Product;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error creating producto:", err);
    throw new Error(errorMessage);
  }
};

export const getProductos = async (): Promise<Product[]> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/productos?active=true`);
    if (!res.ok) {
      const errorMsg = res.status === 404 
        ? "No se encontraron productos" 
        : res.status === 500 
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudieron obtener los productos";
      throw new Error(errorMsg);
    }
    const data = await res.json();
    return data as Product[];
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching productos:", err);
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

    const res = await fetch(`${env.API_BASE_URL}/productos/${id}`, {
      method: "PUT",
      body: formData,
    });

    if (!res.ok) {
      const errorMsg = res.status === 404 
        ? "Producto no encontrado"
        : res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 500
        ? "Error al guardar los cambios. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo actualizar el producto";
      throw new Error(errorMsg);
    }
    return (await res.json()) as Product;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error updating producto:", err);
    throw new Error(errorMessage);
  }
};

export const deleteProducto = async (id: number): Promise<void> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/productos/${id}`, {
      method: "DELETE",
      headers: {
        accept: "application/json",
      },
    });

    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Producto no encontrado"
        : res.status === 500
        ? "Error al eliminar el producto. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo eliminar el producto";
      throw new Error(errorMsg);
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error deleting producto:", err);
    throw new Error(errorMessage);
  }
};
