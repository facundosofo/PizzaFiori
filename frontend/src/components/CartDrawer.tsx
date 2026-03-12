import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { CartItem } from '../types/cart';
import { formatCurrency } from '../utils/formatters';
import * as Icons from './shared/Icons';
import '../styles/cart-drawer.css';
import '../styles/shared/quantity-controls.css';

interface CartDrawerProps {
  items: CartItem[];
  total: number;
  onUpdateQuantity: (itemId: string, newQuantity: number) => void;
  onRemoveItem: (itemId: string) => void;
  onClearCart: () => void;
  onConfirmSale: () => void;
  isConfirming?: boolean;
}

export const CartDrawer: React.FC<CartDrawerProps> = ({
  items,
  total,
  onUpdateQuantity,
  onRemoveItem,
  onClearCart,
  onConfirmSale,
  isConfirming = false,
}) => {
  const isEmpty = items.length === 0;

  // Calcular cantidad total de items (sumando cantidades y productos dentro de ofertas)
  const totalItems = useMemo(() => items.reduce((acc, item) => {
    if (item.tipo === 'oferta') {
      const productosEnOferta = item.productos_seleccionados.reduce((sum, p) => sum + p.cantidad, 0);
      return acc + productosEnOferta * item.cantidad;
    }
    return acc + item.cantidad;
  }, 0), [items]);

  return (
    <div className="cart-drawer">
      {/* Header */}
      <div className="cart-drawer-header">
        <div className="cart-drawer-header-main">
          <h2 className="cart-drawer-title">Carrito</h2>
          <p className="cart-drawer-subtitle">
            {isEmpty ? 'Sin items' : `${totalItems} ${totalItems === 1 ? 'item' : 'items'}`}
          </p>
        </div>
        {!isEmpty && (
          <button
            className="cart-btn cart-btn-clear"
            onClick={onClearCart}
            disabled={isConfirming}
          >
            <Icons.TrashIcon size={18} /> Vaciar
          </button>
        )}
      </div>

      {/* Items */}
      <div className="cart-drawer-items">
        {isEmpty ? (
          <div className="cart-empty">
            <div className="cart-empty-icon">
              <Icons.ShoppingCartIcon size={48} color="rgba(255, 255, 255, 0.3)" />
            </div>
            <p className="cart-empty-text">
              Agrega productos u ofertas para comenzar
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {items.map((item) => {
              const isOffer = item.tipo === 'oferta';
              const isPizzaMitadMitad = item.tipo === 'pizza_mitad_mitad';

              return (
                <motion.div
                  key={item.id}
                  className={`cart-item ${isOffer ? 'cart-item-offer' : ''} ${isPizzaMitadMitad ? 'cart-item-pizza-mitad' : ''}`}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="cart-item-header">
                    <div className="cart-item-info">
                      <h3 className="cart-item-name">
                        {isOffer && <Icons.DiscountIcon size={16} />}{' '}
                        {item.tipo === 'producto' ? item.producto_nombre : 
                         item.tipo === 'oferta' ? item.oferta_nombre :
                         item.tipo === 'pizza_mitad_mitad' ? item.nombre_completo :
                         'Item desconocido'}
                      </h3>
                      {item.tipo === 'producto' ? (
                        <p className="cart-item-category">{item.categoria_nombre}</p>
                      ) : item.tipo === 'pizza_mitad_mitad' ? (
                        <p className="cart-item-category">Pizzas</p>
                      ) : null}
                    </div>
                    <button
                      className="cart-item-remove"
                      onClick={() => onRemoveItem(item.id)}
                      title="Eliminar"
                    >
                      <Icons.TrashIcon size={18} />
                    </button>
                  </div>

                  {/* Offer details (expandable) */}
                  {isOffer && item.productos_seleccionados.length > 0 && (
                    <div className="cart-offer-details">
                      <div className="cart-offer-products">
                        {item.productos_seleccionados.map((product, index) => (
                          <div key={index} className="cart-offer-product-item">
                            <span className="cart-offer-product-qty">{product.cantidad}x</span>
                            <span className="cart-offer-product-name">{product.producto_nombre}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="cart-item-controls">
                    <div className="cart-item-quantity">
                      <div className="quantity-control">
                        <button
                          type="button"
                          className="qty-btn qty-btn-minus"
                          onClick={() => onUpdateQuantity(item.id, Math.max(1, item.cantidad - 1))}
                          aria-label="Disminuir cantidad"
                          disabled={item.cantidad <= 1}
                        >
                          <Icons.MinusIcon size={14} />
                        </button>

                        <input
                          type="number"
                          min="1"
                          className="qty-input"
                          value={item.cantidad}
                          onFocus={(e) => (e.target as HTMLInputElement).select()}
                          onChange={(e) => {
                            const newQty = Math.max(1, parseInt(e.target.value) || 1);
                            onUpdateQuantity(item.id, newQty);
                          }}
                        />

                        <button
                          type="button"
                          className="qty-btn qty-btn-plus"
                          onClick={() => onUpdateQuantity(item.id, item.cantidad + 1)}
                          aria-label="Aumentar cantidad"
                        >
                          <Icons.PlusIcon size={14} />
                        </button>
                      </div>
                    </div>
                    <div className="cart-item-subtotal">
                      {formatCurrency(item.subtotal)}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>

      {/* Footer */}
      <div className="cart-drawer-footer">
        <p className="cart-total-single">TOTAL: <span className="cart-total-amount">{formatCurrency(total)}</span></p>

        <div className="cart-actions">
          {/* Botón de vaciar movido al header */}
          <button
            className="cart-btn cart-btn-confirm"
            onClick={onConfirmSale}
            disabled={isEmpty || isConfirming}
          >
            {isConfirming ? (
                <>
                <Icons.ClockIcon size={18} /> Procesando...
              </>
            ) : (
                <>
                <Icons.CheckIcon size={18} color="currentColor" /> Confirmar
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
