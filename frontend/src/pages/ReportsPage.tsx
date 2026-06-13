import { useMemo, useState } from "react";
import ReportConfigPanel from "../components/ReportConfigPanel";
import ErrorAlert from "../components/shared/ErrorAlert";
import { validateDateRange } from "../utils/formatters";
import useGenerateReport from "../hooks/useGenerateReport";
import type { ReportRequest } from "../services/reportService";
import { ShieldOffIcon } from "../components/shared/Icons";
import { useAuth } from "../contexts/AuthContext";
import "../styles/reports.css";

const buildDefaultConfig = (): ReportRequest => ({
  reportType: "ventas",
  dateRangeMode: "rango",
  dateFrom: null,
  dateTo: null,
  selectedMonth: new Date().getMonth(),
  selectedYear: new Date().getFullYear(),
  mode: "light",
  sections: {
    resumenPeriodo: true,
    resumenDia: true,
    resumenMes: true,
    resumenCategoria: true,
    resumenProductos: true,
    detalleVentas: true,
    costoResumenPeriodo: true,
    costoResumenCategoria: true,
    costoResumenMes: true,
    costoDetalleCostos: true,
    generalResumenPeriodo: true,
    generalResumenMes: true,
    generalResumenCategoriaVentas: true,
    generalResumenProductos: true,
    generalResumenCategoriaGastos: true,
  },
});

const ReportsPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const [config, setConfig] = useState<ReportRequest>(buildDefaultConfig());
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const { generateReport, loading, error, clearError } = useGenerateReport();

  const validationMessage = useMemo(() => {
    if (config.dateRangeMode !== "rango") return null;
    return validateDateRange(config.dateFrom, config.dateTo);
  }, [config.dateRangeMode, config.dateFrom, config.dateTo]);

  if (!isAdmin) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    );
  }

  const handleGenerate = async () => {
    if (validationMessage) return;

    const ok = await generateReport(config);
    if (ok) {
      setSuccessMessage("Descarga iniciada. El reporte esta llegando a tu equipo.");
      setTimeout(() => setSuccessMessage(null), 4000);
    }
  };

  const handleReset = () => {
    setConfig(buildDefaultConfig());
  };

  return (
    <div className="reports-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Reportes</h1>
        </div>
      </div>

      <ErrorAlert message={error} onClose={clearError} />

      {successMessage && (
        <div className="report-success">
          <span className="report-success-dot" />
          {successMessage}
        </div>
      )}

      <ReportConfigPanel
        config={config}
        onChange={setConfig}
        onSubmit={handleGenerate}
        onReset={handleReset}
        loading={loading}
        validationMessage={validationMessage}
      />
    </div>
  );
};

export default ReportsPage;
