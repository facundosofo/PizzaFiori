import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";
import * as Icons from "../components/shared/Icons";
import Badge from "../components/shared/Badge";
import ErrorAlert from "../components/shared/ErrorAlert";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import StockAddModal from "../components/StockAddModal";
import StockAlertsModal from "../components/StockAlertsModal";
import StockConfigModal from "../components/StockConfigModal";
import StockProductBreakdown from "../components/StockProductBreakdown";
import StockQuantityDisplay from "../components/shared/StockQuantityDisplay";
import type { CategoryStock, StockListResponse } from "../types/stock";
import { STOCK_ESTADO_BADGE, STOCK_ESTADO_LABELS } from "../types/stock";
import { getAllStocks } from "../services/stockService";
import { getProductos } from "../services/productsService";
import type { Product } from "../types/product";
import "../styles/stock.css";

const StockPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  const [stocks, setStocks] = useState<CategoryStock[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const loadingRef = useRef(loading);
  useEffect(() => { loadingRef.current = loading; }, [loading]);

  // Modal: agregar stock (categoria)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedForAdd, setSelectedForAdd] = useState<CategoryStock | null>(null);

  // Modal: configurar alertas (categoria)
  const [isAlertsModalOpen, setIsAlertsModalOpen] = useState(false);
  const [selectedForAlerts, setSelectedForAlerts] = useState<CategoryStock | null>(null);

  // Modal: configurar categorias (admin)
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  // Panel: desglose por producto
  const [expandedCategoryId, setExpandedCategoryId] = useState<number | null>(null);

  const fetchStocks = useCallback(async () => {
    try {
      setError(null);
      const [data, productsData]: [StockListResponse, Product[]] = await Promise.all([
        getAllStocks(),
        getProductos(),
      ]);
      setStocks(Array.isArray(data.categorias) ? data.categorias : []);
      setProducts(productsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar el stock");
    } finally {
      setLoading(false);
    }
  }, []);

  // Carga inicial
  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  // Refresh por eventos cross-page y focus
  useEffect(() => {
    const handleRefresh = () => { if (!loadingRef.current) void fetchStocks(); };
    window.addEventListener("focus", handleRefresh);
    window.addEventListener("sale:created", handleRefresh);
    window.addEventListener("stock-updated", handleRefresh);

    return () => {
      window.removeEventListener("focus", handleRefresh);
      window.removeEventListener("sale:created", handleRefresh);
      window.removeEventListener("stock-updated", handleRefresh);
    };
  }, [fetchStocks]);

  const handleOpenAddModal = (cat: CategoryStock) => {
    setSelectedForAdd(cat);
    setIsAddModalOpen(true);
  };

  // El stock compartido de una categoría se expresa en unidades, por eso se
  // usa el tamaño de porción más pequeño configurado en sus productos.
  const getCategoryPortionSize = (categoriaId: number): number | null => {
    const portionSizes = products
      .filter((product) => product.categoria_id === categoriaId)
      .flatMap((product) => product.precios ?? [])
      .map((price) => Number(price.cantidad))
      .filter((cantidad) => Number.isFinite(cantidad) && cantidad > 0 && cantidad < 1);

    return portionSizes.length > 0 ? Math.min(...portionSizes) : null;
  };

  const handleOpenAlertsModal = (cat: CategoryStock) => {
    setSelectedForAlerts(cat);
    setIsAlertsModalOpen(true);
  };

  const handleStockSaved = (updated: CategoryStock) => {
    setStocks((prev) =>
      prev.map((s) => (s.categoria_id === updated.categoria_id ? updated : s))
    );
    window.dispatchEvent(new CustomEvent("stock-updated"));
  };

  const handleToggleBreakdown = (categoriaId: number) => {
    setExpandedCategoryId((prev) => (prev === categoriaId ? null : categoriaId));
  };

  const getQuantityClass = (estado: string) => {
    if (estado === "ok") return "qty-ok";
    if (estado === "critical" || estado === "sin_stock") return "qty-critical";
    if (estado === "warning") return "qty-warning";
    return "";
  };

  const getCardClass = (estado: string) => {
    if (estado === "ok") return "has-ok";
    if (estado === "critical" || estado === "sin_stock") return "has-critical";
    if (estado === "warning") return "has-warning";
    return "";
  };

  const expandedCategory = stocks.find((s) => s.categoria_id === expandedCategoryId) ?? null;

  return (
    <div className="stock-container">
      <ErrorAlert message={error} onClose={() => setError(null)} />

      <div className="page-header">
        <div>
          <h1 className="page-title">Stock</h1>
        </div>
        {isAdmin && (
          <button
            className="stock-config-trigger-btn"
            onClick={() => setIsConfigModalOpen(true)}
          >
            <Icons.CogIcon size={15} />
            Configuracion
          </button>
        )}
      </div>

      {loading ? (
        <div className="stock-loading-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonLoader key={i} />
          ))}
        </div>
      ) : stocks.length === 0 ? (
        <div className="stock-empty">
          <Icons.LayersIcon size={48} color="var(--color-text-muted)" />
          <p>No hay categorías de producto configuradas.</p>
          {isAdmin && (
            <button className="stock-config-trigger-btn" onClick={() => setIsConfigModalOpen(true)}>
              <Icons.CogIcon size={15} />
              Configuracion
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="stock-grid">
            {stocks.map((cat) => {
              const isExpanded = expandedCategoryId === cat.categoria_id;
              return (
                <motion.div
                  key={cat.categoria_id}
                  className={`stock-card ${getCardClass(cat.estado)}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.18 }}
                >
                  <div className="stock-card-header">
                    <span className="stock-card-category">{cat.categoria_nombre}</span>
                    <Badge variant={STOCK_ESTADO_BADGE[cat.estado]}>
                      {STOCK_ESTADO_LABELS[cat.estado]}
                    </Badge>
                  </div>

                  <div className="stock-card-quantity-row">
                    <StockQuantityDisplay
                      value={cat.cantidad}
                      className={`stock-card-quantity ${getQuantityClass(cat.estado)}`}
                      formatOptions={cat.stock_por_producto ? { preferredDenominator: 4, reduceFraction: false } : undefined}
                    />
                    <span className="stock-card-unit">unidades</span>
                  </div>
                  {/*
                  {(cat.umbral_amarillo != null || cat.umbral_rojo != null) && (
                    <div className="stock-card-thresholds">
                      {cat.umbral_amarillo != null && (
                        <span className="stock-threshold-chip amarillo">
                          🟡 ≤ {cat.umbral_amarillo}
                        </span>
                      )}
                      {cat.umbral_rojo != null && (
                        <span className="stock-threshold-chip rojo">
                          🔴 ≤ {cat.umbral_rojo}
                        </span>
                      )}
                    </div>
                  )}
                  */}
                  <div className="stock-card-actions">
                    {cat.stock_por_producto ? (
                      <>
                        <button
                          className={`stock-card-btn view${isExpanded ? " active" : ""}`}
                          onClick={() => handleToggleBreakdown(cat.categoria_id)}
                        >
                          {isExpanded ? (
                            <>
                              <Icons.EyeOffIcon size={14} />
                              Cerrar
                            </>
                          ) : (
                            <>
                              <Icons.EyeIcon size={14} />
                              Ver
                            </>
                          )}
                        </button>
                        {isAdmin && (
                          <div className="stock-threshold-tooltip-wrap">
                            <button
                              className="stock-card-btn config"
                              onClick={() => handleOpenAlertsModal(cat)}
                            >
                              <Icons.OctagonAlertIcon size={14} />
                              Umbral
                            </button>
                            <div className="stock-threshold-tooltip" role="tooltip">
                              <div className="stock-threshold-tooltip-title">UMBRALES CONFIGURADOS</div>
                              <div className="stock-threshold-tooltip-divider" />
                              {cat.umbral_amarillo != null && (
                                <div className="stock-threshold-tooltip-row">
                                  <span className="stock-threshold-tooltip-label">🟡 Alerta</span>
                                  <span className="stock-threshold-tooltip-value">a partir de {cat.umbral_amarillo}</span>
                                </div>
                              )}
                              {cat.umbral_rojo != null && (
                                <div className="stock-threshold-tooltip-row">
                                  <span className="stock-threshold-tooltip-label">🔴 Crítico</span>
                                  <span className="stock-threshold-tooltip-value">a partir de {cat.umbral_rojo}</span>
                                </div>
                              )}
                              {cat.umbral_amarillo == null && cat.umbral_rojo == null && (
                                <div className="stock-threshold-tooltip-empty">Sin umbrales configurados</div>
                              )}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      isAdmin && (
                        <>
                          <button
                            className="stock-card-btn add"
                            onClick={() => handleOpenAddModal(cat)}
                          >
                            <Icons.DiffIcon size={14} />
                            Modificar
                          </button>
                          <div className="stock-threshold-tooltip-wrap">
                            <button
                              className="stock-card-btn config"
                              onClick={() => handleOpenAlertsModal(cat)}
                            >
                              <Icons.OctagonAlertIcon size={14} />
                              Umbral
                            </button>
                            <div className="stock-threshold-tooltip" role="tooltip">
                              <div className="stock-threshold-tooltip-title">UMBRALES CONFIGURADOS</div>
                              <div className="stock-threshold-tooltip-divider" />
                              {cat.umbral_amarillo != null && (
                                <div className="stock-threshold-tooltip-row">
                                  <span className="stock-threshold-tooltip-label">🟡 Alerta</span>
                                  <span className="stock-threshold-tooltip-value">a partir de {cat.umbral_amarillo}</span>
                                </div>
                              )}
                              {cat.umbral_rojo != null && (
                                <div className="stock-threshold-tooltip-row">
                                  <span className="stock-threshold-tooltip-label">🔴 Crítico</span>
                                  <span className="stock-threshold-tooltip-value">a partir de {cat.umbral_rojo}</span>
                                </div>
                              )}
                              {cat.umbral_amarillo == null && cat.umbral_rojo == null && (
                                <div className="stock-threshold-tooltip-empty">Sin umbrales configurados</div>
                              )}
                            </div>
                          </div>
                        </>
                      )
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>

          {expandedCategory && (
            <StockProductBreakdown
              categoria={expandedCategory}
              isAdmin={isAdmin}
              onClose={() => setExpandedCategoryId(null)}
              onCategoryStockChanged={fetchStocks}
            />
          )}
        </>
      )}

      {/* Modal: agregar/editar stock por categoria (solo admin) */}
      {isAdmin && (
        <>
          <StockAddModal
            mode="categoria"
            isOpen={isAddModalOpen}
            target={selectedForAdd}
            portionSize={selectedForAdd ? getCategoryPortionSize(selectedForAdd.categoria_id) : null}
            onClose={() => {
              setIsAddModalOpen(false);
              setSelectedForAdd(null);
            }}
            onSave={handleStockSaved}
          />
          <StockAlertsModal
            mode="categoria"
            isOpen={isAlertsModalOpen}
            target={selectedForAlerts}
            onClose={() => {
              setIsAlertsModalOpen(false);
              setSelectedForAlerts(null);
            }}
            onSave={handleStockSaved}
          />
          <StockConfigModal
            isOpen={isConfigModalOpen}
            onClose={() => setIsConfigModalOpen(false)}
            onSaved={() => {
              setExpandedCategoryId(null);
              void fetchStocks();
            }}
          />
        </>
      )}
    </div>
  );
};

export default StockPage;
