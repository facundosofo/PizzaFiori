/**
 * MonthlyChart - Gráfico de barras para ventas mensuales
 * Muestra distribución de ventas a lo largo de los 12 meses del año
 */

import ChartWrapper from '../shared/ChartWrapper';
import type { MonthlyRevenue } from '../../services/dashboardService';

interface MonthlyChartProps {
  data: MonthlyRevenue[];
  height?: number;
}

const MonthlyChart = ({ data, height = 300 }: MonthlyChartProps) => {
  // Validar datos
  if (!data || data.length === 0) {
    return <div className="chart-container">No hay datos disponibles</div>;
  }
  
  // Formatear valores de dinero en tooltip
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Formatear eje Y (en miles o millones)
  const formatYAxis = (value: number): string => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    return `$${(value / 1000).toFixed(0)}K`;
  };

  return (
    <div className="chart-container">
      <ChartWrapper
        type="bar"
        data={data}
        xAxisKey="mes"
        series={[
          {
            key: 'ingresos',
            name: 'Ingresos',
            color: '#3b82f6', // Azul suave para diferenciación
          },
        ]}
        height={height}
        showGrid={true}
        showTooltip={true}
        tooltipFormatter={formatCurrency}
        yAxisFormatter={formatYAxis}
        gridOpacity={0.08}
      />
    </div>
  );
};

export default MonthlyChart;
