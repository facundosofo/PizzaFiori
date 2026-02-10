/**
 * WeekdayMetricSelector - Selector de métrica para gráfico de weekday
 * 
 * Soporta 3 métricas:
 * - Ingresos: Promedio de revenue por día
 * - Pedidos: Promedio de órdenes por día
 * - Items: Promedio de items vendidos por día
 */

import '../../styles/shared/metric-selector.css';

export type WeekdayMetric = 'ingresos' | 'pedidos' | 'items';

interface WeekdayMetricSelectorProps {
  selectedMetric: WeekdayMetric;
  onMetricChange: (metric: WeekdayMetric) => void;
}

const WeekdayMetricSelector = ({ selectedMetric, onMetricChange }: WeekdayMetricSelectorProps) => {
  return (
    <div className="metric-selector">
      <button
        className={`metric-tab ${selectedMetric === 'ingresos' ? 'active' : ''}`}
        onClick={() => onMetricChange('ingresos')}
      >
        Ingresos
      </button>
      <button
        className={`metric-tab ${selectedMetric === 'pedidos' ? 'active' : ''}`}
        onClick={() => onMetricChange('pedidos')}
      >
        Pedidos
      </button>
      <button
        className={`metric-tab ${selectedMetric === 'items' ? 'active' : ''}`}
        onClick={() => onMetricChange('items')}
      >
        Items
      </button>
    </div>
  );
};

export default WeekdayMetricSelector;
