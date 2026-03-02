import { forwardRef, useEffect, useRef, useState } from "react";
import DatePicker, { registerLocale } from "react-datepicker";
import { es } from "date-fns/locale/es";
import { Calendar, Moon, Sun, RotateCcw, FileText } from "lucide-react";
import type { ReportMode, ReportRequest, ReportType, DateRangeMode } from "../services/reportService";
import { getAvailableYears } from "../services/reportService";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/shared/datepicker-custom.css";
import "../styles/sales-filters.css";

registerLocale("es", es);

type ReportConfigPanelProps = {
  config: ReportRequest;
  onChange: (next: ReportRequest) => void;
  onSubmit: () => void;
  onReset: () => void;
  loading: boolean;
  validationMessage: string | null;
};

type DateRangeInputProps = {
  value?: string;
  onClick?: () => void;
  placeholder?: string;
};

const DateRangeInput = forwardRef<HTMLButtonElement, DateRangeInputProps>(
  ({ value, onClick, placeholder }, ref) => (
    <button
      type="button"
      className="filter-date-input rcp-date-input"
      onClick={onClick}
      ref={ref}
    >
      <Calendar size={16} className="rcp-date-icon" />
      <span className="rcp-date-label">
        {value || placeholder}
      </span>
    </button>
  )
);

DateRangeInput.displayName = "DateRangeInput";

const REPORT_TYPES: { key: ReportType; label: string }[] = [
  { key: "general", label: "General" },
  { key: "balance", label: "Balance" },
  { key: "ventas", label: "Ventas" },
  { key: "costo", label: "Costo" },
];

const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const currentYear = new Date().getFullYear();
const FALLBACK_YEARS = [currentYear];

const ReportConfigPanel = ({
  config,
  onChange,
  onSubmit,
  onReset,
  loading,
  validationMessage,
}: ReportConfigPanelProps) => {
  const [availableYears, setAvailableYears] = useState<number[]>(FALLBACK_YEARS);

  // Refs para acceder a los valores actuales sin re-disparar el efecto
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;
  const configRef = useRef(config);
  configRef.current = config;

  useEffect(() => {
    getAvailableYears()
      .then((years) => {
        if (years.length > 0) {
          const minYear = Math.min(...years);
          const range = Array.from(
            { length: currentYear - minYear + 1 },
            (_, i) => minYear + i
          );
          setAvailableYears(range);
          // Si el año seleccionado está fuera del rango, seleccionar el más reciente
          if (configRef.current.selectedYear < minYear) {
            onChangeRef.current({ ...configRef.current, selectedYear: currentYear });
          }
        }
      })
      .catch(() => { /* mantiene FALLBACK_YEARS */ });
  }, []);
  const handleTypeChange = (type: ReportType) => {
    const newMode: DateRangeMode =
      type === "ventas"
        ? config.dateRangeMode
        : config.dateRangeMode === "rango"
        ? "mes"
        : config.dateRangeMode;
    onChange({ ...config, reportType: type, dateRangeMode: newMode });
  };

  const handleDateModeChange = (mode: DateRangeMode) => {
    const updatedSections = { ...config.sections };
    if (mode === "anio") {
      updatedSections.resumenMes = true;
      updatedSections.costoResumenMes = true;
      updatedSections.balanceResumenMes = true;
    }
    onChange({ ...config, dateRangeMode: mode, sections: updatedSections });
  };

  const handleRangeChange = (range: [Date | null, Date | null]) => {
    const [dateFrom, dateTo] = range;
    onChange({ ...config, dateFrom, dateTo });
  };

  const handleCalendarClose = () => {
    if (config.dateFrom && !config.dateTo) {
      onChange({ ...config, dateTo: new Date() });
    }
  };

  const handleModeChange = (mode: ReportMode) => {
    onChange({ ...config, mode });
  };

  const handleToggleSection = (key: keyof ReportRequest["sections"]) => {
    onChange({
      ...config,
      sections: {
        ...config.sections,
        [key]: !config.sections[key],
      },
    });
  };

  const sections = [
    { key: "resumenPeriodo" as const, title: "Resumen del periodo" },
    ...(config.dateRangeMode === "anio"
      ? [{ key: "resumenMes" as const, title: "Resumen por mes" }]
      : [{ key: "resumenDia" as const, title: "Resumen por dia" }]),
    { key: "resumenCategoria" as const, title: "Resumen por categoria" },
    { key: "resumenProductos" as const, title: "Resumen de productos vendidos" },
    { key: "detalleVentas" as const, title: "Detalle de ventas" },
  ];

  const isVentas = config.reportType === "ventas";
  const isCosto = config.reportType === "costo";
  const isBalance = config.reportType === "balance";

  const costSections = [
    { key: "costoResumenPeriodo" as const, title: "Resumen del período" },
    ...(config.dateRangeMode === "anio"
      ? [{ key: "costoResumenMes" as const, title: "Resumen por mes" }]
      : []),
    { key: "costoResumenCategoria" as const, title: "Resumen por categoría" },
    { key: "costoDetalleCostos" as const, title: "Detalle de costos" },
  ];

  const balanceSections = [
    { key: "balanceResumenPeriodo" as const, title: "Resumen del período" },
    ...(config.dateRangeMode === "anio"
      ? [{ key: "balanceResumenMes" as const, title: "Resumen por mes" }]
      : []),
  ];

  const dateModes: { key: DateRangeMode; label: string }[] = isVentas
    ? [
        { key: "rango", label: "Rango de fechas" },
        { key: "mes", label: "Mes específico" },
        { key: "anio", label: "Año completo" },
      ]
    : [
        { key: "mes", label: "Mes específico" },
        { key: "anio", label: "Año completo" },
      ];

  return (
    <section className="rcp">
      <div className="rcp-header">
        <h2 className="rcp-title">Personaliza tu reporte</h2>
        <label
          className={`rcp-toggle-mode rcp-toggle-header ${
            config.mode === "dark" ? "is-dark" : "is-light"
          }`}
        >
          <input
            type="checkbox"
            checked={config.mode === "dark"}
            onChange={() =>
              handleModeChange(config.mode === "dark" ? "light" : "dark")
            }
          />
          <span className="rcp-track" aria-hidden="true">
            <span title="Modo claro">
              <Sun size={14} className="rcp-icon-sun" />
            </span>
            <span title="Modo oscuro">
              <Moon size={14} className="rcp-icon-moon" />
            </span>
            <span className="rcp-thumb" />
          </span>
        </label>
      </div>

      {/* Tipo de reporte */}
      <div className="rcp-type-tabs-wrapper">
        <div className="rcp-type-tabs">
          {REPORT_TYPES.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              className={`rcp-type-tab ${config.reportType === key ? "active" : ""}`}
              onClick={() => handleTypeChange(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Modo de periodo */}
      <div className="rcp-field filter-group">
        <label>Periodo</label>
        <div className="rcp-date-mode-selector">
          {dateModes.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              className={`rcp-date-mode-pill ${config.dateRangeMode === key ? "active" : ""}`}
              onClick={() => handleDateModeChange(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Inputs de fecha según modo */}
      <div className="rcp-row">
        {config.dateRangeMode === "rango" && (
          <div className="rcp-field filter-group filter-group-range">
            <label>Rango de fechas</label>
            <DatePicker
              selectsRange
              startDate={config.dateFrom}
              endDate={config.dateTo}
              onChange={(update) => handleRangeChange(update as [Date | null, Date | null])}
              onCalendarClose={handleCalendarClose}
              dateFormat="dd/MM/yyyy"
              maxDate={new Date()}
              placeholderText="Seleccionar Desde - Hasta"
              calendarClassName="custom-calendar"
              showMonthDropdown
              showYearDropdown
              dropdownMode="select"
              popperPlacement="bottom-start"
              autoComplete="off"
              monthsShown={1}
              locale="es"
              formatWeekDay={(day) => day.charAt(0).toUpperCase()}
              customInput={
                <DateRangeInput placeholder="Seleccionar Desde - Hasta" />
              }
            />
            {validationMessage && (
              <p className="rcp-validation">{validationMessage}</p>
            )}
          </div>
        )}

        {config.dateRangeMode === "mes" && (
          <div className="rcp-field filter-group">
            <label>Mes y año</label>
            <div className="rcp-month-year-selector">
              <select
                className="rcp-select"
                value={config.selectedMonth}
                onChange={(e) =>
                  onChange({ ...config, selectedMonth: Number(e.target.value) })
                }
              >
                {MONTHS.map((name, i) => (
                  <option key={i} value={i}>
                    {name}
                  </option>
                ))}
              </select>
              <select
                className="rcp-select"
                value={config.selectedYear}
                onChange={(e) =>
                  onChange({ ...config, selectedYear: Number(e.target.value) })
                }
              >
                {availableYears.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {config.dateRangeMode === "anio" && (
          <div className="rcp-field filter-group">
            <label>Año</label>
            <select
              className="rcp-select"
              value={config.selectedYear}
              onChange={(e) =>
                onChange({ ...config, selectedYear: Number(e.target.value) })
              }
            >
              {availableYears.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Secciones */}
      {isVentas ? (
        <div className="rcp-sections-block filter-group">
          <label>Secciones</label>
          <div className="rcp-toggles">
            {sections.map((section) => (
              <button
                key={section.key}
                type="button"
                className={`rcp-toggle-row ${config.sections[section.key] ? "is-on" : ""}`}
                onClick={() => handleToggleSection(section.key)}
              >
                <span className="rcp-switch" aria-hidden="true" />
                <span className="rcp-toggle-name">{section.title}</span>
              </button>
            ))}
          </div>
        </div>
      ) : isCosto ? (
        <div className="rcp-sections-block filter-group">
          <label>Secciones</label>
          <div className="rcp-toggles">
            {costSections.map((section) => (
              <button
                key={section.key}
                type="button"
                className={`rcp-toggle-row ${config.sections[section.key] ? "is-on" : ""}`}
                onClick={() => handleToggleSection(section.key)}
              >
                <span className="rcp-switch" aria-hidden="true" />
                <span className="rcp-toggle-name">{section.title}</span>
              </button>
            ))}
          </div>
        </div>
      ) : isBalance ? (
        <div className="rcp-sections-block filter-group">
          <label>Secciones</label>
          <div className="rcp-toggles">
            {balanceSections.map((section) => (
              <button
                key={section.key}
                type="button"
                className={`rcp-toggle-row ${config.sections[section.key] ? "is-on" : ""}`}
                onClick={() => handleToggleSection(section.key)}
              >
                <span className="rcp-switch" aria-hidden="true" />
                <span className="rcp-toggle-name">{section.title}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="rcp-coming-soon">
          <span className="rcp-coming-soon-text">Secciones disponibles próximamente</span>
        </div>
      )}

      <div className="rcp-actions">
        <button
          type="button"
          className="rcp-btn-reset"
          onClick={onReset}
          disabled={loading}
          title="Restablecer"
        >
          <RotateCcw size={16} />
          Restablecer
        </button>
        {isVentas || isCosto || isBalance ? (
          <button
            type="button"
            className="rcp-btn-generate"
            onClick={onSubmit}
            disabled={loading || Boolean(validationMessage)}
          >
            {loading ? <span className="rcp-spinner" /> : <FileText size={16} />}
            {loading ? "Generando..." : "Generar reporte"}
          </button>
        ) : (
          <button type="button" className="rcp-btn-generate rcp-btn-soon" disabled>
            <FileText size={16} />
            Próximamente
          </button>
        )}
      </div>
    </section>
  );
};

export default ReportConfigPanel;
