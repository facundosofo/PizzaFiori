import api from "./http";
import type { Offer, CreateOfferRequest, UpdateOfferRequest } from "../types/offer";

/**
 * Fetch all offers (active or all)
 */
export const getOfertas = async (active?: boolean): Promise<Offer[]> => {
  try {
    const response = await api.get<Offer[]>("/ofertas", {
      params: active !== undefined ? { active } : undefined,
    });
    if (!Array.isArray(response.data)) return [];
    // Ensure numeric fields from API decimals are mapped as numbers in frontend.
    return response.data.map(offer => ({
      ...offer,
      precio: Number(offer.precio),
      productos: offer.productos?.map((item) => ({
        ...item,
        cantidad: Number(item.cantidad),
      })),
    }));
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const getOfertaById = async (id: number): Promise<Offer> => {
  try {
    const response = await api.get<Offer>(`/ofertas/${id}`);
    return {
      ...response.data,
      precio: Number(response.data.precio),
      productos: response.data.productos?.map((item) => ({
        ...item,
        cantidad: Number(item.cantidad),
      })),
    };
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const createOffer = async (data: CreateOfferRequest): Promise<Offer> => {
  try {
    const response = await api.post<Offer>("/ofertas", data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const updateOffer = async (id: number, data: UpdateOfferRequest): Promise<Offer> => {
  try {
    const response = await api.put<Offer>(`/ofertas/${id}`, data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};

export const deactivateOffer = async (id: number): Promise<void> => {
  try {
    await api.patch(`/ofertas/${id}/desactivar`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    throw new Error(errorMessage);
  }
};
