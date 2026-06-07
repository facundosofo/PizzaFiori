import type { OfferItem, OfferItemRequest } from './offer_item';

// Re-exportar OfferItem para facilitar imports
export type { OfferItem } from './offer_item';

export interface Offer {
  id: number;
  nombre: string;
  descripcion?: string | null;
  precio: number;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  productos?: OfferItem[];
}

export interface CreateOfferRequest {
  nombre: string;
  descripcion?: string;
  precio: number;
  productos: OfferItemRequest[];
}

export interface UpdateOfferRequest {
  nombre?: string;
  descripcion?: string;
  precio?: number;
  productos?: OfferItemRequest[];
}
