export interface SaleItem {
  id: number;
  producto_id?: number | null;
  oferta_id?: number | null;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface SaleItemRequest {
  producto_id?: number | null;
  oferta_id?: number | null;
  cantidad: number;
  precio_unitario?: number; // Requerido para updates
}

// Extended interface with product/offer names (populated by frontend)
export interface SaleItemWithDetails extends SaleItem {
  producto_nombre?: string;
  oferta_nombre?: string;
}
