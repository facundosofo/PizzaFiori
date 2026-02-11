import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Offer, OfferItem } from '../types/offer';
import type { Product } from '../types/product';
import type { ProductoOpcion } from '../types/offer_item';
import '../styles/shared/quantity-controls.css';
import '../styles/offer-config-modal.css';
import * as Icons from './shared/Icons';

interface OfferConfigModalProps {
  offer: Offer;
  products: Product[];
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedProducts: { producto_id: number; producto_nombre: string; cantidad: number }[]) => void;
}

type ItemType = 'fixed' | 'category' | 'options';

interface ConfigurableItem {
  item: OfferItem;
  type: ItemType;
  index: number;
}

export const OfferConfigModal: React.FC<OfferConfigModalProps> = ({
  offer,
  products,
  isOpen,
  onClose,
  onConfirm,
}) => {
  // Map of itemIndex -> Map<productId, quantity> for category items
  const [categorySelections, setCategorySelections] = useState<Map<number, Map<number, number>>>(new Map());
  // Map of itemIndex -> selectedProductId for option items
  const [optionSelections, setOptionSelections] = useState<Map<number, number>>(new Map());

  // Classify each offer item
  const getItemType = (item: OfferItem): ItemType => {
    // Fixed: has exactly 1 product in productos array and no categoria_id
    if (item.productos && item.productos.length === 1 && !item.categoria_id) {
      return 'fixed';
    }
    // Category: has categoria_id
    if (item.categoria_id !== null && item.categoria_id !== undefined) {
      return 'category';
    }
    // Options: has multiple products in productos array
    if (item.productos && item.productos.length > 1) {
      return 'options';
    }
    return 'fixed';
  };

  // Get all configurable items (not fixed)
  const configurableItems: ConfigurableItem[] = (offer.productos || [])
    .map((item, index) => ({ item, type: getItemType(item), index }))
    .filter(({ type }) => type !== 'fixed');

  // Fixed items (to show when there is nothing to configure)
  const fixedItems = (offer.productos || [])
    .map((item, index) => ({ item, type: getItemType(item), index }))
    .filter(({ type }) => type === 'fixed');

  // Check if configuration is complete
  const isComplete = (): boolean => {
    for (const { type, item, index } of configurableItems) {
      if (type === 'category') {
        const selections = categorySelections.get(index);
        if (!selections) return false;
        const total = Array.from(selections.values()).reduce((sum, qty) => sum + qty, 0);
        if (total !== item.cantidad) return false;
      } else if (type === 'options') {
        if (!optionSelections.has(index)) return false;
      }
    }
    return true;
  };

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setCategorySelections(new Map());
      setOptionSelections(new Map());
    }
  }, [isOpen, offer.id]);

  // Autofocus first qty input when modal opens
  const modalRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!isOpen) return;
    const t = setTimeout(() => {
      const el = document.querySelector('.offer-config-modal .qty-input') as HTMLInputElement | null;
      if (el) {
        try {
          el.focus();
          el.select();
        } catch (err) {
          /* ignore */
        }
      }
    }, 60);
    return () => clearTimeout(t);
  }, [isOpen]);

  // Handle quantity change for category-based
  const handleQuantityChange = (itemIndex: number, productId: number, change: number) => {
    const item = configurableItems.find(ci => ci.index === itemIndex)?.item;
    if (!item) return;

    setCategorySelections((prev) => {
      const newMap = new Map(prev);
      const itemMap = newMap.get(itemIndex) || new Map<number, number>();
      
      const currentQty = itemMap.get(productId) || 0;
      const newQty = Math.max(0, currentQty + change);
      
      // Don't allow exceeding required quantity
      const currentTotal = Array.from(itemMap.values()).reduce((sum, qty) => sum + qty, 0);
      const newTotal = currentTotal - currentQty + newQty;
      if (newTotal > item.cantidad) return prev;

      const newItemMap = new Map(itemMap);
      if (newQty === 0) {
        newItemMap.delete(productId);
      } else {
        newItemMap.set(productId, newQty);
      }
      
      newMap.set(itemIndex, newItemMap);
      return newMap;
    });
  };

  // Handle option selection
  const handleOptionSelect = (itemIndex: number, productId: number) => {
    setOptionSelections((prev) => {
      const newMap = new Map(prev);
      newMap.set(itemIndex, productId);
      return newMap;
    });
  };

  // Handle confirm
  const handleConfirm = () => {
    const result: { producto_id: number; producto_nombre: string; cantidad: number }[] = [];

    // Add all items (fixed + configured)
    (offer.productos || []).forEach((item, index) => {
      const type = getItemType(item);

      if (type === 'fixed') {
        // Fixed product
        if (item.productos && item.productos.length === 1) {
          result.push({
            producto_id: item.productos[0].id,
            producto_nombre: item.productos[0].nombre,
            cantidad: item.cantidad,
          });
        }
      } else if (type === 'category') {
        // Category-based selections
        const selections = categorySelections.get(index);
        if (selections) {
          selections.forEach((cantidad, producto_id) => {
            const product = products.find((p) => p.id === producto_id);
            if (product) {
              result.push({
                producto_id,
                producto_nombre: product.nombre,
                cantidad,
              });
            }
          });
        }
      } else if (type === 'options') {
        // Option-based selection
        const selectedProductId = optionSelections.get(index);
        if (selectedProductId !== undefined && item.productos) {
          const productOption = item.productos.find((p) => p.id === selectedProductId);
          if (productOption) {
            result.push({
              producto_id: selectedProductId,
              producto_nombre: productOption.nombre,
              cantidad: item.cantidad,
            });
          }
        }
      }
    });

    onConfirm(result);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="offer-config-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="offer-config-modal"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="offer-config-header">
            <h2 className="offer-config-title">{offer.nombre}</h2>
            <p className="offer-config-subtitle">
              {offer.descripcion || 'Configura tu promoción'}
            </p>
            <button className="offer-config-close" onClick={onClose} aria-label="Cerrar">
              <Icons.XIcon size={16} />
            </button>
          </div>

          {/* Content */}
          <div className="offer-config-content">
            {configurableItems.length > 0 ? (
              configurableItems.map(({ item, type, index }) => (
                <div key={index} className="offer-config-item-section">
                  {/* Category-based configuration */}
                  {type === 'category' && (
                    <div className="offer-config-category">
                      <div className="offer-config-category-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                        <h3 className="offer-config-category-title" style={{ margin: 0 }}>
                          {item.categoria_nombre || 'Productos disponibles'} ({item.cantidad}x)
                        </h3>
                        <div className="offer-config-counter">
                          {(() => {
                            const selections = categorySelections.get(index);
                            const total = selections
                              ? Array.from(selections.values()).reduce((sum, qty) => sum + qty, 0)
                              : 0;
                            return `${total} / ${item.cantidad} seleccionados`;
                          })()}
                        </div>
                      </div>

                      <div className="offer-config-products-grid">
                        {products
                          .filter((p) => p.categoria_id === item.categoria_id && p.activo)
                          .map((product) => {
                            const selections = categorySelections.get(index);
                            const qty = selections?.get(product.id) || 0;
                            const currentTotal = selections
                              ? Array.from(selections.values()).reduce((sum, q) => sum + q, 0)
                              : 0;
                            const canIncrease = currentTotal < item.cantidad;

                            return (
                              <div key={product.id} className="offer-config-product-card">
                                <p className="offer-config-product-name">{product.nombre}</p>
                                    <div className="quantity-control">
                                      <button
                                        type="button"
                                        className="qty-btn qty-btn-minus"
                                        onClick={() => handleQuantityChange(index, product.id, -1)}
                                        disabled={qty === 0}
                                        aria-label="Disminuir cantidad"
                                      >
                                        <Icons.MinusIcon size={14} />
                                      </button>

                                      <input
                                        type="number"
                                        min="0"
                                        className="qty-input"
                                        value={qty}
                                        onFocus={(e) => (e.target as HTMLInputElement).select()}
                                        onClick={(e) => (e.target as HTMLInputElement).select()}
                                        onMouseUp={(e) => (e.target as HTMLInputElement).select()}
                                        onChange={(e) => {
                                          const v = parseInt((e.target as HTMLInputElement).value) || 0;
                                          const delta = v - qty;
                                          if (delta > 0) {
                                            const toAdd = Math.min(delta, item.cantidad - currentTotal);
                                            handleQuantityChange(index, product.id, toAdd);
                                          } else if (delta < 0) {
                                            handleQuantityChange(index, product.id, delta);
                                          }
                                        }}
                                        aria-label="Cantidad"
                                        readOnly={false}
                                      />

                                      <button
                                        type="button"
                                        className="qty-btn qty-btn-plus"
                                        onClick={() => handleQuantityChange(index, product.id, 1)}
                                        disabled={!canIncrease}
                                        aria-label="Aumentar cantidad"
                                      >
                                        <Icons.PlusIcon size={14} />
                                      </button>
                                    </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  )}

                  {/* Options-based configuration */}
                  {type === 'options' && item.productos && (
                    <div className="offer-config-options-section">
                      <h3 className="offer-config-category-title">
                        Selecciona una opción ({item.cantidad}x)
                      </h3>
                      <div className="offer-config-options">
                        {item.productos.map((productOption) => {
                          const isSelected = optionSelections.get(index) === productOption.id;
                          return (
                            <div
                              key={productOption.id}
                              className={`offer-config-option ${isSelected ? 'selected' : ''}`}
                              onClick={() => handleOptionSelect(index, productOption.id)}
                            >
                              <div className="offer-config-option-radio">
                                <div className="offer-config-option-radio-dot"></div>
                              </div>
                              <span className="offer-config-option-name">{productOption.nombre}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="offer-config-fixed-list">
                {fixedItems.length > 0 ? (
                  fixedItems.map(({ item }, idx) => (
                    <div key={idx} className="offer-config-fixed-item">
                      <div className="offer-config-fixed-name">{item.productos?.[0]?.nombre || 'Producto'}</div>
                      <div className="offer-config-fixed-qty">{item.cantidad}x</div>
                    </div>
                  ))
                ) : (
                  <div className="offer-config-empty">No hay elementos para configurar</div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="offer-config-footer">
            <button className="offer-config-btn offer-config-btn-cancel form-cancel-btn" onClick={onClose}>
              Cancelar
            </button>
            <button
              className="offer-config-btn offer-config-btn-confirm form-save-btn"
              onClick={handleConfirm}
              disabled={!isComplete()}
            >
              <Icons.CheckIcon size={16} /> Agregar al Carrito
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
