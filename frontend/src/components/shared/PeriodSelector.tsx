/**
 * PeriodSelector - Componente reutilizable para seleccionar períodos de tiempo
 * Usado en gráficos y análisis con tabs: diario, mensual y anual
 */

import '../../styles/shared/period-selector.css';

export type Period = 'daily' | 'monthly' | 'yearly';

interface PeriodSelectorProps {
  selectedPeriod: Period;
  onPeriodChange: (period: Period) => void;
}

const PeriodSelector = ({ selectedPeriod, onPeriodChange }: PeriodSelectorProps) => {
  const periods: { value: Period; label: string }[] = [
    { value: 'daily', label: 'Diario' },
    { value: 'monthly', label: 'Mensual' },
    { value: 'yearly', label: 'Anual' },
  ];

  return (
    <div className="period-selector">
      {periods.map((period) => (
        <button
          key={period.value}
          className={`period-tab ${selectedPeriod === period.value ? 'active' : ''}`}
          onClick={() => onPeriodChange(period.value)}
        >
          {period.label}
        </button>
      ))}
    </div>
  );
};

export default PeriodSelector;
