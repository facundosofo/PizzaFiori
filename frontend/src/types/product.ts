import type { ProductoCategoria } from './product_category';
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
  categoria?: ProductoCategoria;
  precios?: ProductPrice[];
  ofertas?: OfferItem[];
}

export interface BulkPriceUpdateRequest {
  monto?: number;
  porcentaje?: number;
  categoria_ids?: number[];
}

export interface BulkPriceUpdateResponse {
  productos_actualizados: number;
  productos: Product[];
}
