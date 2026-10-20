import api from "./http";

export interface RecargoConfig {
  porcentaje_recargo: number;
}

export interface CatalogPublishStatus {
  publicado_en: string | null;
}

export interface CatalogPublishResult {
  publicado_en: string;
  catalogo_version: string;
  catalogo_url: string;
  categorias: number;
  productos: number;
  ofertas: number;
  actualizado: boolean;
}

export const getCatalogPublishStatus = async (): Promise<CatalogPublishStatus> => {
  const response = await api.get<CatalogPublishStatus>("/config/catalog/status");
  return response.data;
};

export const publishCatalog = async (): Promise<CatalogPublishResult> => {
  const response = await api.post<CatalogPublishResult>("/config/catalog/publish");
  return response.data;
};

/**
 * Get current surcharge percentage configuration
 */
export const getRecargoConfig = async (): Promise<RecargoConfig> => {
  try {
    const response = await api.get<RecargoConfig>("/config/recargo");
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

/**
 * Update surcharge percentage configuration
 */
export const updateRecargoConfig = async (porcentaje_recargo: number): Promise<RecargoConfig> => {
  try {
    const response = await api.put<RecargoConfig>("/config/recargo", {
      porcentaje_recargo,
    });
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};
