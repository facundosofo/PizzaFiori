/**
 * ExpenseByMonthChart - Grafico de barras para gastos por mes
 */

import { memo } from 'react';
import ChartWrapper from '../shared/ChartWrapper';
import type { MonthlyExpense } from '../../services/dashboardService';

interface ExpenseByMonthChartProps {
  data: MonthlyExpense[];
  height?: number;
  chartType?: 'bar' | 'area';
}

const ExpenseByMonthChart = memo(({ data, height = 300, chartType = 'bar' }: ExpenseByMonthChartProps) => {
  if (!data || data.length === 0) {
    return <div className="chart-container">No hay datos disponibles</div>;
  }

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatYAxis = (value: number): string => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  return (
    <div className="chart-container">
      <ChartWrapper
        type={chartType}
        data={data.map((item) => ({
          ...item,
          displayLabel: item.mes,
        }))}
        xAxisKey="displayLabel"
        series={[
          {
            key: 'gastos',
            name: 'Gastos',
            color: '#ef4444',
            labelColor: 'var(--color-text)',
          },
        ]}
        height={height}
        showGrid={true}
        showTooltip={true}
        tooltipFormatter={formatCurrency}
        yAxisFormatter={formatYAxis}
        allowDecimals={false}
        gridOpacity={0.05}
      />
    </div>
  );
});

ExpenseByMonthChart.displayName = 'ExpenseByMonthChart';

export default ExpenseByMonthChart;
