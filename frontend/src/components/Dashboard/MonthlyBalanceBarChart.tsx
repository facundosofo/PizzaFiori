/**
 * MonthlyBalanceBarChart - Gráfico de barras agrupadas para balance mensual
 * 
 * Muestra:
 * - Últimos 12 meses dinámicos
 * - Dos barras por mes: Ventas (verde) y Gastos (rojo)
 * - La diferencia visual entre las barras representa la Ganancia/Pérdida
 * - Tooltip con: Ventas y Gastos
 * - Mes actual destacado
 * - Escala automática según máximo valor
 */

import { memo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { MonthlyBalanceData } from '../../services/dashboardService';
import { formatChartLabel } from '../../utils/formatters';

interface MonthlyBalanceBarChartProps {
  data: MonthlyBalanceData[];
  currentMonth: string;
  height?: number;
}

const MonthlyBalanceBarChart = memo(({ 
  data, 
  currentMonth,
  height = 350 
}: MonthlyBalanceBarChartProps) => {
  
  // Transformar datos para el gráfico
  const isDailyPeriod = data.length > 15 && /^\d{4}-\d{2}-\d{2}$/.test(data[0]?.month ?? '');
  const visibleData = isDailyPeriod ? data.slice(-15) : data;

  const chartData = visibleData.map((item, index) => {
    const profit = item.sales - item.expenses;
    return {
      month: item.month,
      displayMonth: formatChartLabel(item.month, index, visibleData.length),
      sales: item.sales,
      expenses: item.expenses,
      profit,
      isCurrentMonth: item.month === currentMonth,
    };
  });

  const formatCurrencyShort = (value: number) => {
    const absoluteValue = Math.abs(value);
    if (absoluteValue >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (absoluteValue >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  // Formatear eje Y
  const formatYAxis = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(0)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value}`;
  };

  // Calcular ticks del eje Y
  const calculateYTicks = (): number[] | undefined => {
    if (!chartData || chartData.length === 0) return undefined;

    const values = chartData.flatMap(item => [item.sales, item.expenses]);
    const maxValue = Math.max(...values, 0);

    if (maxValue === 0) {
      return [0, 50000, 100000, 150000, 200000];
    }

    const interval = (maxValue / 4) * 1.2;
    return [0, interval, interval * 2, interval * 3, interval * 4];
  };

  // Calcular dominio del eje Y
  const calculateYDomain = (): [number, number] | undefined => {
    const ticks = calculateYTicks();
    if (!ticks || ticks.length === 0) return undefined;
    return [0, ticks[ticks.length - 1]];
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const payloadMap = payload.reduce((acc: Record<string, number>, item: any) => {
      acc[item.name] = item.value;
      return acc;
    }, {});

    const profitValue = (payloadMap.Ventas ?? 0) - (payloadMap.Gastos ?? 0);
    const profitColor = profitValue >= 0 ? '#16a34a' : '#ef4444';

    return (
      <div
        style={{
          backgroundColor: 'var(--color-surface-2)',
          border: '1px solid var(--color-border-strong)',
          borderRadius: '6px',
          padding: '8px 12px',
          fontSize: '13px',
        }}
      >
        <div style={{ color: '#16a34a', marginBottom: '4px' }}>
          <strong>Ventas:</strong> {formatCurrencyShort(payloadMap.Ventas ?? 0)}
        </div>
        <div style={{ color: '#ef4444', marginBottom: '4px' }}>
          <strong>Gastos:</strong> {formatCurrencyShort(payloadMap.Gastos ?? 0)}
        </div>
        <div style={{ color: profitColor }}>
          <strong>Balance:</strong> {formatCurrencyShort(profitValue)}
        </div>
      </div>
    );
  };

  const BAR_GAP = 6;

  // Label para la barra de Ventas: se muestra solo cuando Ventas >= Gastos
  // El label se centra entre ambas barras usando la posición conocida de la barra adyacente
  const SalesBarLabel = (props: any) => {
    const { x, y, width, index } = props;
    const entry = chartData[index];
    if (!entry || (entry.sales === 0 && entry.expenses === 0)) return <g />;
    if (entry.sales < entry.expenses) return <g />; // la barra de gastos es más alta
    const centerX = x + width + BAR_GAP / 2; // punto medio entre ambas barras
    const fill = entry.profit >= 0 ? '#16a34a' : '#ef4444';
    return (
      <text x={centerX} y={y - 8} textAnchor="middle" fill={fill} fontSize={12} fontWeight={600}>
        {formatCurrencyShort(entry.profit)}
      </text>
    );
  };

  // Label para la barra de Gastos: se muestra solo cuando Gastos > Ventas
  const ExpensesBarLabel = (props: any) => {
    const { x, y, index } = props;
    const entry = chartData[index];
    if (!entry || (entry.sales === 0 && entry.expenses === 0)) return <g />;
    if (entry.expenses <= entry.sales) return <g />; // la barra de ventas es más alta o igual
    const centerX = x - BAR_GAP / 2; // punto medio entre ambas barras
    const fill = entry.profit >= 0 ? '#16a34a' : '#ef4444';
    return (
      <text x={centerX} y={y - 8} textAnchor="middle" fill={fill} fontSize={12} fontWeight={600}>
        {formatCurrencyShort(entry.profit)}
      </text>
    );
  };

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          margin={{ top: 32, right: 30, left: 0, bottom: 0 }}
          barGap={BAR_GAP}
          barCategoryGap="20%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-strong)" strokeOpacity={0.05} />
          <XAxis
            dataKey="displayMonth"
            stroke="var(--color-text-muted)"
            tick={{ fontSize: isDailyPeriod ? 10 : 12, fill: 'var(--color-text-muted)' }}
            interval={isDailyPeriod ? 0 : 'preserveStartEnd'}
            height={isDailyPeriod ? 80 : 60}
            angle={isDailyPeriod ? -45 : -35}
            textAnchor="end"
            tickMargin={10}
          />
          <YAxis
            stroke="var(--color-text-muted)"
            style={{ fontSize: '12px', fill: 'var(--color-text-muted)' }}
            domain={calculateYDomain()}
            ticks={calculateYTicks()}
            tickFormatter={formatYAxis}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: '13px', color: 'var(--color-text)' }} />
          <Bar dataKey="sales" name="Ventas" fill="#16a34a" radius={[4, 4, 0, 0]} label={<SalesBarLabel />} />
          <Bar dataKey="expenses" name="Gastos" fill="#ef4444" radius={[4, 4, 0, 0]} label={<ExpensesBarLabel />} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
});

MonthlyBalanceBarChart.displayName = 'MonthlyBalanceBarChart';

export default MonthlyBalanceBarChart;
