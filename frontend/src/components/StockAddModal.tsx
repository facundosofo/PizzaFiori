import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Icons from "./shared/Icons";
import type { CategoryStock } from "../types/stock";
import { addStock } from "../services/stockService";
import "../styles/stock-add-modal.css";
import "../styles/shared/quantity-controls.css";

interface StockAddModalProps {
  isOpen: boolean;
  categoria: CategoryStock | null;
  onClose: () => void;
  onSave: (updated: CategoryStock) => void;
}

const StockAddModal = ({
  isOpen,
  categoria,
  onClose,
  onSave,
}: StockAddModalProps) => {
  const [delta, setDelta] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      setDelta(0);
      setError("");
    }
  }, [isOpen]);

  const handleDeltaChange = (raw: string) => {
    if (raw === "" || raw === "-") { setDelta(0); return; }
    const n = parseInt(raw, 10);
    if (!isNaN(n)) setDelta(n);
  };

  const handleSave = async () => {
    setError("");
    if (delta === 0) return;
    if (!categoria) return;

    setLoading(true);
    try {
      const updated = await addStock(categoria.categoria_id, { cantidad: delta });
      onSave(updated);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al ajustar stock");
    } finally {
      setLoading(false);
    }
  };

  const nuevoStock = categoria ? Math.max(0, categoria.cantidad + delta) : 0;
  const deltaLabel =
    delta > 0 ? `+${delta}` : delta < 0 ? `−${Math.abs(delta)}` : "0";
  const canSubmit = delta !== 0 && !loading;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="stock-add-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="stock-add-modal"
            initial={{ scale: 0.92, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="stock-add-modal-header">
              <div>
                <p className="stock-add-modal-eyebrow">Stock</p>
                <h2 className="stock-add-modal-title">
                  Modificar —{" "}
                  <span className="stock-add-modal-category">
                    {categoria?.categoria_nombre}
                  </span>
                </h2>
              </div>
              <button
                className="stock-add-modal-close"
                onClick={onClose}
                disabled={loading}
              >
                <Icons.XIcon size={18} />
              </button>
            </div>

            {/* Body */}
            <div className="stock-add-modal-body">
              {/* Stock actual */}
              <div className="stock-add-current-row">
                <span className="stock-add-current-label">Stock actual</span>
                <span className="stock-add-current-value">
                  {categoria?.cantidad ?? 0} unidades
                </span>
              </div>

              {/* Control - delta + */}
              <div className="stock-add-control-section">
                <div className="stock-add-control">
                  <button
                    type="button"
                    className="qty-btn qty-btn-minus"
                    aria-label="Disminuir"
                    onClick={() => setDelta((d) => d - 1)}
                    disabled={loading}
                  >
                    <Icons.MinusIcon size={16} />
                  </button>

                  <input
                    type="number"
                    className="stock-delta-input"
                    value={delta}
                    onFocus={(e) => e.target.select()}
                    onChange={(e) => handleDeltaChange(e.target.value)}
                    disabled={loading}
                    data-sign={delta > 0 ? "positive" : delta < 0 ? "negative" : "zero"}
                  />

                  <button
                    type="button"
                    className="qty-btn qty-btn-plus"
                    aria-label="Aumentar"
                    onClick={() => setDelta((d) => d + 1)}
                    disabled={loading}
                  >
                    <Icons.PlusIcon size={16} />
                  </button>
                </div>
              </div>

              {/* Preview nuevo stock */}
              <div className="stock-add-preview-row">
                <span className="stock-add-preview-label">Nuevo stock</span>
                <span
                  className="stock-add-preview-value"
                  data-zero={nuevoStock === 0 ? "true" : "false"}
                >
                  {nuevoStock} unidades
                </span>
              </div>

              {/* Error */}
              {error && (
                <div className="stock-add-error">
                  <Icons.AlertCircleIcon size={16} />
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="stock-add-modal-footer">
              <button
                className="stock-add-btn cancel"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                className={`stock-add-btn save${delta < 0 ? " negative" : ""}`}
                onClick={handleSave}
                disabled={!canSubmit}
              >
                {loading ? (
                  <span className="stock-add-spinner" />
                ) : (
                  <>
                    {delta < 0 ? (
                      <Icons.MinusIcon size={15} />
                    ) : (
                      <Icons.PlusIcon size={15} />
                    )}
                    Confirmar ({deltaLabel})
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default StockAddModal;
