import type { Offer } from './offer';
import type { Product } from './product';

export interface OfferItem {
  id: number;
  oferta_id: number;
  producto_id: number;
  cantidad: number;
  oferta?: Offer;
  producto?: Product;
}
