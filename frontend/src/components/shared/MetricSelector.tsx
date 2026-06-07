/**
 * MetricSelector - Componente reutilizable para seleccionar métricas en gráficos
 * Permite cambiar entre diferentes métricas: ingresos, pedidos, cantidad
 */

import '../../styles/shared/metric-selector.css';

export type Metric = 'ingresos' | 'pedidos' | 'items';

interface MetricSelectorProps {
  selectedMetric: Metric;
  onMetricChange: (metric: Metric) => void;
}

const MetricSelector = ({ selectedMetric, onMetricChange }: MetricSelectorProps) => {
  const metrics: { value: Metric; label: string }[] = [
    { value: 'ingresos', label: 'Ingresos' },
    { value: 'pedidos', label: 'Pedidos' },
    { value: 'items', label: 'Items' },
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
