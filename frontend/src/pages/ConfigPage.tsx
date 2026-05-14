import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { getRecargoConfig, updateRecargoConfig } from "../services/configService";
import ErrorAlert from "../components/shared/ErrorAlert";
import * as Icons from "../components/shared/Icons";
import "../styles/config-page.css";

const CONFIG_FIELDS = [
  {
    key: "recargo_transferencia",
    label: "Recargo por transferencia/débito",
    description:
      "Porcentaje que se aplica a las ventas pagadas por transferencia o débito.",
    suffix: "%",
  },
];

export default function ConfigPage() {
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

  useEffect(() => {
    const loadConfig = async () => {
      try {
        setLoading(true);
        setError(null);
        const config = await getRecargoConfig();
        const value = String(config.porcentaje_recargo ?? "10");
        setConfigValues({ recargo_transferencia: value });
        setOriginalValues({ recargo_transferencia: value });
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

  return (
    <div className="config-page">
      <div className="config-container">
        <div className="page-header">
          <h1 className="page-title">Configuración</h1>
          <p className="page-subtitle">
            Gestiona las claves y valores del negocio desde un solo lugar.
          </p>
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
                  <Icons.CogIcon size={24} />
                </div>
                <div>
                  <h2 className="config-card-title">Ajustes del negocio</h2>
                  <p className="config-card-description">
                    Actualiza los valores de negocio que se usan en ventas y procesos.
                  </p>
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
                      <Icons.EditIcon size={16} /> Revertir
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
      </div>
    </div>
  );
}

