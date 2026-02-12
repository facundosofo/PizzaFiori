import api from "./http";
import type { Offer, CreateOfferRequest, UpdateOfferRequest } from "../types/offer";
import type { Product } from "../types/product";

/**
 * Fetch all offers (active or all)
 */
export const getOfertas = async (active?: boolean): Promise<Offer[]> => {
  try {
    const response = await api.get<Offer[]>("/ofertas", {
      params: active !== undefined ? { active } : undefined,
    });
    // Ensure precio is a number
    return response.data.map(offer => ({
      ...offer,
      precio: Number(offer.precio)
    }));
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching ofertas:", err);
    throw new Error(errorMessage);
  }
};

export const getOfertaById = async (id: number): Promise<Offer> => {
  try {
    const response = await api.get<Offer>(`/ofertas/${id}`);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching oferta by ID:", err);
    throw new Error(errorMessage);
  }
};

export const createOffer = async (data: CreateOfferRequest): Promise<Offer> => {
  try {
    const response = await api.post<Offer>("/ofertas", data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error creating oferta:", err);
    throw new Error(errorMessage);
  }
};

export const updateOffer = async (id: number, data: UpdateOfferRequest): Promise<Offer> => {
  try {
    const response = await api.put<Offer>(`/ofertas/${id}`, data);
    return response.data;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error updating oferta:", err);
    throw new Error(errorMessage);
  }
};

export const deactivateOffer = async (id: number): Promise<void> => {
  try {
    await api.patch(`/ofertas/${id}/desactivar`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error deactivating oferta:", err);
    throw new Error(errorMessage);
  }
};
