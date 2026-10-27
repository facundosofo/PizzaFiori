import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";
import {
  getCatalogPublishStatus,
  getDeliveryMinimumConfig,
  getRecargoConfig,
  publishCatalog,
  updateDeliveryMinimumConfig,
  updateRecargoConfig,
  type CatalogPublishResult,
} from "../services/configService";
import ErrorAlert from "../components/shared/ErrorAlert";
import * as Icons from "../components/shared/Icons";
import "../styles/shared/page-header.css";
import "../styles/config-page.css";

const CONFIG_FIELDS = [
  {
    key: "recargo_transferencia",
    label: "Recargo por transferencia/débito",
    description:
      "Porcentaje que se aplica a las ventas pagadas por transferencia o débito. Después de cambiarlo, publicá nuevamente el catálogo para actualizar la web de pedidos.",
    suffix: "%",
  },
];

export default function ConfigPage() {
  const { user, isLoading: authLoading } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  const [configValues, setConfigValues] = useState<Record<string, string>>({
    recargo_transferencia: "10",
  });
  const [originalValues, setOriginalValues] = useState<Record<string, string>>({
    recargo_transferencia: "10",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogPublishedAt, setCatalogPublishedAt] = useState<string | null>(null);
  const [catalogPublishing, setCatalogPublishing] = useState(false);
  const [catalogResult, setCatalogResult] = useState<CatalogPublishResult | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [deliveryMinimum, setDeliveryMinimum] = useState("13000");
  const [originalDeliveryMinimum, setOriginalDeliveryMinimum] = useState("13000");
  const [deliverySaving, setDeliverySaving] = useState(false);
  const [deliverySuccess, setDeliverySuccess] = useState(false);
  const [deliveryError, setDeliveryError] = useState<string | null>(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        setLoading(true);
        setError(null);
        const [config, deliveryConfig, catalogStatus] = await Promise.all([
          getRecargoConfig(),
          getDeliveryMinimumConfig(),
          getCatalogPublishStatus(),
        ]);
        const value = String(config.porcentaje_recargo ?? "10");
        setConfigValues({ recargo_transferencia: value });
        setOriginalValues({ recargo_transferencia: value });
        const minimum = String(deliveryConfig.monto_minimo_delivery);
        setDeliveryMinimum(minimum);
        setOriginalDeliveryMinimum(minimum);
        setCatalogPublishedAt(catalogStatus.publicado_en);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, []);

  const hasChanges = useMemo(
    () =>
      CONFIG_FIELDS.some(
        (field) => configValues[field.key] !== originalValues[field.key]
      ),
    [configValues, originalValues]
  );

  const handleChange = (key: string, value: string) => {
    setConfigValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    setConfigValues(originalValues);
    setError(null);
  };

  const handleSave = async () => {
    try {
      setError(null);
      setSaving(true);
      const rawValue = configValues.recargo_transferencia.trim();
      const percentage = parseFloat(rawValue);

      if (isNaN(percentage)) {
        setError("El porcentaje debe ser un número válido");
        return;
      }

      if (percentage < 0 || percentage > 100) {
        setError("El porcentaje debe estar entre 0 y 100");
        return;
      }

      const result = await updateRecargoConfig(percentage);
      const normalized = String(result.porcentaje_recargo);
      setConfigValues({ recargo_transferencia: normalized });
      setOriginalValues({ recargo_transferencia: normalized });
      setSuccess(true);
      window.setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al guardar";
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handlePublishCatalog = async () => {
    try {
      setCatalogError(null);
      setCatalogResult(null);
      setCatalogPublishing(true);
      const result = await publishCatalog();
      setCatalogPublishedAt(result.publicado_en);
      setCatalogResult(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al publicar el catálogo";
      setCatalogError(errorMessage);
    } finally {
      setCatalogPublishing(false);
    }
  };

  const handleSaveDeliveryMinimum = async () => {
    const rawMinimum = deliveryMinimum.trim();
    const minimum = Number(rawMinimum);
    if (
      !/^\d+(\.\d{1,2})?$/.test(rawMinimum) ||
      !Number.isFinite(minimum) ||
      minimum < 0 ||
      minimum > 9999999999.99
    ) {
      setDeliveryError("Ingresá un monto válido entre $0 y $9.999.999.999,99, con hasta dos decimales.");
      return;
    }

    try {
      setDeliveryError(null);
      setDeliverySaving(true);
      const result = await updateDeliveryMinimumConfig(minimum);
      const normalized = String(result.monto_minimo_delivery);
      setDeliveryMinimum(normalized);
      setOriginalDeliveryMinimum(normalized);
      setDeliverySuccess(true);
      window.setTimeout(() => setDeliverySuccess(false), 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al guardar";
      setDeliveryError(errorMessage);
    } finally {
      setDeliverySaving(false);
    }
  };

  if (authLoading) {
    return (
      <div className="config-page">
        <div className="config-container">
          <div className="page-header">
            <h1 className="page-title">Configuración</h1>
          </div>
          <div className="access-denied">
            <p>Cargando...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="config-page">
        <div className="config-container">
          <div className="access-denied">
            <Icons.ShieldOffIcon size={64} color="#ef4444" />
            <h1>Acceso Denegado</h1>
            <p>Solo los administradores pueden acceder a esta página.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="config-page">
      <div className="config-container">
        <div className="page-header">
          <h1 className="page-title">Configuración</h1>
        </div>

        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

        <motion.div
          className="config-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="config-card">
            <div className="config-card-header">
              <div className="config-card-title-group">
                <div className="config-card-icon">
                  <Icons.PesoIcon size={24} />
                </div>
                <div>
                  <h2 className="config-card-title">Ajustes del negocio</h2>
                </div>
              </div>
            </div>

            <div className="config-card-body">
              {loading ? (
                <div className="config-loading">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Icons.SpinnerIcon size={32} />
                  </motion.div>
                  <p>Cargando configuración...</p>
                </div>
              ) : (
                <div className="config-form">
                  {CONFIG_FIELDS.map((field) => (
                    <div key={field.key} className="form-group">
                      <div>
                        <label className="form-label" htmlFor={field.key}>
                          {field.label}
                        </label>
                        <p className="form-help">{field.description}</p>
                      </div>
                      <div className="input-group">
                        <input
                          id={field.key}
                          type="number"
                          min="0"
                          max="100"
                          step="0.01"
                          value={configValues[field.key] ?? ""}
                          onChange={(event) =>
                            handleChange(field.key, event.target.value)
                          }
                          disabled={saving}
                          className="form-input"
                        />
                        {field.suffix && (
                          <span className="input-addon">{field.suffix}</span>
                        )}
                      </div>
                    </div>
                  ))}

                  <div className="form-actions">
                    <button
                      className="btn btn-secondary"
                      onClick={handleReset}
                      disabled={saving || !hasChanges}
                    >
                      <Icons.UndoIcon size={16} /> Revertir
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleSave}
                      disabled={saving || !hasChanges}
                    >
                      {saving ? (
                        <>
                          <Icons.SpinnerIcon size={16} /> Guardando...
                        </>
                      ) : (
                        <>
                          <Icons.SaveIcon size={16} /> Guardar cambios
                        </>
                      )}
                    </button>
                  </div>

                  {success && (
                    <motion.div
                      className="success-message"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                    >
                      <Icons.CheckIcon size={18} /> Valores guardados correctamente.
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </div>
        </motion.div>

        <motion.div
          className="config-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.08 }}
        >
          <div className="config-card">
            <div className="config-card-header">
              <div className="config-card-title-group">
                <div className="config-card-icon">
                  <Icons.CogIcon size={24} />
                </div>
                <div>
                  <h2 className="config-card-title">Delivery gratis</h2>
                  <p className="config-card-description">
                    El delivery se habilita cuando el subtotal del pedido alcanza este mínimo.
                  </p>
                </div>
              </div>
            </div>
            <div className="config-card-body">
              {deliveryError && (
                <ErrorAlert
                  message={deliveryError}
                  onClose={() => setDeliveryError(null)}
                />
              )}
              {loading ? (
                <div className="config-loading">
                  <p>Cargando configuración...</p>
                </div>
              ) : (
                <div className="config-form">
                  <div className="form-group">
                    <div>
                      <label className="form-label" htmlFor="monto_minimo_delivery">
                        Monto mínimo del pedido
                      </label>
                      <p className="form-help">
                        Se calcula sobre productos y promociones, antes del recargo por transferencia.
                        El valor inicial es $13.000. Guardá el cambio y publicá el catálogo para actualizar
                        la web de pedidos. Usá $0 para habilitar delivery sin mínimo.
                      </p>
                    </div>
                    <div className="input-group">
                      <input
                        id="monto_minimo_delivery"
                        type="number"
                        min="0"
                        max="9999999999.99"
                        step="0.01"
                        value={deliveryMinimum}
                        onChange={(event) => setDeliveryMinimum(event.target.value)}
                        disabled={deliverySaving}
                        className="form-input"
                      />
                      <span className="input-addon">$</span>
                    </div>
                  </div>
                  <div className="form-actions">
                    <button
                      className="btn btn-secondary"
                      type="button"
                      onClick={() => {
                        setDeliveryMinimum(originalDeliveryMinimum);
                        setDeliveryError(null);
                      }}
                      disabled={deliverySaving || deliveryMinimum === originalDeliveryMinimum}
                    >
                      <Icons.UndoIcon size={16} /> Revertir
                    </button>
                    <button
                      className="btn btn-primary"
                      type="button"
                      onClick={handleSaveDeliveryMinimum}
                      disabled={
                        deliverySaving ||
                        deliveryMinimum === originalDeliveryMinimum ||
                        deliveryMinimum.trim() === ""
                      }
                    >
                      {deliverySaving ? (
                        <>
                          <Icons.SpinnerIcon size={16} /> Guardando...
                        </>
                      ) : (
                        <>
                          <Icons.SaveIcon size={16} /> Guardar mínimo
                        </>
                      )}
                    </button>
                  </div>
                  {deliverySuccess && (
                    <motion.div
                      className="success-message"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                    >
                      <Icons.CheckIcon size={18} />
                      Monto mínimo guardado. Publicá el catálogo para reflejarlo en pedidos.
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </div>
        </motion.div>

        <motion.div
          className="config-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="config-card">
            <div className="config-card-header">
              <div className="config-card-title-group">
                <div className="config-card-icon">
                  <Icons.SaveIcon size={24} />
                </div>
                <div>
                  <h2 className="config-card-title">Catálogo para pedidos</h2>
                  <p className="config-card-description">
                    Publica productos, precios, imágenes, recargo por transferencia y el mínimo de delivery para la web de pedidos.
                  </p>
                </div>
              </div>
            </div>
            <div className="config-card-body">
              <div className="catalog-publish-panel">
                <p className="catalog-published-at">
                  Última publicación:{" "}
                  <strong>
                    {catalogPublishedAt
                      ? new Date(catalogPublishedAt).toLocaleString()
                      : "Todavía no se publicó"}
                  </strong>
                </p>
                {catalogError && (
                  <ErrorAlert
                    message={catalogError}
                    onClose={() => setCatalogError(null)}
                  />
                )}
                <div className="form-actions">
                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={handlePublishCatalog}
                    disabled={catalogPublishing || loading}
                  >
                    {catalogPublishing ? (
                      <>
                        <Icons.SpinnerIcon size={16} /> Publicando...
                      </>
                    ) : (
                      "Publicar catálogo"
                    )}
                  </button>
                </div>
                {catalogResult && (
                  <div className="success-message" role="status">
                    <Icons.CheckIcon size={18} />
                    {catalogResult.actualizado
                      ? "Catálogo actualizado"
                      : "El catálogo ya estaba actualizado"}
                    : {catalogResult.productos} productos, {catalogResult.categorias}{" "}
                    categorías y {catalogResult.ofertas} ofertas.
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
