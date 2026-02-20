import { forwardRef } from "react";
import DatePicker, { registerLocale } from "react-datepicker";
import { es } from "date-fns/locale/es";
import { Calendar, Moon, Sun, RotateCcw, FileText } from "lucide-react";
import type { ReportMode, ReportRequest } from "../services/reportService";
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

const ReportConfigPanel = ({
  config,
  onChange,
  onSubmit,
  onReset,
  loading,
  validationMessage,
}: ReportConfigPanelProps) => {
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
    { key: "resumenDia" as const, title: "Resumen por dia" },
    { key: "resumenCategoria" as const, title: "Resumen por categoria" },
    { key: "resumenProductos" as const, title: "Resumen de productos vendidos" },
    { key: "detalleVentas" as const, title: "Detalle de ventas" },
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

      <div className="rcp-row">
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

      </div>

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
        <button
          type="button"
          className="rcp-btn-generate"
          onClick={onSubmit}
          disabled={loading || Boolean(validationMessage)}
        >
          {loading ? (
            <span className="rcp-spinner" />
          ) : (
            <FileText size={16} />
          )}
          {loading ? "Generando..." : "Generar reporte"}
        </button>
      </div>
    </section>
  );
};

export default ReportConfigPanel;
