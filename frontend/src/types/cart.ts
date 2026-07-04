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
  product_price_id?: number;
  precio_cantidad?: number;
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

// Pizza mitad-mitad item in cart
export interface CartPizzaMitadMitadItem extends CartItemBase {
  tipo: 'pizza_mitad_mitad';
  producto_id_izquierda: number;
  producto_id_derecha: number;
  // Nombre completo para mostrar: "Pizza Mitad Muzzarella/Carne"
  nombre_completo: string;
}

// Union type for any cart item
export type CartItem = CartProductItem | CartOfferItem | CartPizzaMitadMitadItem;

// Cart state
export interface CartState {
  items: CartItem[];
  total: number;
}
