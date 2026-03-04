import { useState } from "react";
import DatePicker, { registerLocale } from "react-datepicker";
import { es } from "date-fns/locale/es";
import DateRangeInput from "./shared/DateRangeInput";
import FilterBar from "./shared/FilterBar";
import { validateDateRange } from "../utils/formatters";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/sales-filters.css";
import "../styles/shared/datepicker-custom.css";

registerLocale("es", es);

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

  const handleCalendarClose = () => {
    if (dateFrom && !dateTo) {
      const today = new Date();
      setDateRange([dateFrom, today]);
      onFilter(dateFrom, today);
    }
  };

  const today = new Date();

  const quickFilters = [
    { label: "Ayer", onClick: () => applyQuickFilter("yesterday"), title: "Filtrar ventas de ayer" },
    { label: "Hoy", onClick: () => applyQuickFilter("today"), title: "Filtrar ventas de hoy" },
    { label: "Última semana", onClick: () => applyQuickFilter("week"), title: "Filtrar últimos 7 días" },
    { label: "Último mes", onClick: () => applyQuickFilter("month"), title: "Filtrar últimos 30 días" },
  ];

  return (
    <FilterBar
      onSearch={handleSearch}
      onClear={handleClear}
      error={error}
      quickFilters={quickFilters}
    >
      <div className="filter-group filter-group-range">
        <label htmlFor="date-range">Rango de fechas</label>
        <DatePicker
          id="date-range"
          selectsRange={true}
          startDate={dateFrom}
          endDate={dateTo}
          onChange={(update) => {
            setDateRange(update as [Date | null, Date | null]);
          }}
          onCalendarClose={handleCalendarClose}
          dateFormat="dd/MM/yyyy"
          maxDate={today}
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
      </div>
    </FilterBar>
  );
};

export default SalesFilters;
