/**
 * WeekdayPeriodSelector - Selector de período para gráfico por día de semana
 * 
 * Periodos:
 * - Semanal: última semana completa (Lun-Dom)
 * - Mensual: último mes calendario completo
 * - Anual: últimos 12 meses completos
 * - Histórico: sin filtro
 */

import { useState, useRef, useEffect } from 'react';
import '../../styles/shared/category-selector.css';

export type WeekdayPeriod = 'weekly' | 'monthly' | 'yearly' | 'historic';

interface WeekdayPeriodSelectorProps {
  selectedPeriod: WeekdayPeriod;
  onPeriodChange: (period: WeekdayPeriod) => void;
}

const WeekdayPeriodSelector = ({ selectedPeriod, onPeriodChange }: WeekdayPeriodSelectorProps) => {
  const periods: { value: WeekdayPeriod; label: string }[] = [
    { value: 'weekly', label: 'Semanal' },
    { value: 'monthly', label: 'Mensual' },
    { value: 'yearly', label: 'Anual' },
    { value: 'historic', label: 'Historico' },
  ];

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = periods.find((period) => period.value === selectedPeriod);

  return (
    <div className="category-selector" ref={dropdownRef}>
      <button
        className="category-selector-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        {selectedOption?.label || 'Periodo'}
        <span className={`chevron ${isOpen ? 'open' : ''}`}>▼</span>
      </button>

      {isOpen && (
        <div className="category-dropdown">
          {periods.map((period) => (
            <button
              key={period.value}
              className={`category-option ${selectedPeriod === period.value ? 'active' : ''}`}
              onClick={() => {
                onPeriodChange(period.value);
                setIsOpen(false);
              }}
            >
              {period.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default WeekdayPeriodSelector;
