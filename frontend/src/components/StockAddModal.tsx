import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Icons from "./shared/Icons";
import type { CategoryStock, ProductStock } from "../types/stock";
import { addStock, addProductStock } from "../services/stockService";
import StockQuantityDisplay from "./shared/StockQuantityDisplay";
import { formatStockQuantity } from "../utils/stockQuantityFormatter";
import "../styles/stock-add-modal.css";
import "../styles/shared/quantity-controls.css";

interface StockAddModalCategoriaProps {
  mode: "categoria";
  isOpen: boolean;
  target: CategoryStock | null;
  /** Tamaño de la porción compartida por los productos de la categoría. */
  portionSize?: number | null;
  onClose: () => void;
  onSave: (updated: CategoryStock) => void;
}

interface StockAddModalProductoProps {
  mode: "producto";
  isOpen: boolean;
  target: ProductStock | null;
  productPortionSize?: number | null;
  onClose: () => void;
  onSave: (updated: ProductStock) => void;
}

type StockAddModalProps = StockAddModalCategoriaProps | StockAddModalProductoProps;

const parseSignedInteger = (value: number): number => (value < 0 ? -Math.trunc(Math.abs(value)) : Math.trunc(value));
const clamp = (value: number, min: number, max: number): number => Math.min(max, Math.max(min, value));
const toNumericQuantity = (value: unknown): number => {
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  if (typeof value === "string") {
    const parsed = parseFloat(value.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
};

const StockAddModal = (props: StockAddModalProps) => {
  const { isOpen, target, onClose } = props;
  const [singleDelta, setSingleDelta] = useState(0);
  const [unitsDelta, setUnitsDelta] = useState(0);
  const [portionCount, setPortionCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const round3 = (value: number): number => Number(value.toFixed(3));
  const fixedPortionSize = props.mode === "producto"
    ? ((props as StockAddModalProductoProps).productPortionSize ?? null)
    : ((props as StockAddModalCategoriaProps).portionSize ?? null);
  const hasFixedPortion = typeof fixedPortionSize === "number" && fixedPortionSize > 0 && fixedPortionSize < 1;
  const effectivePortionSize = hasFixedPortion ? fixedPortionSize : 0.125;
  const useDualCounters = hasFixedPortion;
  const effectiveDelta = useDualCounters
    ? round3(unitsDelta + portionCount * effectivePortionSize)
    : singleDelta;

  useEffect(() => {
    if (!isOpen) return;
    setSingleDelta(0);
    setUnitsDelta(0);
    setPortionCount(0);
    setError("");
  }, [isOpen]);

  const handleSingleDeltaChange = (raw: string) => {
    if (raw === "" || raw === "-") {
      setSingleDelta(0);
      return;
    }

    const normalized = raw.replace(",", ".");
    const n = parseFloat(normalized);
    if (isNaN(n)) return;

    setSingleDelta(parseSignedInteger(n));
  };

  const handleUnitsChange = (raw: string) => {
    if (raw === "" || raw === "-") {
      setUnitsDelta(0);
      return;
    }

    const normalized = raw.replace(",", ".");
    const n = parseFloat(normalized);
    if (isNaN(n)) return;

    setUnitsDelta(parseSignedInteger(n));
  };

  const handlePortionCountChange = (raw: string) => {
    if (raw === "" || raw === "-") {
      setPortionCount(0);
      return;
    }

    const normalized = raw.replace(",", ".");
    const n = parseFloat(normalized);
    if (isNaN(n)) return;

    setPortionCount(clamp(parseSignedInteger(n), -maxPortionCount, maxPortionCount));
  };

  const applySingleStep = (direction: -1 | 1) => {
    setSingleDelta((prev) => prev + direction);
  };

  const applyUnitsStep = (direction: -1 | 1) => {
    setUnitsDelta((prev) => prev + direction);
  };

  const applyPortionStep = (direction: -1 | 1) => {
    setPortionCount((prev) => clamp(prev + direction, -maxPortionCount, maxPortionCount));
  };

  const handleSave = async () => {
    setError("");
    if (effectiveDelta === 0) return;
    if (!target) return;

    setLoading(true);
    try {
      if (props.mode === "categoria") {
        const updated = await addStock((target as CategoryStock).categoria_id, { cantidad: effectiveDelta });
        props.onSave(updated);
      } else {
        const updated = await addProductStock((target as ProductStock).producto_id, { cantidad: effectiveDelta });
        props.onSave(updated);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al ajustar stock");
    } finally {
      setLoading(false);
    }
  };

  const targetName = target
    ? props.mode === "categoria"
      ? (target as CategoryStock).categoria_nombre
      : (target as ProductStock).producto_nombre
    : "";

  const currentQty = toNumericQuantity(target?.cantidad);
  const nuevoStock = Math.max(0, currentQty + effectiveDelta);
  const portionDenominator = Math.max(1, Math.round(1 / effectivePortionSize));
  const maxPortionCount = useDualCounters ? Math.max(0, portionDenominator - 1) : 0;
  const deltaLabel = effectiveDelta > 0
    ? `+${formatStockQuantity(effectiveDelta, useDualCounters
      ? { preferredDenominator: portionDenominator, reduceFraction: false }
      : undefined)}`
    : effectiveDelta < 0
      ? `−${formatStockQuantity(Math.abs(effectiveDelta), useDualCounters
        ? { preferredDenominator: portionDenominator, reduceFraction: false }
        : undefined)}`
      : "0";
  const canSubmit = effectiveDelta !== 0 && !loading;

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
            <div className="stock-add-modal-header">
              <div>
                <p className="stock-add-modal-eyebrow">Stock</p>
                <h2 className="stock-add-modal-title">
                  Modificar - {" "}
                  <span className="stock-add-modal-category">{targetName}</span>
                </h2>
              </div>
              <button className="stock-add-modal-close" onClick={onClose} disabled={loading}>
                <Icons.XIcon size={18} />
              </button>
            </div>

            <div className="stock-add-modal-body">
              <div className="stock-add-current-row">
                <span className="stock-add-current-label">Stock actual</span>
                <span className="stock-add-current-value">
                  <StockQuantityDisplay
                    value={currentQty}
                    formatOptions={useDualCounters
                      ? { preferredDenominator: portionDenominator, reduceFraction: false }
                      : undefined}
                  />
                  <span className="stock-add-unit-suffix">unidades</span>
                </span>
              </div>

              <div className="stock-add-control-section">
                {useDualCounters ? (
                  <div className="stock-dual-counters">
                    <div className="stock-dual-counter">
                      <span className="stock-dual-counter-title">Unidades</span>
                      <div className="stock-add-control">
                        <button
                          type="button"
                          className="qty-btn qty-btn-minus"
                          aria-label="Disminuir unidades"
                          onClick={() => applyUnitsStep(-1)}
                          disabled={loading}
                        >
                          <Icons.MinusIcon size={16} />
                        </button>

                        <input
                          type="number"
                          step="1"
                          inputMode="numeric"
                          className="stock-delta-input"
                          value={unitsDelta}
                          onFocus={(e) => e.target.select()}
                          onChange={(e) => handleUnitsChange(e.target.value)}
                          disabled={loading}
                          data-sign={unitsDelta > 0 ? "positive" : unitsDelta < 0 ? "negative" : "zero"}
                        />

                        <button
                          type="button"
                          className="qty-btn qty-btn-plus"
                          aria-label="Aumentar unidades"
                          onClick={() => applyUnitsStep(1)}
                          disabled={loading}
                        >
                          <Icons.PlusIcon size={16} />
                        </button>
                      </div>
                    </div>

                    <div className="stock-dual-divider" aria-hidden="true" />

                    <div className="stock-dual-counter">
                      <span className="stock-dual-counter-title">Porciones</span>
                      <div className="stock-add-control">
                        <button
                          type="button"
                          className="qty-btn qty-btn-minus"
                          aria-label="Disminuir porciones"
                          onClick={() => applyPortionStep(-1)}
                          disabled={loading || portionCount <= -maxPortionCount}
                        >
                          <Icons.MinusIcon size={16} />
                        </button>

                        <input
                          type="number"
                          step="1"
                          inputMode="numeric"
                          className="stock-delta-input"
                          value={portionCount}
                          onFocus={(e) => e.target.select()}
                          onChange={(e) => handlePortionCountChange(e.target.value)}
                          disabled={loading}
                          data-sign={portionCount > 0 ? "positive" : portionCount < 0 ? "negative" : "zero"}
                        />

                        <button
                          type="button"
                          className="qty-btn qty-btn-plus"
                          aria-label="Aumentar porciones"
                          onClick={() => applyPortionStep(1)}
                          disabled={loading || portionCount >= maxPortionCount}
                        >
                          <Icons.PlusIcon size={16} />
                        </button>
                      </div>

                      <span className="stock-portion-mode-hint">
                        1 porcion = {formatStockQuantity(effectivePortionSize)}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="stock-add-control">
                    <button
                      type="button"
                      className="qty-btn qty-btn-minus"
                      aria-label="Disminuir"
                      onClick={() => applySingleStep(-1)}
                      disabled={loading}
                    >
                      <Icons.MinusIcon size={16} />
                    </button>

                    <input
                      type="number"
                      step="1"
                      inputMode="numeric"
                      className="stock-delta-input"
                      value={singleDelta}
                      onFocus={(e) => e.target.select()}
                      onChange={(e) => handleSingleDeltaChange(e.target.value)}
                      disabled={loading}
                      data-sign={singleDelta > 0 ? "positive" : singleDelta < 0 ? "negative" : "zero"}
                    />

                    <button
                      type="button"
                      className="qty-btn qty-btn-plus"
                      aria-label="Aumentar"
                      onClick={() => applySingleStep(1)}
                      disabled={loading}
                    >
                      <Icons.PlusIcon size={16} />
                    </button>
                  </div>
                )}
              </div>

              <div className="stock-add-preview-row">
                <span className="stock-add-preview-label">Nuevo stock</span>
                <span className="stock-add-preview-value" data-zero={nuevoStock === 0 ? "true" : "false"}>
                  <StockQuantityDisplay
                    value={nuevoStock}
                    formatOptions={useDualCounters
                      ? { preferredDenominator: portionDenominator, reduceFraction: false }
                      : undefined}
                  />
                  <span className="stock-add-unit-suffix">unidades</span>
                </span>
              </div>

              {error && (
                <div className="stock-add-error">
                  <Icons.AlertCircleIcon size={16} />
                  {error}
                </div>
              )}
            </div>

            <div className="stock-add-modal-footer">
              <button className="stock-add-btn cancel" onClick={onClose} disabled={loading}>
                Cancelar
              </button>
              <button
                className={`stock-add-btn save${effectiveDelta < 0 ? " negative" : ""}`}
                onClick={handleSave}
                disabled={!canSubmit}
              >
                {loading ? (
                  <span className="stock-add-spinner" />
                ) : (
                  <>
                    {effectiveDelta < 0 ? <Icons.MinusIcon size={15} /> : <Icons.PlusIcon size={15} />}
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
