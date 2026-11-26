import type { SaleItem, SaleItemRequest, SaleItemUpdateRequest } from './sale_item';

export interface Sale {
  id: number;
  numero_orden?: string | null;
  total_items?: number;
  total: number;
  porcentaje_recargo?: number | null;
  monto_recargo?: number | null;
  fecha_creacion: string;
  fecha_actualizacion: string;
  items: SaleItem[];
}

export interface SaleCreateRequest {
  numero_orden?: string | null;
  items: SaleItemRequest[];
  aplicar_recargo?: boolean;
}

export interface SaleUpdateRequest {
  items: SaleItemUpdateRequest[];
  aplicar_recargo?: boolean;
}
