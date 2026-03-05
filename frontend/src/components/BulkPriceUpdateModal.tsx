import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { actualizarPreciosMasivos } from "../services/productsService";
import ConfirmDialog from "./shared/ConfirmDialog";
import * as Icons from "./shared/Icons";
import type { Product } from "../types/product";
import type { ProductoCategoria } from "../types/product_category";
import "../styles/bulk-price-modal.css";

interface BulkPriceUpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (productos: Product[]) => void;
  categorias: ProductoCategoria[];
}

const BulkPriceUpdateModal = ({
  isOpen,
  onClose,
  onSuccess,
  categorias,
}: BulkPriceUpdateModalProps) => {
  const [tipoAjuste, setTipoAjuste] = useState<"monto" | "porcentaje">("monto");
  const [valor, setValor] = useState("");
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<Set<number>>(new Set());
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setTipoAjuste("monto");
    setValor("");
    setSelectedCategoryIds(new Set());
    setShowConfirm(false);
    setError(null);
    setLoading(false);
  };

  const handleClose = () => {
    if (loading) return;
    resetForm();
    onClose();
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !loading) {
      handleClose();
    }
  };

  const valorNumerico = parseFloat(valor);
  const isValorValido = !isNaN(valorNumerico) && valorNumerico !== 0;

  const allSelected = selectedCategoryIds.size === categorias.length && categorias.length > 0;

  const categoriaNombre = allSelected
    ? "todos los productos"
    : categorias
        .filter((c) => selectedCategoryIds.has(c.id))
        .map((c) => c.nombre)
        .join(", ");

  const getDescripcion = (): string => {
    if (!isValorValido) return "";

    const accion = valorNumerico > 0 ? "aumentar" : "disminuir";
    const valorAbs = Math.abs(valorNumerico);

    if (tipoAjuste === "monto") {
      return `${accion} en $${valorAbs} los precios de ${categoriaNombre}`;
    } else {
      return `${accion} en un ${valorAbs}% los precios de ${categoriaNombre}`;
    }
  };

  const handleApply = () => {
    setError(null);

    if (!isValorValido) {
      setError("Ingrese un valor numérico distinto de cero");
      return;
    }

    if (tipoAjuste === "porcentaje" && valorNumerico <= -100) {
      setError("El porcentaje no puede ser -100% o menor");
      return;
    }

    setShowConfirm(true);
  };

  const handleConfirm = async () => {
    setShowConfirm(false);
    setLoading(true);
    setError(null);

    try {
      const data: Record<string, number | number[] | null> = {};

      if (tipoAjuste === "monto") {
        data.monto = valorNumerico;
      } else {
        data.porcentaje = valorNumerico;
      }

      if (!allSelected && selectedCategoryIds.size > 0) {
        data.categoria_ids = Array.from(selectedCategoryIds);
      }

      const result = await actualizarPreciosMasivos(data);
      onSuccess(result.productos);
      resetForm();
      onClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Error desconocido";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="bulk-price-modal-overlay"
            onClick={handleOverlayClick}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div
              className="bulk-price-modal-content"
              onClick={(e) => e.stopPropagation()}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <button
                className="bulk-price-modal-close"
                onClick={handleClose}
                disabled={loading}
              >
                <Icons.XIcon size={18} />
              </button>

              <div className="bulk-price-modal-header">
                <h2 className="bulk-price-modal-title">
                  Actualizar Precios
                </h2>
                <p className="bulk-price-modal-subtitle">
                  Modificar precios de forma masiva
                </p>
              </div>

              {error && <div className="form-error">{error}</div>}

              {/* Tipo de ajuste */}
              <div className="form-group">
                <label>Tipo de ajuste</label>
                <div className="bulk-price-type-selector">
                  <button
                    type="button"
                    className={`bulk-price-type-btn ${tipoAjuste === "monto" ? "active" : ""}`}
                    onClick={() => {
                      setTipoAjuste("monto");
                      setValor("");
                      setError(null);
                    }}
                    disabled={loading}
                  >
                    <Icons.PesoIcon size={16} />
                    Monto fijo
                  </button>
                  <button
                    type="button"
                    className={`bulk-price-type-btn ${tipoAjuste === "porcentaje" ? "active" : ""}`}
                    onClick={() => {
                      setTipoAjuste("porcentaje");
                      setValor("");
                      setError(null);
                    }}
                    disabled={loading}
                  >
                    <Icons.DiscountIcon size={16} />
                    Porcentaje
                  </button>
                </div>
              </div>

              {/* Valor */}
              <div className="form-group">
                <label>
                  {tipoAjuste === "monto"
                    ? "Monto a aplicar"
                    : "Porcentaje a aplicar"}
                </label>
                <div className="bulk-price-input-wrapper">
                  {tipoAjuste === "monto" ? (
                    <>
                      <span className="bulk-price-input-prefix">$</span>
                      <input
                        type="text"
                        inputMode="decimal"
                        className="form-input"
                        placeholder="Ej: 200 o -100"
                        value={valor}
                        onChange={(e) => {
                          const v = e.target.value;
                          if (v === "" || v === "-" || /^-?\d*\.?\d*$/.test(v)) setValor(v);
                        }}
                        disabled={loading}
                      />
                    </>
                  ) : (
                    <>
                      <input
                        type="text"
                        inputMode="decimal"
                        className="form-input has-suffix"
                        placeholder="Ej: 10 o -5"
                        value={valor}
                        onChange={(e) => {
                          const v = e.target.value;
                          if (v === "" || v === "-" || /^-?\d*\.?\d*$/.test(v)) setValor(v);
                        }}
                        disabled={loading}
                      />
                      <span className="bulk-price-input-suffix">%</span>
                    </>
                  )}
                </div>
              </div>

              {/* Categorías */}
              <div className="form-group">
                <label>Categorías</label>
                <label className="bulk-price-check-all">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={() => {
                      if (allSelected) {
                        setSelectedCategoryIds(new Set());
                      } else {
                        setSelectedCategoryIds(new Set(categorias.map((c) => c.id)));
                      }
                    }}
                    disabled={loading}
                  />
                  Seleccionar todas
                </label>
                <div className="bulk-price-category-grid">
                  {categorias.map((cat) => (
                    <label key={cat.id} className="bulk-price-check-item">
                      <input
                        type="checkbox"
                        checked={selectedCategoryIds.has(cat.id)}
                        onChange={() => {
                          setSelectedCategoryIds((prev) => {
                            const next = new Set(prev);
                            if (next.has(cat.id)) {
                              next.delete(cat.id);
                            } else {
                              next.add(cat.id);
                            }
                            return next;
                          });
                        }}
                        disabled={loading}
                      />
                      {cat.nombre}
                    </label>
                  ))}
                </div>
              </div>

              {/* Resumen */}
              {isValorValido && (
                <div className="bulk-price-summary">
                  <p className="bulk-price-summary-title">Resumen</p>
                  <p className="bulk-price-summary-text">
                    Se van a <strong>{getDescripcion()}</strong>.
                    Todos los precios escalonados serán afectados y redondeados
                    al entero más cercano.
                  </p>
                </div>
              )}

              {/* Acciones */}
              <div className="form-actions">
                <button
                  className="form-cancel-btn"
                  onClick={handleClose}
                  disabled={loading}
                >
                  Cancelar
                </button>
                <button
                  className="form-save-btn"
                  onClick={handleApply}
                  disabled={loading || !isValorValido || selectedCategoryIds.size === 0}
                >
                  {loading ? (
                    <>
                      <Icons.LoaderIcon size={16} /> Actualizando...
                    </>
                  ) : (
                    "Aplicar"
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <ConfirmDialog
        isOpen={showConfirm}
        title="Confirmar actualización"
        message={`¿Está seguro que desea ${getDescripcion()}? Todos los precios escalonados serán modificados.`}
        confirmText="Confirmar"
        cancelText="Cancelar"
        onConfirm={handleConfirm}
        onCancel={() => setShowConfirm(false)}
      />
    </>
  );
};

export default BulkPriceUpdateModal;
