/**
 * PeriodSelector - Componente reutilizable para seleccionar períodos de tiempo
 * Usado en gráficos y análisis con tabs: Daily, Weekly, Monthly, Yearly
 */

import '../../styles/shared/period-selector.css';

export type Period = 'daily' | 'weekly' | 'monthly' | 'yearly';

interface PeriodSelectorProps {
  selectedPeriod: Period;
  onPeriodChange: (period: Period) => void;
}

const PeriodSelector = ({ selectedPeriod, onPeriodChange }: PeriodSelectorProps) => {
  const periods: { value: Period; label: string }[] = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'yearly', label: 'Yearly' },
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
