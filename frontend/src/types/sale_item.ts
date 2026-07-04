// Snapshot de un producto incluido en una oferta vendida
export interface SaleItemOfferProductSnapshot {
  id: number;
  producto_id?: number | null;
  producto_nombre: string;
  categoria_nombre?: string | null;
  cantidad: number;
}

export interface SaleItem {
  id: number;
  producto_id?: number | null;
  oferta_id?: number | null;
  cantidad: number;
  precio_cantidad?: number | null;
  precio_unitario: number;
  subtotal: number;
  // Campos de snapshot (preservan datos históricos)
  producto_sku?: string | null;
  item_nombre: string;
  item_categoria: string;
  item_descripcion?: string | null;
  oferta_productos_snapshot?: SaleItemOfferProductSnapshot[];
}

export interface SaleItemRequest {
  producto_id?: number | null;
  oferta_id?: number | null;
  cantidad: number;
  precio_cantidad?: number | null;
  precio_unitario?: number; // Requerido para updates
  productos_seleccionados?: { producto_id: number; cantidad: number }[];
  pizza_mitad_mitad?: {
    producto_id_izquierda: number;
    producto_id_derecha: number;
    cantidad: number;
  };
}

// Extended interface with product/offer names (populated by backend via snapshots)
export interface SaleItemWithDetails extends SaleItem {
  // Estos campos vienen del snapshot, no necesitamos buscarlos
  producto_nombre?: string; // Deprecated: usar item_nombre
  oferta_nombre?: string;   // Deprecated: usar item_nombre
}
