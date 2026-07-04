import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { CartItem } from '../types/cart';
import { formatCurrency } from '../utils/formatters';
import { formatMixedFraction } from '../utils/soldQuantityFormatter';
import * as Icons from './shared/Icons';
import '../styles/cart-drawer.css';
import '../styles/shared/quantity-controls.css';

interface CartDrawerProps {
  items: CartItem[];
  total: number;
  aplicarRecargo: boolean;
  recargoPercent: number;
  recargoAmount: number;
  onToggleRecargo: () => void;
  onUpdateQuantity: (itemId: string, newQuantity: number) => void;
  onRemoveItem: (itemId: string) => void;
  onClearCart: () => void;
  onConfirmSale: () => void;
  isConfirming?: boolean;
}

const formatCartItemCantidadLabel = (cantidad: number): string => {
  if (Math.abs(cantidad - 1) < 1e-9) return 'Unidad';
  if (Math.abs(cantidad - 0.5) < 1e-9) return 'Porción 1/2';
  if (Math.abs(cantidad - 0.25) < 1e-9) return 'Porción 1/4';
  if (Math.abs(cantidad - 0.125) < 1e-9) return 'Porción 1/8';
  return `${cantidad}`;
};

const getFractionDenominator = (value: number): 2 | 4 | 8 => {
  const normalized = Math.abs(value);
  if (Math.abs(normalized * 4 - Math.round(normalized * 4)) < 1e-9) {
    return 4;
  }
  if (Math.abs(normalized * 2 - Math.round(normalized * 2)) < 1e-9) {
    return 2;
  }
  return 8;
};

const formatQuantityWithX = (value: number): string => {
  const denominator = getFractionDenominator(value);
  return `${formatMixedFraction(value, { fallbackDenominator: denominator })}x`;
};

export const CartDrawer: React.FC<CartDrawerProps> = ({
  items,
  total,
  aplicarRecargo,
  recargoPercent,
  recargoAmount,
  onToggleRecargo,
  onUpdateQuantity,
  onRemoveItem,
  onClearCart,
  onConfirmSale,
  isConfirming = false,
}) => {
  const isEmpty = items.length === 0;

  const getMaxQuantityForPortionPrice = (priceCantidad?: number) => {
    if (!priceCantidad || priceCantidad >= 1) return null;

    const maxQuantity = Math.round(1 / priceCantidad) - 1;
    return Number.isFinite(maxQuantity) && maxQuantity > 0 ? maxQuantity : null;
  };

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
              const maxQuantity = item.tipo === 'producto'
                ? getMaxQuantityForPortionPrice(item.precio_cantidad)
                : null;
              const isAtMaxQuantity = maxQuantity !== null && item.cantidad >= maxQuantity;

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
                        {item.tipo === 'producto' ? (
                          item.precio_cantidad && item.precio_cantidad < 1 ?
                            `${item.producto_nombre} - ${formatCartItemCantidadLabel(item.precio_cantidad)}` :
                            item.producto_nombre
                        ) : item.tipo === 'oferta' ? item.oferta_nombre :
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
                            <span className="cart-offer-product-qty">{formatQuantityWithX(product.cantidad)}</span>
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
                          max={maxQuantity ?? 1000}
                          className="qty-input"
                          value={item.cantidad}
                          onFocus={(e) => (e.target as HTMLInputElement).select()}
                          onChange={(e) => {
                            const rawQty = Math.max(1, parseInt(e.target.value) || 1);
                            onUpdateQuantity(item.id, maxQuantity !== null ? Math.min(rawQty, maxQuantity) : rawQty);
                          }}
                        />

                        <button
                          type="button"
                          className="qty-btn qty-btn-plus"
                          onClick={() => !isAtMaxQuantity && onUpdateQuantity(item.id, item.cantidad + 1)}
                          aria-label="Aumentar cantidad"
                          disabled={isAtMaxQuantity}
                        >
                          <Icons.PlusIcon size={14} />
                        </button>
                      </div>
                      {maxQuantity !== null && (
                        <p className="cart-item-quantity-hint">
                          Máximo {maxQuantity} porciones
                        </p>
                      )}
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
        <div className="cart-recargo-row">
          <label className="cart-recargo-label">
            <input
              type="checkbox"
              checked={aplicarRecargo}
              onChange={onToggleRecargo}
              disabled={isEmpty || isConfirming}
            />
            Aplicar recargo por transferencia/débito
          </label>
        </div>

        {aplicarRecargo && (
          <div className="cart-recargo-summary">
            <span>Recargo ({recargoPercent}%):</span>
            <span>{formatCurrency(recargoAmount)}</span>
          </div>
        )}

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
