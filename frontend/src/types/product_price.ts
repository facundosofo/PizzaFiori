import type { Product } from './product';

export interface ProductPrice {
  id: number;
  producto_id: number;
  cantidad: number;
  precio: number;
  fecha_creacion: string;
  fecha_actualizacion: string;
  producto?: Product;
}
