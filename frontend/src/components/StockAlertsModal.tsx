import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Icons from "./shared/Icons";
import Badge from "./shared/Badge";
import type { CategoryStock } from "../types/stock";
import { STOCK_ESTADO_BADGE, STOCK_ESTADO_LABELS } from "../types/stock";
import { configureAlerts } from "../services/stockService";
import "../styles/stock-alerts-modal.css";
import "../styles/shared/quantity-controls.css";

interface StockAlertsModalProps {
  isOpen: boolean;
  categoria: CategoryStock | null;
  onClose: () => void;
  onSave: (updated: CategoryStock) => void;
}

const StockAlertsModal = ({
  isOpen,
  categoria,
  onClose,
  onSave,
}: StockAlertsModalProps) => {
  const [umbralAmarillo, setUmbralAmarillo] = useState(0);
  const [umbralRojo, setUmbralRojo] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen && categoria) {
      setUmbralAmarillo(categoria.umbral_amarillo ?? 0);
      setUmbralRojo(categoria.umbral_rojo ?? 0);
      setError("");
    }
  }, [isOpen, categoria]);

  const umbralAmarilloVal = umbralAmarillo > 0 ? umbralAmarillo : null;
  const umbralRojoVal = umbralRojo > 0 ? umbralRojo : null;

  // Preview del estado con los valores ingresados
  const previewEstado = (() => {
    const qty = categoria?.cantidad ?? 0;
    if (qty === 0) return "sin_stock" as const;
    if (umbralRojoVal != null && qty <= umbralRojoVal) return "critical" as const;
    if (umbralAmarilloVal != null && qty <= umbralAmarilloVal) return "warning" as const;
    return "ok" as const;
  })();

  const handleSave = async () => {
    setError("");

    if (umbralAmarilloVal != null && umbralRojoVal != null && umbralRojoVal >= umbralAmarilloVal) {
      setError("El umbral rojo debe ser menor al umbral amarillo");
      return;
    }

    if (!categoria) return;

    setLoading(true);
    try {
      const updated = await configureAlerts(categoria.categoria_id, {
        umbral_amarillo: umbralAmarilloVal,
        umbral_rojo: umbralRojoVal,
      });
      onSave(updated);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar umbral");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="stock-alerts-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="stock-alerts-modal"
            initial={{ scale: 0.92, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="stock-alerts-modal-header">
              <div>
                <p className="stock-alerts-modal-eyebrow">Stock — Umbral</p>
                <h2 className="stock-alerts-modal-title">
                  {categoria?.categoria_nombre}
                </h2>
              </div>
              <button
                className="stock-alerts-modal-close"
                onClick={onClose}
                disabled={loading}
              >
                <Icons.XIcon size={18} />
              </button>
            </div>

            <div className="stock-alerts-modal-body">
              {/* Umbral amarillo */}
              <div className="stock-alerts-threshold-row">
                <div className="stock-alerts-threshold-label">
                  <span className="stock-alerts-threshold-name">Umbral amarillo</span>
                  <span className="stock-alerts-threshold-hint">
                    {umbralAmarillo > 0 ? `Stock ≤ ${umbralAmarillo}` : "Sin umbral"}
                  </span>
                </div>
                <div className="quantity-control">
                  <button
                    className="qty-btn qty-btn-minus"
                    onClick={() => setUmbralAmarillo((v) => Math.max(0, v - 1))}
                    disabled={loading || umbralAmarillo === 0}
                  >
                    −
                  </button>
                  <input
                    type="number"
                    className="qty-input alerts-qty-input"
                    value={umbralAmarillo}
                    onChange={(e) =>
                      setUmbralAmarillo(Math.max(0, parseInt(e.target.value) || 0))
                    }
                    min={0}
                    disabled={loading}
                  />
                  <button
                    className="qty-btn qty-btn-plus"
                    onClick={() => setUmbralAmarillo((v) => v + 1)}
                    disabled={loading}
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Umbral rojo */}
              <div className="stock-alerts-threshold-row">
                <div className="stock-alerts-threshold-label">
                  <span className="stock-alerts-threshold-name">Umbral rojo</span>
                  <span className="stock-alerts-threshold-hint">
                    {umbralRojo > 0 ? `Stock ≤ ${umbralRojo}` : "Sin umbral"}
                  </span>
                </div>
                <div className="quantity-control">
                  <button
                    className="qty-btn qty-btn-minus"
                    onClick={() => setUmbralRojo((v) => Math.max(0, v - 1))}
                    disabled={loading || umbralRojo === 0}
                  >
                    −
                  </button>
                  <input
                    type="number"
                    className="qty-input alerts-qty-input"
                    value={umbralRojo}
                    onChange={(e) =>
                      setUmbralRojo(Math.max(0, parseInt(e.target.value) || 0))
                    }
                    min={0}
                    disabled={loading}
                  />
                  <button
                    className="qty-btn qty-btn-plus"
                    onClick={() => setUmbralRojo((v) => v + 1)}
                    disabled={loading}
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Vista previa */}
              <div className="stock-alerts-preview">
                <p className="stock-alerts-preview-title">
                  Vista previa con stock actual ({categoria?.cantidad ?? 0} uds)
                </p>
                <div className="stock-alerts-preview-row">
                  <span>Estado resultante:</span>
                  <Badge variant={STOCK_ESTADO_BADGE[previewEstado]}>
                    {STOCK_ESTADO_LABELS[previewEstado]}
                  </Badge>
                </div>
                {umbralAmarilloVal != null && (
                  <div className="stock-alerts-preview-row">
                    <span>Umbral amarillo activo si stock ≤ {umbralAmarilloVal}</span>
                    <Badge variant="warning">Advertencia</Badge>
                  </div>
                )}
                {umbralRojoVal != null && (
                  <div className="stock-alerts-preview-row">
                    <span>Umbral rojo activo si stock ≤ {umbralRojoVal}</span>
                    <Badge variant="danger">Crítico</Badge>
                  </div>
                )}
              </div>

              {error && (
                <div className="stock-alerts-error">
                  <Icons.AlertCircleIcon size={18} />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <div className="stock-alerts-modal-footer">
              <button
                className="stock-alerts-btn cancel"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                className="stock-alerts-btn save"
                onClick={handleSave}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Icons.LoaderIcon size={16} className="stock-alerts-spinner" />
                    Guardando...
                  </>
                ) : (
                  <>Guardar umbral</>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default StockAlertsModal;
