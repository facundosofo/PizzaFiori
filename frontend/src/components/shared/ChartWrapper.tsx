/**
 * ChartWrapper - Componente genérico reutilizable para gráficos con Recharts
 * 
 * Soporta diferentes tipos de gráficos (line, bar, area) con configuración flexible
 * Diseñado para ser reutilizable en todo el sistema
 */

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export type ChartType = 'line' | 'bar' | 'area';

export interface DataSeries {
  key: string;
  name: string;
  color: string;
  type?: ChartType; // Permite mixed charts (line + bar)
}

export interface ChartWrapperProps {
  type: ChartType;
  data: any[];
  xAxisKey: string;
  series: DataSeries[];
  height?: number;
  xAxisLabel?: string;
  yAxisLabel?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  tooltipFormatter?: (value: any) => string;
  gridOpacity?: number;
  curved?: boolean; // Para line/area charts
}

const ChartWrapper = ({
  type,
  data,
  xAxisKey,
  series,
  height = 300,
  xAxisLabel,
  yAxisLabel,
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  tooltipFormatter,
  gridOpacity = 0.1,
  curved = true,
}: ChartWrapperProps) => {
  // Tooltip personalizado con estilos dark mode
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div
        style={{
          backgroundColor: '#1a1a1a',
          border: '1px solid rgba(255, 255, 255, 0.15)',
          borderRadius: '6px',
          padding: '8px 12px',
          fontSize: '13px',
        }}
      >
        {payload.map((entry: any, index: number) => (
          <div key={index} style={{ color: entry.color, marginBottom: index < payload.length - 1 ? '4px' : 0 }}>
            <strong>{entry.name}:</strong>{' '}
            {tooltipFormatter ? tooltipFormatter(entry.value) : entry.value}
          </div>
        ))}
      </div>
    );
  };

  // Props comunes para todos los gráficos
  const commonProps = {
    data,
    margin: { top: 10, right: 30, left: 0, bottom: 0 },
  };

  const commonAxisProps = {
    stroke: '#888888',
    style: { fontSize: '12px', fill: '#e8e8e8' },
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={`rgba(255, 255, 255, ${gridOpacity})`} />}
            <XAxis dataKey={xAxisKey} {...commonAxisProps} label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom' } : undefined} />
            <YAxis {...commonAxisProps} label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined} />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend wrapperStyle={{ fontSize: '13px', color: '#e8e8e8' }} />}
            {series.map((s) => (
              <Line
                key={s.key}
                type={curved ? 'monotone' : 'linear'}
                dataKey={s.key}
                name={s.name}
                stroke={s.color}
                strokeWidth={2}
                dot={{ fill: s.color, r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={`rgba(255, 255, 255, ${gridOpacity})`} />}
            <XAxis dataKey={xAxisKey} {...commonAxisProps} label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom' } : undefined} />
            <YAxis {...commonAxisProps} label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined} />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend wrapperStyle={{ fontSize: '13px', color: '#e8e8e8' }} />}
            {series.map((s) => (
              <Bar
                key={s.key}
                dataKey={s.key}
                name={s.name}
                fill={s.color}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={`rgba(255, 255, 255, ${gridOpacity})`} />}
            <XAxis dataKey={xAxisKey} {...commonAxisProps} label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom' } : undefined} />
            <YAxis {...commonAxisProps} label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined} />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend wrapperStyle={{ fontSize: '13px', color: '#e8e8e8' }} />}
            {series.map((s) => (
              <Area
                key={s.key}
                type={curved ? 'monotone' : 'linear'}
                dataKey={s.key}
                name={s.name}
                stroke={s.color}
                fill={s.color}
                fillOpacity={0.2}
                strokeWidth={2}
              />
            ))}
          </AreaChart>
        );

      default:
        return null;
    }
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      {renderChart()}
    </ResponsiveContainer>
  );
};

export default ChartWrapper;
