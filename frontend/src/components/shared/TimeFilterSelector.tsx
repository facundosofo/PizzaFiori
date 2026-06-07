/**
 * TimeFilterSelector - Selector de filtro temporal
 * Permite seleccionar período de análisis: Hoy, Últimos 7 días, Último mes, Último año, Histórico
 * Usado en componentes de análisis de ventas y productos
 */

import { useState, useRef, useEffect } from 'react';
import '../../styles/shared/time-filter-selector.css';

export type TimeFilter = 'today' | 'last_7_days' | 'last_month' | 'last_year' | 'all_time';

export interface TimeFilterOption {
  value: TimeFilter;
  label: string;
  description: string;
}

export const TIME_FILTER_OPTIONS: TimeFilterOption[] = [
  { value: 'last_month', label: 'Mes actual', description: 'Del 1° del mes hasta hoy' },
  { value: 'last_year', label: 'Año actual', description: 'Del 1° de enero hasta hoy' },
  { value: 'all_time', label: 'Histórico', description: 'Todos los datos' },
];

interface TimeFilterSelectorProps {
  value: TimeFilter;
  onChange: (filter: TimeFilter) => void;
  className?: string;
  options?: TimeFilterOption[];
}

const TimeFilterSelector = ({ value, onChange, className = '', options = TIME_FILTER_OPTIONS }: TimeFilterSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <div className={`time-filter-selector ${className}`} ref={dropdownRef}>
      <button
        className="time-filter-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        {selectedOption?.label || 'Período'}
        <span className={`chevron ${isOpen ? 'open' : ''}`}>▼</span>
      </button>

      {isOpen && (
        <div className="time-filter-dropdown">
          {options.map((option) => (
            <button
              key={option.value}
              className={`time-filter-option ${value === option.value ? 'active' : ''}`}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default TimeFilterSelector;
