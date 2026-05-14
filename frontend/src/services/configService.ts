import api from "./http";

export interface RecargoConfig {
  porcentaje_recargo: number;
}

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
