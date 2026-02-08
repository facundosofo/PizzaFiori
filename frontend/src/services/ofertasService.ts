import env from "../config/env";
import type { Offer, CreateOfferRequest, UpdateOfferRequest } from "../types/offer";
import type { Product } from "../types/product";

/**
 * Fetch all offers (active or all)
 */
export const getOfertas = async (active?: boolean): Promise<Offer[]> => {
  try {
    const url = active !== undefined
      ? `${env.API_BASE_URL}/ofertas?active=${active}`
      : `${env.API_BASE_URL}/ofertas`;
    const res = await fetch(url);
    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "No se encontraron ofertas"
        : res.status === 500
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudieron obtener las ofertas";
      throw new Error(errorMsg);
    }
    const data = await res.json();
    // Ensure precio is a number
    return (data as Offer[]).map(offer => ({
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
    const res = await fetch(`${env.API_BASE_URL}/ofertas/${id}`);
    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Oferta no encontrada"
        : res.status === 500
        ? "Error del servidor. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo obtener la oferta";
      throw new Error(errorMsg);
    }
    const data = await res.json();
    return data as Offer;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error fetching oferta by ID:", err);
    throw new Error(errorMessage);
  }
};

export const createOffer = async (data: CreateOfferRequest): Promise<Offer> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorMsg = res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 404
        ? "Uno o más productos no encontrados"
        : res.status === 500
        ? "Error al crear la oferta. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo crear la oferta";
      throw new Error(errorMsg);
    }

    return (await res.json()) as Offer;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error creating oferta:", err);
    throw new Error(errorMessage);
  }
};

export const updateOffer = async (id: number, data: UpdateOfferRequest): Promise<Offer> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Oferta no encontrada"
        : res.status === 400
        ? "Datos inválidos. Verifica que todos los campos sean correctos."
        : res.status === 500
        ? "Error al guardar los cambios. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo actualizar la oferta";
      throw new Error(errorMsg);
    }

    return (await res.json()) as Offer;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error updating oferta:", err);
    throw new Error(errorMessage);
  }
};

export const deactivateOffer = async (id: number): Promise<void> => {
  try {
    const res = await fetch(`${env.API_BASE_URL}/ofertas/${id}/desactivar`, {
      method: "PATCH",
      headers: {
        accept: "application/json",
      },
    });

    if (!res.ok) {
      const errorMsg = res.status === 404
        ? "Oferta no encontrada"
        : res.status === 500
        ? "Error al desactivar la oferta. El administrador ha sido notificado."
        : res.status === 503
        ? "El servidor no está disponible. Intenta más tarde."
        : "No se pudo desactivar la oferta";
      throw new Error(errorMsg);
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Error desconocido";
    console.error("Error deactivating oferta:", err);
    throw new Error(errorMessage);
  }
};
