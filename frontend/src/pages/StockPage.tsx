import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";
import * as Icons from "../components/shared/Icons";
import Badge from "../components/shared/Badge";
import ErrorAlert from "../components/shared/ErrorAlert";
import SkeletonLoader from "../components/shared/SkeletonLoader";
import StockAddModal from "../components/StockAddModal";
import StockAlertsModal from "../components/StockAlertsModal";
import type { CategoryStock } from "../types/stock";
import { STOCK_ESTADO_BADGE, STOCK_ESTADO_LABELS } from "../types/stock";
import { getAllStocks } from "../services/stockService";
import "../styles/stock.css";

const StockPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  const [stocks, setStocks] = useState<CategoryStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const loadingRef = useRef(loading);
  useEffect(() => { loadingRef.current = loading; }, [loading]);

  // Modal: agregar stock
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedForAdd, setSelectedForAdd] = useState<CategoryStock | null>(null);

  // Modal: configurar alertas
  const [isAlertsModalOpen, setIsAlertsModalOpen] = useState(false);
  const [selectedForAlerts, setSelectedForAlerts] = useState<CategoryStock | null>(null);

  const fetchStocks = useCallback(async () => {
    try {
      setError(null);
      const data = await getAllStocks();
      setStocks(Array.isArray(data) ? data : []);
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

  // Refresh por eventos cross-page y focus — usa ref para evitar re-registrar handlers en cada cambio de loading
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

  const getQuantityClass = (estado: string) => {
    if (estado === "critical" || estado === "sin_stock") return "qty-critical";
    if (estado === "warning") return "qty-warning";
    if (estado === "sin_stock") return "qty-sin-stock";
    return "";
  };

  const getCardClass = (estado: string) => {
    if (estado === "critical" || estado === "sin_stock") return "has-critical";
    if (estado === "warning") return "has-warning";
    return "";
  };

  return (
    <div className="stock-container">
      <ErrorAlert message={error} onClose={() => setError(null)} />

      <div className="page-header">
        <h1 className="page-title">Stock</h1>
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
        </div>
      ) : (
        <>
          <div className="stock-grid">
            {stocks.map((cat) => (
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
                  <span className={`stock-card-quantity ${getQuantityClass(cat.estado)}`}>
                    {cat.cantidad}
                  </span>
                  <span className="stock-card-unit">unidades</span>
                </div>

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

                {isAdmin && (
                  <div className="stock-card-actions">
                    <button
                      className="stock-card-btn add"
                      onClick={() => handleOpenAddModal(cat)}
                    >
                      <Icons.PlusIcon size={14} />
                      Modificar
                    </button>
                    <button
                      className="stock-card-btn config"
                      onClick={() => handleOpenAlertsModal(cat)}
                    >
                      <Icons.OctagonAlertIcon size={14} />
                      Umbral
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </>
      )}

      {/* Modales (solo admin) */}
      {isAdmin && (
        <>
          <StockAddModal
            isOpen={isAddModalOpen}
            categoria={selectedForAdd}
            onClose={() => {
              setIsAddModalOpen(false);
              setSelectedForAdd(null);
            }}
            onSave={handleStockSaved}
          />
          <StockAlertsModal
            isOpen={isAlertsModalOpen}
            categoria={selectedForAlerts}
            onClose={() => {
              setIsAlertsModalOpen(false);
              setSelectedForAlerts(null);
            }}
            onSave={handleStockSaved}
          />
        </>
      )}
    </div>
  );
};

export default StockPage;
