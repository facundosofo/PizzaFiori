/**
 * MetricSelector - Componente reutilizable para seleccionar métricas en gráficos
 * Permite cambiar entre diferentes métricas: ingresos, cantidad, etc.
 */

import '../../styles/shared/metric-selector.css';

export type Metric = 'ingresos' | 'cantidad';

interface MetricSelectorProps {
  selectedMetric: Metric;
  onMetricChange: (metric: Metric) => void;
}

const MetricSelector = ({ selectedMetric, onMetricChange }: MetricSelectorProps) => {
  const metrics: { value: Metric; label: string }[] = [
    { value: 'ingresos', label: 'Ingresos' },
    { value: 'cantidad', label: 'Cantidad' },
  ];

  return (
    <div className="metric-selector">
      {metrics.map((metric) => (
        <button
          key={metric.value}
          className={`metric-tab ${selectedMetric === metric.value ? 'active' : ''}`}
          onClick={() => onMetricChange(metric.value)}
        >
          {metric.label}
        </button>
      ))}
    </div>
  );
};

export default MetricSelector;
