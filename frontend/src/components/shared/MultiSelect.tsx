import { useState, useMemo } from "react";
import { XIcon } from "./Icons";
import "../../styles/shared/multi-select.css";

export interface MultiSelectItem {
  id: number;
  label: string;
  optionLabel?: string; // Label solo para las opciones del dropdown
  disabled?: boolean;
}

interface MultiSelectProps {
  items: MultiSelectItem[];
  selectedIds: number[];
  onChange: (selectedIds: number[]) => void;
  label?: string;
  searchable?: boolean;
  placeholder?: string;
  minSelection?: number;
  maxSelection?: number;
  className?: string;
}

const MultiSelect = ({
  items,
  selectedIds,
  onChange,
  label,
  searchable = false,
  placeholder = "Buscar...",
  minSelection,
  maxSelection,
  className = "",
}: MultiSelectProps) => {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredItems = useMemo(() => {
    if (!searchable || !searchTerm) return items;
    return items.filter((item) =>
      item.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [items, searchTerm, searchable]);

  const selectedItems = useMemo(() => {
    return items.filter((item) => selectedIds.includes(item.id));
  }, [items, selectedIds]);

  const handleToggle = (itemId: number) => {
    const isSelected = selectedIds.includes(itemId);
    
    if (isSelected) {
      onChange(selectedIds.filter((id) => id !== itemId));
    } else {
      // Validar máximo
      if (maxSelection && selectedIds.length >= maxSelection) {
        return;
      }
      onChange([...selectedIds, itemId]);
    }
  };

  const handleRemove = (itemId: number) => {
    onChange(selectedIds.filter((id) => id !== itemId));
  };

  return (
    <div className={`multi-select ${className}`}>
      {label && <label className="multi-select-label">{label}</label>}

      {/* Chips de seleccionados */}
      {selectedItems.length > 0 && (
        <div className="multi-select-chips">
          {selectedItems.map((item) => (
            <div key={item.id} className="multi-select-chip">
              <span>{item.label}</span>
              <button
                type="button"
                onClick={() => handleRemove(item.id)}
                className="chip-remove-btn"
                aria-label={`Eliminar ${item.label}`}
              >
                <XIcon />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Búsqueda */}
      {searchable && (
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={placeholder}
          className="multi-select-search"
        />
      )}

      {/* Grid de checkboxes */}
      <div className="multi-select-options">
        {filteredItems.length === 0 ? (
          <p className="multi-select-empty">No se encontraron resultados</p>
        ) : (
          filteredItems.map((item) => {
            const isSelected = selectedIds.includes(item.id);
            const isDisabled = item.disabled || 
              (!isSelected && maxSelection !== undefined && selectedIds.length >= maxSelection);

            return (
              <label
                key={item.id}
                className={`multi-select-option ${isSelected ? "multi-select-option-selected" : ""} ${
                  isDisabled ? "multi-select-option-disabled" : ""
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => handleToggle(item.id)}
                  disabled={isDisabled}
                  className="multi-select-checkbox"
                />
                <span className="multi-select-option-label">{item.optionLabel || item.label}</span>
              </label>
            );
          })
        )}
      </div>

      {/* Info de validación */}
      {(minSelection !== undefined || maxSelection !== undefined) && (
        <div className="multi-select-info">
          {minSelection !== undefined && (
            <span className={selectedIds.length < minSelection ? "text-warning" : ""}>
              Mínimo: {minSelection}
            </span>
          )}
          {maxSelection !== undefined && (
            <span className={selectedIds.length >= maxSelection ? "text-warning" : ""}>
              Máximo: {maxSelection}
            </span>
          )}
          <span>Seleccionados: {selectedIds.length}</span>
        </div>
      )}
    </div>
  );
};

export default MultiSelect;
