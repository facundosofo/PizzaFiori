import type { SaleItem, SaleItemRequest } from './sale_item';

export interface Sale {
  id: number;
  numero_orden?: string | null;
  total: number;
  fecha_creacion: string;
  fecha_actualizacion: string;
  items: SaleItem[];
}

export interface SaleCreateRequest {
  numero_orden?: string | null;
  items: SaleItemRequest[];
}
