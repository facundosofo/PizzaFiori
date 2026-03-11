import type { Offer } from './offer';

export interface ProductoOpcion {
  id: number;
  nombre: string;
  imagen?: string | null;
}

export interface OfferItem {
  id: number;
  oferta_id: number;
  categoria_id?: number | null;
  cantidad: number;
  categoria_nombre?: string | null;
  productos?: ProductoOpcion[];
  oferta?: Offer;
}

export interface OfferItemRequest {
  producto_id?: number;
  categoria_id?: number;
  producto_opciones?: number[];
  cantidad: number;
}
