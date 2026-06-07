import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Icons from "./shared/Icons";
import type { CategoryConfigItem } from "../types/stock";
import { getStockConfig, saveStockConfig } from "../services/stockService";
import "../styles/stock-config-modal.css";

interface StockConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
}

const StockConfigModal = ({ isOpen, onClose, onSaved }: StockConfigModalProps) => {
  const [configs, setConfigs] = useState<CategoryConfigItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      setError("");
      setLoading(true);
      getStockConfig()
        .then(setConfigs)
        .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar configuración"))
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  const handleToggle = (
    categoriaId: number,
    field: "stock_visible" | "stock_por_producto",
    value: boolean
  ) => {
    setConfigs((prev) =>
      prev.map((c) => (c.categoria_id === categoriaId ? { ...c, [field]: value } : c))
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      await saveStockConfig(configs.map(({ categoria_id, stock_visible, stock_por_producto }) => ({
        categoria_id,
        stock_visible,
        stock_por_producto,
      })));
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar configuración");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="stock-config-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="stock-config-modal"
            initial={{ scale: 0.92, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="stock-config-header">
              <div>
                <p className="stock-config-eyebrow">Stock — Administrar</p>
                <h2 className="stock-config-title">Configurar categorías</h2>
              </div>
              <button className="stock-config-close" onClick={onClose} disabled={saving}>
                <Icons.XIcon size={18} />
              </button>
            </div>

            <div className="stock-config-body">
              {loading ? (
                <div className="stock-config-loading">
                  <Icons.LoaderIcon size={22} className="stock-config-spinner" />
                  <span>Cargando categorías...</span>
                </div>
              ) : (
                <table className="stock-config-table">
                  <thead>
                    <tr>
                      <th className="stock-config-th name-col">Categoría</th>
                      <th className="stock-config-th toggle-col">Visible</th>
                      <th className="stock-config-th toggle-col">Stock por producto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {configs.map((cat) => (
                      <tr
                        key={cat.categoria_id}
                        className={`stock-config-row${!cat.stock_visible ? " hidden-row" : ""}`}
                      >
                        <td className="stock-config-td name-col">
                          <span className="stock-config-cat-name">{cat.categoria_nombre}</span>
                          {cat.stock_por_producto && (
                            <span className="stock-config-hint suma">Suma de productos</span>
                          )}
                        </td>
                        <td className="stock-config-td toggle-col">
                          <label className="stock-config-toggle">
                            <input
                              type="checkbox"
                              checked={cat.stock_visible}
                              onChange={(e) =>
                                handleToggle(cat.categoria_id, "stock_visible", e.target.checked)
                              }
                              disabled={saving}
                            />
                            <span className="stock-config-toggle-slider" />
                          </label>
                        </td>
                        <td className="stock-config-td toggle-col">
                          <label className="stock-config-toggle">
                            <input
                              type="checkbox"
                              checked={cat.stock_por_producto}
                              onChange={(e) =>
                                handleToggle(cat.categoria_id, "stock_por_producto", e.target.checked)
                              }
                              disabled={saving}
                            />
                            <span className="stock-config-toggle-slider" />
                          </label>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {error && (
                <div className="stock-config-error">
                  <Icons.AlertCircleIcon size={16} />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <div className="stock-config-footer">
              <button className="stock-config-btn cancel" onClick={onClose} disabled={saving}>
                Cancelar
              </button>
              <button className="stock-config-btn save" onClick={handleSave} disabled={saving || loading}>
                {saving ? (
                  <>
                    <Icons.LoaderIcon size={16} className="stock-config-spinner" />
                    Guardando...
                  </>
                ) : (
                  "Guardar configuración"
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default StockConfigModal;
