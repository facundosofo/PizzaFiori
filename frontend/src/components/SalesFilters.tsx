import { useState } from "react";
import { SearchIcon, XIcon } from "./Icons";
import { validateDateRange } from "../utils/formatters";
import "../styles/sales-filters.css";

interface SalesFiltersProps {
  onFilter: (dateFrom: Date | null, dateTo: Date | null) => void;
  onClear: () => void;
}

const SalesFilters = ({ onFilter, onClear }: SalesFiltersProps) => {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSearch = () => {
    setError(null);

    // Convert input values to Date objects
    const fromDate = dateFrom ? new Date(dateFrom) : null;
    const toDate = dateTo ? new Date(dateTo) : null;

    // Validate date range
    const validationError = validateDateRange(fromDate, toDate);
    if (validationError) {
      setError(validationError);
      return;
    }

    // Apply filter
    onFilter(fromDate, toDate);
  };

  const handleClear = () => {
    setDateFrom("");
    setDateTo("");
    setError(null);
    onClear();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  // Get max date (today) for validation
  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="sales-filters">
      <div className="sales-filters-row">
        <div className="filter-group">
          <label htmlFor="date-from">Desde</label>
          <input
            id="date-from"
            type="date"
            className="filter-date-input"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            onKeyPress={handleKeyPress}
            max={today}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="date-to">Hasta</label>
          <input
            id="date-to"
            type="date"
            className="filter-date-input"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            onKeyPress={handleKeyPress}
            max={today}
          />
        </div>

        <div className="filter-actions">
          <button
            className="filter-btn search"
            onClick={handleSearch}
            title="Buscar ventas"
          >
            <SearchIcon size={18} />
            <span>Buscar</span>
          </button>

          <button
            className="filter-btn clear"
            onClick={handleClear}
            title="Limpiar filtros"
          >
            <XIcon size={18} />
            <span>Limpiar</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="filter-error">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};

export default SalesFilters;
