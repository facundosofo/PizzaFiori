/**
 * HourlyChart - Gráfico de barras para ventas por franja horaria
 * Muestra distribución de ventas a lo largo del día
 */

import ChartWrapper from '../shared/ChartWrapper';
import type { HourlyRevenue } from '../../mocks/dashboard';

interface HourlyChartProps {
  data: HourlyRevenue[];
  height?: number;
}

const HourlyChart = ({ data, height = 300 }: HourlyChartProps) => {
  // Formatear valores de dinero en tooltip
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="chart-container">
      <ChartWrapper
        type="bar"
        data={data}
        xAxisKey="hour"
        series={[
          {
            key: 'revenue',
            name: 'Ingresos',
            color: '#3b82f6', // Azul suave en lugar de verde para diferenciación
          },
        ]}
        height={height}
        showGrid={true}
        showTooltip={true}
        tooltipFormatter={formatCurrency}
        gridOpacity={0.08}
      />
    </div>
  );
};

export default HourlyChart;
