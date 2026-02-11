import { useState } from "react";
import DatePicker, { registerLocale } from "react-datepicker";
import { es } from "date-fns/locale/es";
import * as Icons from './shared/Icons';
import { validateDateRange } from "../utils/formatters";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/sales-filters.css";
import "../styles/shared/datepicker-custom.css";

// Registrar locale español
registerLocale('es', es);
interface SalesFiltersProps {
  onFilter: (dateFrom: Date | null, dateTo: Date | null) => void;
  onClear: () => void;
}

const SalesFilters = ({ onFilter, onClear }: SalesFiltersProps) => {
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [dateFrom, dateTo] = dateRange;
  const [error, setError] = useState<string | null>(null);

  // Quick filter helpers
  const applyQuickFilter = (type: "today" | "yesterday" | "week" | "month") => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);

    const monthAgo = new Date(today);
    monthAgo.setMonth(today.getMonth() - 1);

    let from: Date;
    let to: Date;

    switch (type) {
      case "today":
        from = to = today;
        break;
      case "yesterday":
        from = to = yesterday;
        break;
      case "week":
        from = weekAgo;
        to = today;
        break;
      case "month":
        from = monthAgo;
        to = today;
        break;
    }

    setDateRange([from, to]);
    setError(null);

    // Auto-apply filter
    onFilter(from, to);
  };

  const handleSearch = () => {
    setError(null);

    // Validate date range
    const validationError = validateDateRange(dateFrom, dateTo);
    if (validationError) {
      setError(validationError);
      return;
    }

    // Apply filter
    onFilter(dateFrom, dateTo);
  };

  const handleClear = () => {
    setDateRange([null, null]);
    setError(null);
    onClear();
  };

  // Get max date (today) for validation
  const today = new Date();

  return (
    <div className="sales-filters">
      <div className="sales-filters-row">
        <div className="filter-group filter-group-range">
          <label htmlFor="date-range">Seleccionar rango de fechas</label>
          <DatePicker
            id="date-range"
            selectsRange={true}
            startDate={dateFrom}
            endDate={dateTo}
            onChange={(update) => {
              setDateRange(update as [Date | null, Date | null]);
            }}
            dateFormat="dd/MM/yyyy"
            maxDate={today}
            placeholderText="Seleccionar Desde - Hasta"
            className="filter-date-input"
            calendarClassName="custom-calendar"
            showMonthDropdown
            showYearDropdown
            dropdownMode="select"
            popperPlacement="bottom-start"
            autoComplete="off"
            monthsShown={1}
            locale="es"
            formatWeekDay={(day) => day.charAt(0).toUpperCase()}
          />
        </div>

        <div className="filter-group quick-filters-group">
          <label>Filtros rápidos</label>
          <div className="quick-filters">
            <button
              className="quick-filter-btn"
              onClick={() => applyQuickFilter("yesterday")}
              title="Filtrar ventas de ayer"
            >
              Ayer
            </button>
            <button
              className="quick-filter-btn"
              onClick={() => applyQuickFilter("today")}
              title="Filtrar ventas de hoy"
            >
              Hoy
            </button>
            <button
              className="quick-filter-btn"
              onClick={() => applyQuickFilter("week")}
              title="Filtrar últimos 7 días"
            >
              Última semana
            </button>
            <button
              className="quick-filter-btn"
              onClick={() => applyQuickFilter("month")}
              title="Filtrar últimos 30 días"
            >
              Último mes
            </button>
          </div>
        </div>

        <div className="filter-actions">
          <button
            className="filter-btn search"
            onClick={handleSearch}
            title="Buscar ventas"
          >
            <Icons.SearchIcon size={18} />
            <span>Buscar</span>
          </button>

          <button
            className="filter-btn clear"
            onClick={handleClear}
            title="Limpiar filtros"
          >
            <Icons.XIcon size={18} />
            <span>Limpiar</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="filter-error">
          <Icons.WarningIcon size={18} /> {error}
        </div>
      )}
    </div>
  );
};

export default SalesFilters;
