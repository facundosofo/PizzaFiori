/**
 * RevenueChart - Gráfico de línea para ventas con selector de período y métrica
 * Componente reutilizable que muestra la evolución de ventas/cantidad según período y métrica seleccionados
 * Soporta períodos: Daily, Weekly, Monthly, Yearly
 * Soporta métricas: Ingresos, Cantidad
 */

import ChartWrapper from '../shared/ChartWrapper';
import { type Period } from '../shared/PeriodSelector';
import { type Metric } from '../shared/MetricSelector';
import type { DailyRevenue, WeeklyRevenue, MonthlyRevenue, YearlyRevenue } from '../../services/dashboardService';

interface RevenueChartProps {
  dailyData: DailyRevenue[];
  weeklyData: WeeklyRevenue[];
  monthlyData: MonthlyRevenue[];
  yearlyData: YearlyRevenue[];
  selectedPeriod: Period;
  selectedMetric: Metric;
  height?: number;
}

const RevenueChart = ({ 
  dailyData, 
  weeklyData, 
  monthlyData, 
  yearlyData,
  selectedPeriod,
  selectedMetric,
  height = 350 
}: RevenueChartProps) => {

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
    return value.toString();
  };

  // Formatear eje Y según métrica
  const formatYAxis = (value: number): string => {
    if (selectedMetric === 'ingresos') {
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      return `$${(value / 1000).toFixed(0)}K`;
    }
    // Para cantidad - siempre enteros
    if (value >= 1000) {
      return `${Math.round(value / 1000)}K`;
    }
    return Math.round(value).toString();
  };

  // Calcular ticks del eje Y en múltiplos de 5 (exactamente 5 valores)
  const calculateYTicks = (): number[] | undefined => {
    if (selectedMetric !== 'cantidad') return undefined;

    const currentData = getData();
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
    if (selectedMetric !== 'cantidad') return undefined;

    const ticks = calculateYTicks();
    if (!ticks || ticks.length === 0) return undefined;

    // El dominio debe ir desde 0 hasta el último tick
    return [0, ticks[ticks.length - 1]];
  };

  // Obtener datos según período seleccionado
  const getData = () => {
    if (!dailyData || !weeklyData || !monthlyData || !yearlyData) {
      return [];
    }
    
    switch (selectedPeriod) {
      case 'daily':
        return dailyData.map((item) => {
          const date = new Date(item.fecha);
          const day = date.getDate();
          const month = date.getMonth() + 1;
          return {
            ...item,
            displayLabel: `${day}/${month}`,
          };
        });
      case 'weekly':
        return weeklyData.map((item) => ({
          ...item,
          displayLabel: item.semana,
        }));
      case 'monthly':
        return monthlyData.map((item) => ({
          ...item,
          displayLabel: item.mes,
        }));
      case 'yearly':
        return yearlyData.map((item) => ({
          ...item,
          displayLabel: item.año,
        }));
      default:
        return dailyData || [];
    }
  };

  // Obtener configuración de la serie según métrica
  const getSeriesConfig = () => {
    if (selectedMetric === 'ingresos') {
      return {
        key: 'ingresos',
        name: 'Ingresos',
        color: '#22c55e',
      };
    }
    return {
      key: 'cantidad',
      name: 'Cantidad de Items Vendidos',
      color: '#22c55e',
    };
  };

  return (
    <div className="chart-container">
      <ChartWrapper
        type="area"
        data={getData()}
        xAxisKey="displayLabel"
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
        curved={true}
      />
    </div>
  );
};

export default RevenueChart;
