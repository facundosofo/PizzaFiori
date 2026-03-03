/**
 * PeriodSelector - Componente reutilizable para seleccionar períodos de tiempo
 * Usado en gráficos y análisis con tabs: diario, mensual y anual
 */

import '../../styles/shared/period-selector.css';

export type Period = 'daily' | 'monthly' | 'yearly';

interface PeriodOption {
  value: Period;
  label: string;
}

interface PeriodSelectorProps {
  selectedPeriod: Period;
  onPeriodChange: (period: Period) => void;
  options?: PeriodOption[];
}

const PeriodSelector = ({ selectedPeriod, onPeriodChange, options }: PeriodSelectorProps) => {
  const defaultPeriods: PeriodOption[] = [
    { value: 'daily', label: 'Diario' },
    { value: 'monthly', label: 'Mensual' },
    { value: 'yearly', label: 'Anual' },
  ];

  const periods = options || defaultPeriods;

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
