/**
 * Cart types for Sales Creation module
 * Manages products and offers with quantity controls
 */

// Base cart item interface
export interface CartItemBase {
  id: string; // Unique ID for cart item (generated client-side)
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

// Product item in cart
export interface CartProductItem extends CartItemBase {
  tipo: 'producto';
  producto_id: number;
  producto_nombre: string;
  categoria_nombre: string;
  imagen?: string | null;
}

// Offer item in cart
export interface CartOfferItem extends CartItemBase {
  tipo: 'oferta';
  oferta_id: number;
  oferta_nombre: string;
  oferta_descripcion?: string | null;
  // Selected products for this offer instance
  productos_seleccionados: {
    producto_id: number;
    producto_nombre: string;
    cantidad: number;
  }[];
}

// Union type for any cart item
export type CartItem = CartProductItem | CartOfferItem;

// Cart state
export interface CartState {
  items: CartItem[];
  total: number;
}
