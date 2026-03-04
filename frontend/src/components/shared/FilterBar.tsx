import type { ReactNode } from "react";
import * as Icons from "./Icons";
import "../../styles/shared/filter-bar.css";

interface QuickFilter {
  label: string;
  onClick: () => void;
  title?: string;
}

interface FilterBarProps {
  onSearch: () => void;
  onClear: () => void;
  error?: string | null;
  quickFilters?: QuickFilter[];
  children: ReactNode;
}

const FilterBar = ({
  onSearch,
  onClear,
  error,
  quickFilters,
  children,
}: FilterBarProps) => {
  return (
    <div className="filter-bar">
      <div className="filter-bar-row">
        {children}

        {quickFilters && quickFilters.length > 0 && (
          <div className="filter-group quick-filters-group">
            <label>Filtros rápidos</label>
            <div className="quick-filters">
              {quickFilters.map((qf) => (
                <button
                  key={qf.label}
                  className="quick-filter-btn"
                  onClick={qf.onClick}
                  title={qf.title}
                >
                  {qf.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="filter-actions">
          <button
            className="filter-btn search"
            onClick={onSearch}
            title="Buscar"
          >
            <Icons.SearchIcon size={18} />
            <span>Buscar</span>
          </button>
          <button
            className="filter-btn clear"
            onClick={onClear}
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

export default FilterBar;
