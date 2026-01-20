import type { OfferItem } from './offer_item';

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
