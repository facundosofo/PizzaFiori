/**
 * MonthlyChart - Gráfico de barras para ventas mensuales
 * Muestra distribución de ventas a lo largo de los 12 meses del año
 */

import ChartWrapper from '../shared/ChartWrapper';
import type { MonthlyRevenue } from '../../mocks/dashboard';

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

  return (
    <div className="chart-container">
      <ChartWrapper
        type="bar"
        data={data}
        xAxisKey="month"
        series={[
          {
            key: 'revenue',
            name: 'Ingresos',
            color: '#3b82f6', // Azul suave para diferenciación
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

export default MonthlyChart;
