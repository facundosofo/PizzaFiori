import { useState, useMemo, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { ChevronDownIcon } from "./Icons";
import "../../styles/shared/searchable-select.css";

export interface SelectOption {
  value: number;
  label: string;
  disabled?: boolean;
}

interface SearchableSelectProps {
  options: SelectOption[];
  value: number;
  onChange: (value: number) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  searchable?: boolean;
  id?: string;
  disabled?: boolean;
  className?: string;
}

const SearchableSelect = ({
  options,
  value,
  onChange,
  placeholder = "Seleccionar...",
  searchPlaceholder = "Buscar...",
  searchable = true,
  id,
  disabled = false,
  className = "",
}: SearchableSelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const DROPDOWN_MARGIN = 8;
  const DROPDOWN_MAX_HEIGHT = 320;

  const selectedOption = useMemo(() => {
    return options.find((opt) => opt.value === value);
  }, [options, value]);

  const filteredOptions = useMemo(() => {
    if (!searchable || !searchTerm) return options;
    return options.filter((option) =>
      option.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [options, searchTerm, searchable]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };

    const updatePosition = () => {
      if (containerRef.current && isOpen) {
        const rect = containerRef.current.getBoundingClientRect();
        const top = rect.bottom + DROPDOWN_MARGIN;

        setDropdownPosition({
          top,
          left: rect.left,
          width: rect.width,
        });
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      window.addEventListener("scroll", updatePosition, true);
      window.addEventListener("resize", updatePosition);
      updatePosition();
      // Focus en el input cuando se abre
      if (searchable) {
        setTimeout(() => searchInputRef.current?.focus(), 0);
      }
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [isOpen]);

  const handleSelect = (optionValue: number) => {
    onChange(optionValue);
    setIsOpen(false);
    setSearchTerm("");
  };

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
      setSearchTerm("");
    }
  };

  return (
    <div
      ref={containerRef}
      className={`searchable-select ${isOpen ? "open" : ""} ${disabled ? "disabled" : ""} ${className}`}
      id={id}
    >
      {/* Selector principal */}
      <div className="searchable-select-trigger" onClick={handleToggle}>
        <span className={`searchable-select-value ${!selectedOption ? "placeholder" : ""}`}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDownIcon className={`searchable-select-icon ${isOpen ? "rotated" : ""}`} size={20} />
      </div>

      {/* Dropdown con búsqueda */}
      {isOpen && createPortal(
        <div 
          className="searchable-select-dropdown"
          style={{
            top: `${dropdownPosition.top}px`,
            left: `${dropdownPosition.left}px`,
            width: `${dropdownPosition.width}px`,
            maxHeight: `calc(100vh - ${DROPDOWN_MARGIN * 2}px)`,
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          {searchable && (
            <div className="searchable-select-search">
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={searchPlaceholder}
                className="searchable-select-input"
                onMouseDown={(e) => e.stopPropagation()}
              />
            </div>
          )}

          <div className="searchable-select-options">
            {filteredOptions.length === 0 ? (
              <div className="searchable-select-empty">No se encontraron resultados</div>
            ) : (
              filteredOptions.map((option) => (
                <div
                  key={option.value}
                  className={`searchable-select-option ${option.value === value ? "selected" : ""} ${
                    option.disabled ? "disabled" : ""
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!option.disabled) {
                      handleSelect(option.value);
                    }
                  }}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  {option.label}
                </div>
              ))
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default SearchableSelect;
