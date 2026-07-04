import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import type { Sale } from "../types/sale";
import type { SaleItemWithDetails } from "../types/sale_item";
import { getSaleById } from "../services/salesService";
import { formatCurrency, formatDateTimeDisplay } from "../utils/formatters";
import { formatMixedFraction } from "../utils/soldQuantityFormatter";
import "../styles/sale-modal.css";
import * as Icons from './shared/Icons';
import ErrorAlert from './shared/ErrorAlert';

type SaleWithDetails = Omit<Sale, 'items'> & {
  items: SaleItemWithDetails[];
};

interface SaleDetailModalProps {
  saleId: number | null;
  isOpen: boolean;
  onClose: () => void;
}

const SaleDetailModal = ({
  saleId,
  isOpen,
  onClose,
}: SaleDetailModalProps) => {
  const [sale, setSale] = useState<SaleWithDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isSameQuantity = (a: number, b: number): boolean => Math.abs(a - b) < 1e-9;

  const toNumber = (value: unknown): number => {
    if (typeof value === 'number') return Number.isFinite(value) ? value : 0;
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      return Number.isFinite(parsed) ? parsed : 0;
    }
    return 0;
  };

  const formatQuantityForDetail = (
    quantity: number,
    baseQuantity?: number | null,
    itemName?: string,
    categoryName?: string,
  ): string => {
    if (!Number.isFinite(quantity) || quantity <= 0) return "0";
    return formatMixedFraction(quantity, { baseQuantity, itemName, categoryName });
  };

  const formatFractionLabelForDetail = (quantity: number, baseQuantity?: number | null): string => {
    if (!Number.isFinite(quantity) || quantity <= 0) return "";

    if (isSameQuantity(quantity, Math.round(quantity))) {
      return "Unidad entera";
    }

    if (baseQuantity && baseQuantity > 0) {
      if (isSameQuantity(baseQuantity, 0.5)) return "Porción 1/2";
      if (isSameQuantity(baseQuantity, 0.25)) return "Porción 1/4";
      if (isSameQuantity(baseQuantity, 0.125)) return "Porción 1/8";
    }

    if (isSameQuantity(quantity, 0.5)) return "Porción 1/2";
    if (isSameQuantity(quantity, 0.25)) return "Porción 1/4";
    if (isSameQuantity(quantity, 0.125)) return "Porción 1/8";

    const portionCount = Math.max(1, Math.round(quantity / 0.125));
    const fractionMap: Record<number, string> = {
      1: "Porción 1/8",
      2: "Porción 1/4",
      4: "Porción 1/2",
    };

    return fractionMap[portionCount] ?? `Porción ${portionCount}/8`;
  };

  const getSaleItemPriceDisplay = (item: SaleItemWithDetails): number => {
    const baseQuantity = toNumber(item.precio_cantidad);
    const unitPrice = toNumber(item.precio_unitario);

    if (baseQuantity > 0 && baseQuantity < 1) {
      return Number((unitPrice * baseQuantity).toFixed(2));
    }

    return unitPrice;
  };

  useEffect(() => {
    if (saleId && isOpen) {
      const fetchSale = async () => {
        try {
          setLoading(true);
          setError("");
          const data = await getSaleById(saleId);
          setSale(data);
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : "Error desconocido";
          setError(errorMessage);
        } finally {
          setLoading(false);
        }
      };

      fetchSale();
    }
  }, [saleId, isOpen]);

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="sale-modal-overlay"
          onClick={handleOverlayClick}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.div
            className="sale-modal-content sale-detail-modal"
            onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="sale-modal-header">
              <h2>Detalle de Venta</h2>
              <button
                className="sale-modal-close-btn"
                onClick={onClose}
                aria-label="Cerrar modal"
              >
                <Icons.XIcon size={18} />
              </button>
            </div>

            <div className="sale-modal-body">
              {loading ? (
                <div className="sale-detail-loading">
                  <motion.div
                    className="loading-spinner"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Icons.SpinnerIcon size={36} />
                  </motion.div>
                  <p>Cargando detalles...</p>
                </div>
              ) : error ? (
                <ErrorAlert message={error} onClose={() => setError("")} />
              ) : sale ? (
                <>
                  <div className="sale-info">
                    <div className="sale-info-row">
                      <span className="sale-info-label">N° Orden:</span>
                      <span className="sale-info-value">
                        {sale.numero_orden || `#${sale.id}`}
                      </span>
                    </div>
                    <div className="sale-info-row">
                      <span className="sale-info-label">Fecha:</span>
                      <span className="sale-info-value">
                        {formatDateTimeDisplay(sale.fecha_creacion)}
                      </span>
                    </div>
                    <div className="sale-info-row">
                      <span className="sale-info-label">Total Items:</span>
                      <span className="sale-info-value">
                        {(sale.total_items ?? 0)}
                      </span>
                    </div>
                  </div>

                  <div className="sale-items-section">
                    <h3>Productos / Ofertas</h3>
                    <div className="sale-items-table">
                      <div className="sale-items-header">
                        <div className="sale-item-col-name">Nombre</div>
                        <div className="sale-item-col-qty">Cantidad</div>
                        <div className="sale-item-col-price">Precio</div>
                        <div className="sale-item-col-subtotal">Subtotal</div>
                      </div>

                      {sale.items.map((item) => (
                        <div key={item.id} className="sale-items-row">
                          <div className="sale-item-col-name">
                            {item.item_nombre}
                            {item.item_descripcion && (
                              <div style={{ color: "rgba(255, 255, 255, 0.6)", fontSize: "0.85rem", marginTop: 2 }}>
                                {item.item_descripcion}
                              </div>
                            )}

                            {Number(item.cantidad) < 1 && (
                              <div className="sale-item-fraction-label">
                                {formatFractionLabelForDetail(Number(item.cantidad), item.precio_cantidad)}
                              </div>
                            )}

                            {item.oferta_id && item.oferta_productos_snapshot?.length ? (
                              <div style={{ marginTop: 6, paddingLeft: 14 }}>
                                {item.oferta_productos_snapshot.map((p) => (
                                  <div key={p.id} style={{ color: "rgba(255, 255, 255, 0.75)", fontSize: "0.9rem", fontWeight: 600 }}>
                                    - {p.cantidad * item.cantidad} {p.producto_nombre}
                                  </div>
                                ))}
                              </div>
                            ) : null}
                          </div>
                          <div className="sale-item-col-qty">
                            <div className="sale-quantity-stack">
                              <span className="sale-quantity-main">
                                {formatQuantityForDetail(
                                  Number(item.cantidad),
                                  item.precio_cantidad,
                                  item.item_nombre,
                                  item.item_categoria,
                                )}
                              </span>
                            </div>
                          </div>
                          <div className="sale-item-col-price">
                            {formatCurrency(getSaleItemPriceDisplay(item))}
                          </div>
                          <div className="sale-item-col-subtotal">
                            {formatCurrency(item.subtotal)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="sale-total-section">
                    {sale.monto_recargo && sale.monto_recargo > 0 ? (
                      <>
                        <div className="sale-total-row">
                          <span className="sale-total-label">Subtotal:</span>
                          <span className="sale-total-value">
                            {formatCurrency((sale.total - sale.monto_recargo))}
                          </span>
                        </div>
                        <div className="sale-total-row" style={{ color: "rgba(255, 165, 0, 0.9)" }}>
                          <span className="sale-total-label">Recargo ({sale.porcentaje_recargo}%):</span>
                          <span className="sale-total-value">
                            {formatCurrency(sale.monto_recargo)}
                          </span>
                        </div>
                      </>
                    ) : null}
                    <div className="sale-total-row">
                      <span className="sale-total-label">TOTAL:</span>
                      <span className="sale-total-value">
                        {formatCurrency(sale.total)}
                      </span>
                    </div>
                  </div>
                </>
              ) : null}
            </div>

            <div className="sales-modal-footer">
              <button className="sales-btn-close" onClick={onClose}>
                Cerrar
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SaleDetailModal;
