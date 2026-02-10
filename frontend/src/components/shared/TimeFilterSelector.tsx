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
  { value: 'today', label: 'Hoy', description: 'Ventas de hoy' },
  { value: 'last_7_days', label: 'Últimos 7 días', description: 'Últimos 7 días' },
  { value: 'last_month', label: 'Último mes', description: 'Últimos 30 días' },
  { value: 'last_year', label: 'Último año', description: 'Últimos 12 meses' },
  { value: 'all_time', label: 'Histórico', description: 'Todos los datos' },
];

interface TimeFilterSelectorProps {
  value: TimeFilter;
  onChange: (filter: TimeFilter) => void;
  className?: string;
}

const TimeFilterSelector = ({ value, onChange, className = '' }: TimeFilterSelectorProps) => {
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

  const selectedOption = TIME_FILTER_OPTIONS.find(opt => opt.value === value);

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
          {TIME_FILTER_OPTIONS.map((option) => (
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
