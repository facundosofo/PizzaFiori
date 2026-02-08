import type { Category } from './category';
import type { ProductPrice } from './product_price';
import type { OfferItem } from './offer_item';

export interface Product {
  sku: string;
  id: number;
  nombre: string;
  categoria_id?: number | null;
  imagen?: string | null;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  categoria?: Category;
  precios?: ProductPrice[];
  ofertas?: OfferItem[];
}
