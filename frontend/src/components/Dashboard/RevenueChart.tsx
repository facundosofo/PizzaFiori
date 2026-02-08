/**
 * RevenueChart - Gráfico de línea para ventas con selector de período
 * Componente reutilizable que muestra la evolución de ventas según período seleccionado
 * Soporta: Daily, Weekly, Monthly, Yearly
 */

import { useState } from 'react';
import ChartWrapper from '../shared/ChartWrapper';
import PeriodSelector, { type Period } from '../shared/PeriodSelector';
import type { DailyRevenue, WeeklyRevenue, MonthlyRevenue, YearlyRevenue } from '../../services/dashboardService';

interface RevenueChartProps {
  dailyData: DailyRevenue[];
  weeklyData: WeeklyRevenue[];
  monthlyData: MonthlyRevenue[];
  yearlyData: YearlyRevenue[];
  height?: number;
}

const RevenueChart = ({ 
  dailyData, 
  weeklyData, 
  monthlyData, 
  yearlyData, 
  height = 350 
}: RevenueChartProps) => {
  const [selectedPeriod, setSelectedPeriod] = useState<Period>('daily');

  // Formatear valores de dinero en tooltip
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Obtener datos según período seleccionado
  const getData = () => {
    if (!dailyData || !weeklyData || !monthlyData || !yearlyData) {
      return [];
    }
    
    switch (selectedPeriod) {
      case 'daily':
        return dailyData.map((item) => {
          const date = new Date(item.date);
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
          displayLabel: item.week,
        }));
      case 'monthly':
        return monthlyData.map((item) => ({
          ...item,
          displayLabel: item.month,
        }));
      case 'yearly':
        return yearlyData.map((item) => ({
          ...item,
          displayLabel: item.year,
          }));
      default:
        return dailyData || [];
    }
  };

  return (
    <div className="chart-container">
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'flex-end' }}>
        <PeriodSelector 
          selectedPeriod={selectedPeriod} 
          onPeriodChange={setSelectedPeriod} 
        />
      </div>
      <ChartWrapper
        type="line"
        data={getData()}
        xAxisKey="displayLabel"
        series={[
          {
            key: 'revenue',
            name: 'Ingresos',
            color: '#22c55e', // Verde suave (no neón)
          },
        ]}
        height={height}
        showGrid={true}
        showTooltip={true}
        tooltipFormatter={formatCurrency}
        gridOpacity={0.08}
        curved={true}
      />
    </div>
  );
};

export default RevenueChart;
