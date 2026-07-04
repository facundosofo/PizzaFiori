import { useCallback, useEffect, useState } from "react";
import * as Icons from "./shared/Icons";
import Badge from "./shared/Badge";
import type { CategoryStock, ProductStock } from "../types/stock";
import { STOCK_ESTADO_BADGE, STOCK_ESTADO_LABELS } from "../types/stock";
import { getProductStocks } from "../services/stockService";
import { getProductos } from "../services/productsService";
import StockQuantityDisplay from "./shared/StockQuantityDisplay";
import StockAddModal from "./StockAddModal";
import StockAlertsModal from "./StockAlertsModal";
import "../styles/stock-product-breakdown.css";

interface StockProductBreakdownProps {
  categoria: CategoryStock;
  isAdmin: boolean;
  onClose: () => void;
  onCategoryStockChanged?: () => void;
}

const StockProductBreakdown = ({ categoria, isAdmin, onClose, onCategoryStockChanged }: StockProductBreakdownProps) => {
  const [products, setProducts] = useState<ProductStock[]>([]);
  const [productPortionSizeMap, setProductPortionSizeMap] = useState<Record<number, number | null>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [addTarget, setAddTarget] = useState<ProductStock | null>(null);
  const [alertsTarget, setAlertsTarget] = useState<ProductStock | null>(null);

  const loadProducts = useCallback(() => {
    setLoading(true);
    setError("");
    Promise.all([
      getProductStocks(categoria.categoria_id),
      getProductos(categoria.categoria_id),
    ])
      .then(([stockProducts, catalogProducts]) => {
        setProducts(stockProducts);

        const nextMap: Record<number, number | null> = {};
        catalogProducts.forEach((product) => {
          const portionValues = (product.precios || [])
            .map((price) => Number(price.cantidad))
            .filter((cantidad) => Number.isFinite(cantidad) && cantidad > 0 && cantidad < 1)
            .sort((a, b) => a - b);

          nextMap[product.id] = portionValues.length > 0 ? portionValues[0] : null;
        });

        setProductPortionSizeMap(nextMap);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar productos"))
      .finally(() => setLoading(false));
  }, [categoria.categoria_id]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    loadProducts();
  }, [categoria.cantidad, loadProducts]);

  // Refresh product stocks automatically when a sale is registered
  useEffect(() => {
    window.addEventListener("sale:created", loadProducts);
    return () => window.removeEventListener("sale:created", loadProducts);
  }, [loadProducts]);

  const getProductCardClass = (estado: ProductStock["estado"]) => {
    if (estado === "ok") return "has-ok";
    if (estado === "critical" || estado === "sin_stock") return "has-critical";
    if (estado === "warning") return "has-warning";
    return "";
  };

  const handleProductStockSaved = (updated: ProductStock) => {
    setProducts((prev) =>
      prev.map((p) => (p.producto_id === updated.producto_id ? updated : p))
    );
    // Re-fetch category totals in parent (category total = sum of product stocks)
    onCategoryStockChanged?.();
  };

  const getQtyClass = (estado: ProductStock["estado"], cantidad: number) => {
    if (cantidad <= 0) return "qty-critical";
    if (estado === "critical") return "qty-critical";
    if (estado === "warning") return "qty-warning";
    if (estado === "ok") return "qty-ok";
    if (estado === "sin_stock") return "qty-sin-stock";
    return "";
  };

  return (
    <div className="spb-container">
      <div className="spb-header">
        <div className="spb-header-row">
          <div className="spb-breadcrumb">
            <div>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.45)", marginBottom: "0.2rem" }}>Categoría</div>
              <span className="spb-category-name">{categoria.categoria_nombre}</span>
            </div>
            {!loading && (
              <div>
                <div style={{ fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.45)", marginBottom: "0.2rem" }}>Productos</div>
                <span className="spb-meta" style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--color-text)" }}>
                  {products.length}
                </span>
              </div>
            )}
          </div>
            <button className="stock-config-close" onClick={onClose} aria-label="Cerrar">
                          <Icons.XIcon size={18} />
            </button>
        </div>
      </div>

      <div className="spb-body">
        {loading ? (
          <div className="spb-loading">
            <Icons.LoaderIcon size={20} className="spb-spinner" />
            <span>Cargando productos...</span>
          </div>
        ) : error ? (
          <div className="spb-error">
            <Icons.AlertCircleIcon size={16} />
            <span>{error}</span>
          </div>
        ) : products.length === 0 ? (
          <div className="spb-empty">No hay productos configurados para esta categoría.</div>
        ) : (
          <div className="spb-grid">
            {products.map((product) => (
              <div key={product.producto_id} className={`spb-card ${getProductCardClass(product.estado)}`}>
                <div className="spb-card-content">
                  <div className="spb-card-top">
                    <span className="spb-product-name">{product.producto_nombre}</span>
                    <Badge variant={STOCK_ESTADO_BADGE[product.estado]}>
                      {STOCK_ESTADO_LABELS[product.estado]}
                    </Badge>
                  </div>

                  <div className="spb-quantity">
                    <StockQuantityDisplay
                      value={product.cantidad}
                      className={`spb-qty-number ${getQtyClass(product.estado, product.cantidad)}`}
                      formatOptions={productPortionSizeMap[product.producto_id]
                        ? {
                            preferredDenominator: Math.max(1, Math.round(1 / (productPortionSizeMap[product.producto_id] as number))),
                            reduceFraction: false,
                          }
                        : undefined}
                    />
                    <span className="spb-qty-label">unidades</span>
                  </div>
                  {/*
                  <div className="spb-thresholds">
                    {product.umbral_amarillo != null && (
                      <span className="spb-threshold warning">Alerta ≤ {product.umbral_amarillo}</span>
                    )}
                    {product.umbral_rojo != null && (
                      <span className="spb-threshold critical">Crítico ≤ {product.umbral_rojo}</span>
                    )}
                    {product.umbral_amarillo == null && product.umbral_rojo == null && (
                      <span className="spb-threshold empty">Sin límite</span>
                    )}
                  </div>*/}
                </div>

                {isAdmin && (
                  <div className="spb-card-actions">
                    <button
                      className="spb-action-btn mod"
                      onClick={() => setAddTarget(product)}
                    >
                      <Icons.DiffIcon size={14} />
                      Modificar
                    </button>
                    <div className="stock-threshold-tooltip-wrap">
                      <button
                        className="spb-action-btn alerts"
                        onClick={() => setAlertsTarget(product)}
                      >
                        <Icons.OctagonAlertIcon size={14} />
                        Umbral
                      </button>
                      <div className="stock-threshold-tooltip" role="tooltip">
                        <div className="stock-threshold-tooltip-title">UMBRALES CONFIGURADOS</div>
                        <div className="stock-threshold-tooltip-divider" />
                        {product.umbral_amarillo != null && (
                          <div className="stock-threshold-tooltip-row">
                            <span className="stock-threshold-tooltip-label">🟡 Alerta</span>
                            <span className="stock-threshold-tooltip-value">a partir de {product.umbral_amarillo}</span>
                          </div>
                        )}
                        {product.umbral_rojo != null && (
                          <div className="stock-threshold-tooltip-row">
                            <span className="stock-threshold-tooltip-label">🔴 Crítico</span>
                            <span className="stock-threshold-tooltip-value">a partir de {product.umbral_rojo}</span>
                          </div>
                        )}
                        {product.umbral_amarillo == null && product.umbral_rojo == null && (
                          <div className="stock-threshold-tooltip-empty">Sin umbrales configurados</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {addTarget && (
        <StockAddModal
          mode="producto"
          isOpen={addTarget !== null}
          target={addTarget}
          productPortionSize={productPortionSizeMap[addTarget.producto_id] ?? null}
          onClose={() => setAddTarget(null)}
          onSave={(updated: ProductStock) => {
            handleProductStockSaved(updated);
            setAddTarget(null);
          }}
        />
      )}

      {alertsTarget && (
        <StockAlertsModal
          mode="producto"
          isOpen={alertsTarget !== null}
          target={alertsTarget}
          onClose={() => setAlertsTarget(null)}
          onSave={(updated: ProductStock) => {
            handleProductStockSaved(updated);
            setAlertsTarget(null);
          }}
        />
      )}
    </div>
  );
};

export default StockProductBreakdown;
