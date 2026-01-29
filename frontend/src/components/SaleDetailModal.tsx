import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import type { Sale } from "../types/sale";
import type { SaleItemWithDetails } from "../types/sale_item";
import { getSaleById } from "../services/salesService";
import { formatCurrency, formatDateDisplay } from "../utils/formatters";
import "../styles/sale-modal.css";

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
          console.error("Error fetching sale details:", err);
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
                ✕
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
                    ⟳
                  </motion.div>
                  <p>Cargando detalles...</p>
                </div>
              ) : error ? (
                <div className="sale-detail-error">
                  <p>❌ {error}</p>
                </div>
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
                        {formatDateDisplay(sale.fecha_creacion)}
                      </span>
                    </div>
                    <div className="sale-info-row">
                      <span className="sale-info-label">Total Items:</span>
                      <span className="sale-info-value">
                        {sale.items.reduce((sum, item) => sum + item.cantidad, 0)}
                      </span>
                    </div>
                  </div>

                  <div className="sale-items-section">
                    <h3>Productos / Ofertas</h3>
                    <div className="sale-items-table">
                      <div className="sale-items-header">
                        <div className="sale-item-col-name">Nombre</div>
                        <div className="sale-item-col-qty">Cant.</div>
                        <div className="sale-item-col-price">P. Unit.</div>
                        <div className="sale-item-col-subtotal">Subtotal</div>
                      </div>

                      {sale.items.map((item) => (
                        <div key={item.id} className="sale-items-row">
                          <div className="sale-item-col-name">
                            {item.producto_nombre || item.oferta_nombre || "Producto/Oferta no encontrado"}
                            {item.producto_id && (
                              <span className="sale-item-type"> (Producto)</span>
                            )}
                            {item.oferta_id && (
                              <span className="sale-item-type"> (Oferta)</span>
                            )}
                          </div>
                          <div className="sale-item-col-qty">{item.cantidad}</div>
                          <div className="sale-item-col-price">
                            {formatCurrency(item.precio_unitario)}
                          </div>
                          <div className="sale-item-col-subtotal">
                            {formatCurrency(item.subtotal)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="sale-total-section">
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
