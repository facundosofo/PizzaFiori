/**
 * WeekdayChart - Gráfico de barras para promedio de ventas por día de semana
 * Muestra el promedio de ingresos o cantidad por día (Lunes a Domingo)
 * Ajustado al horario de negocio (16:00 a 06:00)
 */

import ChartWrapper from '../shared/ChartWrapper';
import type { WeekdayRevenue } from '../../services/dashboardService';

export type WeekdayMetric = 'ingresos' | 'pedidos' | 'items';

interface WeekdayChartProps {
  data: WeekdayRevenue[];
  selectedMetric: WeekdayMetric;
  height?: number;
}

const WeekdayChart = ({ 
  data, 
  selectedMetric,
  height = 300 
}: WeekdayChartProps) => {

  // Formatear valores según métrica seleccionada
  const formatTooltip = (value: number): string => {
    if (selectedMetric === 'ingresos') {
      return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    }
    // Para pedidos e items, mostrar con 1 decimal
    return value.toFixed(1);
  };

  // Formatear eje Y según métrica
  const formatYAxis = (value: number): string => {
    if (selectedMetric === 'ingresos') {
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      if (value >= 1000) {
        return `$${(value / 1000).toFixed(0)}K`;
      }
      return `$${value.toFixed(0)}`;
    }
    // Para pedidos e items - permitir decimales
    return value.toFixed(0);
  };

  // Calcular ticks del eje Y en múltiplos de 5 (exactamente 5 valores) para pedidos e items
  const calculateYTicks = (): number[] | undefined => {
    if (selectedMetric === 'ingresos') return undefined;

    const currentData = getChartData();
    if (!currentData || currentData.length === 0) return undefined;

    const seriesConfig = getSeriesConfig();
    const values = currentData.map(item => (item as any)[seriesConfig.key] || 0);
    const maxValue = Math.max(...values);

    if (maxValue === 0) return [0, 5, 10, 15, 20];

    // Calcular intervalo tentativo para 5 ticks (4 intervalos)
    const rawInterval = maxValue / 4;
    
    // Redondear al múltiplo de 5 más cercano hacia arriba
    const interval = Math.ceil(rawInterval / 5) * 5;

    // Generar exactamente 5 ticks
    return [0, interval, interval * 2, interval * 3, interval * 4];
  };

  // Calcular dominio del eje Y
  const calculateYDomain = (): [number, number] | undefined => {
    if (selectedMetric === 'ingresos') return undefined;

    const ticks = calculateYTicks();
    if (!ticks || ticks.length === 0) return undefined;

    // El dominio debe ir desde 0 hasta el último tick
    return [0, ticks[ticks.length - 1]];
  };

  // Preparar datos para el chart
  const getChartData = () => {
    return data.map((item) => ({
      diaSemana: item.dia_semana,
      promedioIngresos: item.promedio_ingresos,
      promedioPedidos: item.promedio_pedidos,
      promedioCantidad: item.promedio_cantidad,
    }));
  };

  // Obtener configuración de la serie según métrica
  const getSeriesConfig = () => {
    if (selectedMetric === 'ingresos') {
      return {
        key: 'promedioIngresos',
        name: 'Promedio de Ingresos',
        color: '#22c55e',
      };
    }
    if (selectedMetric === 'pedidos') {
      return {
        key: 'promedioPedidos',
        name: 'Promedio de Pedidos',
        color: '#22c55e',
      };
    }
    return {
      key: 'promedioCantidad',
      name: 'Promedio de Items Vendidos',
      color: '#22c55e',
    };
  };

  return (
    <div className="chart-container">
      <ChartWrapper
        type="bar"
        data={getChartData()}
        xAxisKey="diaSemana"
        series={[
          {
            ...getSeriesConfig(),
            labelColor: '#f7f7f7',
          },
        ]}
        height={height}
        showGrid={true}
        showTooltip={true}
        tooltipFormatter={formatTooltip}
        yAxisFormatter={formatYAxis}
        yAxisTicks={calculateYTicks()}
        yAxisDomain={calculateYDomain()}
        allowDecimals={selectedMetric === 'ingresos'}
        gridOpacity={0.05}
      />
    </div>
  );
};

export default WeekdayChart;
