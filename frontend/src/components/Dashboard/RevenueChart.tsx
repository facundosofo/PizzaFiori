/**
 * RevenueChart - Gráfico de línea para ventas con selector de período y métrica
 * Componente reutilizable que muestra la evolución de ventas según período y métrica seleccionados
 * Soporta períodos: Daily, Weekly, Monthly, Yearly
 * Soporta métricas: Ingresos, Pedidos, Items
 */

import { memo } from 'react';
import ChartWrapper from '../shared/ChartWrapper';
import { type Period } from '../shared/PeriodSelector';
import { type Metric } from '../shared/MetricSelector';
import type { DailyRevenue, WeeklyRevenue, MonthlyRevenue, YearlyRevenue } from '../../services/dashboardService';
import { formatChartLabel } from '../../utils/formatters';

interface RevenueChartProps {
  dailyData: DailyRevenue[];
  weeklyData: WeeklyRevenue[];
  monthlyData: MonthlyRevenue[];
  yearlyData: YearlyRevenue[];
  selectedPeriod: Period;
  selectedMetric: Metric;
  height?: number;
  chartType?: 'area' | 'bar';
}

const RevenueChart = memo(({ 
  dailyData, 
  weeklyData,
  monthlyData, 
  yearlyData,
  selectedPeriod,
  selectedMetric,
  height = 350,
  chartType = 'area',
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

  // Calcular ticks del eje Y (exactamente 5 valores)
  const calculateYTicks = (): number[] | undefined => {
    const currentData = getData();
    if (!currentData || currentData.length === 0) return undefined;

    const seriesConfig = getSeriesConfig();
    const values = chartData.map((item: any) => Number(item[seriesConfig.key]) || 0);
    const maxValue = Math.max(...values);

    if (maxValue === 0) {
      if (selectedMetric === 'ingresos') {
        return [0, 1000, 2000, 3000, 4000];
      }
      return [0, 5, 10, 15, 20];
    }

    // Calcular intervalo: dividir máximo entre 4 (para generar 5 ticks)
    const interval = (maxValue / 4) * 1.2;

    // Generar exactamente 5 ticks
    return [0, interval, interval * 2, interval * 3, interval * 4];
  };

  // Calcular dominio del eje Y
  const calculateYDomain = (): [number, number] | undefined => {
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
      case 'daily': {
        // Crear un mapa de datos por fecha para búsqueda rápida
        const dataMap = new Map<string, DailyRevenue>();
        dailyData.forEach(item => {
          dataMap.set(item.fecha, item);
        });

        // Generar todos los días desde hace 30 días hasta hoy
        const today = new Date();
        const dates: Array<{ fecha: string; data: DailyRevenue | undefined }> = [];
        
        for (let i = 29; i >= 0; i--) {
          const date = new Date(today);
          date.setDate(date.getDate() - i);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          const fechaStr = `${year}-${month}-${day}`;
          const data = dataMap.get(fechaStr);
          dates.push({ fecha: fechaStr, data });
        }

        // Mapear a formato para el gráfico
        return dates.map((item) => {
          // Parsear fecha YYYY-MM-DD manualmente para evitar problemas de timezone
          const [, monthStr, dayStr] = item.fecha.split('-');
          const day = parseInt(dayStr, 10);
          const month = parseInt(monthStr, 10);
          
          if (item.data) {
            return {
              ...item.data,
              displayLabel: `${day}/${month}`,
            };
          } else {
            // Día sin datos - mostrar 0s
            return {
              fecha: item.fecha,
              ingresos: 0,
              pedidos: 0,
              cantidad: 0,
              displayLabel: `${day}/${month}`,
            };
          }
        });
      }
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
        return [];
    }
  };

  const chartData = getData();

  // Obtener configuración de la serie según métrica
  const getSeriesConfig = () => {
    if (selectedMetric === 'ingresos') {
      return {
        key: 'ingresos',
        name: 'Ingresos',
        color: '#22c55e',
      };
    }
    if (selectedMetric === 'pedidos') {
      return {
        key: 'pedidos',
        name: 'Pedidos',
        color: '#22c55e',
      };
    }
    return {
      key: 'cantidad',
      name: 'Items',
      color: '#22c55e',
    };
  };

  return (
    <div className="chart-container">
      <ChartWrapper
        type={chartType}
        data={chartData}
        xAxisKey="displayLabel"
        series={[
          {
            ...getSeriesConfig(),
            labelColor: 'var(--color-text)',
          },
        ]}
        height={height}
        showGrid={true}
        showTooltip={true}
        tooltipFormatter={formatTooltip}
        xAxisProps={{
          interval: selectedPeriod === 'daily' || selectedPeriod === 'weekly' ? 0 : 'preserveStartEnd',
          angle: selectedPeriod === 'daily' || selectedPeriod === 'weekly' ? -35 : -25,
          height: selectedPeriod === 'daily' || selectedPeriod === 'weekly' ? 80 : 60,
          textAnchor: 'end',
          tickMargin: 8,
          tickFormatter: formatChartLabel,
        }}
        yAxisFormatter={formatYAxis}
        yAxisTicks={calculateYTicks()}
        yAxisDomain={calculateYDomain()}
        allowDecimals={false}
        gridOpacity={0.05}
        curved={true}
      />
    </div>
  );
});

RevenueChart.displayName = 'RevenueChart';

export default RevenueChart;
