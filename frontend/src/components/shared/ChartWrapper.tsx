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
  type XAxisProps,
} from 'recharts';

export type ChartType = 'line' | 'bar' | 'area';

export interface DataSeries {
  key: string;
  name: string;
  color: string;
  labelColor?: string; // Color separado para el texto/label (opcional)
  type?: ChartType; // Permite mixed charts (line + bar)
}

export interface ChartWrapperProps {
  type: ChartType;
  data: any[];
  xAxisKey: string;
  series: DataSeries[];
  height?: number | `${number}%`;
  xAxisLabel?: string;
  xAxisProps?: Partial<Omit<XAxisProps, 'dataKey'>>;
  yAxisLabel?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  tooltipFormatter?: (value: any) => string;
  yAxisFormatter?: (value: any) => string; // Formateador de valores eje Y
  yAxisDomain?: [number, number]; // [mínimo, máximo] del eje Y
  yAxisTicks?: number[]; // Valores específicos para el eje Y
  allowDecimals?: boolean; // Permitir decimales en eje Y
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
  xAxisProps,
  yAxisFormatter,
  yAxisDomain,
  yAxisTicks,
  allowDecimals = true,
  gridOpacity = 0.1,
  curved = true,
}: ChartWrapperProps) => {
  // Calcular dominio automático del eje Y si no se especifica
  const calculateYAxisDomain = (): [number, number] | undefined => {
    if (yAxisDomain) return yAxisDomain;
    
    if (!data || data.length === 0) return undefined;
    
    // Obtener todos los valores de las series
    const allValues: number[] = [];
    series.forEach(s => {
      data.forEach(item => {
        const value = item[s.key];
        if (typeof value === 'number') {
          allValues.push(value);
        }
      });
    });
    
    if (allValues.length === 0) return undefined;
    
    const max = Math.max(...allValues);
    const min = Math.min(...allValues);
    
    // Agregar 10% de padding arriba para que no toque el borde
    const padding = (max - min) * 0.1;
    return [Math.max(0, min - padding), max + padding];
  };

  const calculatedDomain = calculateYAxisDomain();

  // Mapa de series con sus colores de label
  const seriesLabelColorMap = series.reduce((acc, s) => {
    acc[s.name] = s.labelColor || s.color;
    return acc;
  }, {} as Record<string, string>);

  // Tooltip personalizado con estilos dark mode
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

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
        {payload.map((entry: any, index: number) => (
          <div key={index} style={{ color: seriesLabelColorMap[entry.name] || entry.color, marginBottom: index < payload.length - 1 ? '4px' : 0 }}>
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
    stroke: 'var(--color-text-muted)',
    style: { fontSize: '12px', fill: 'var(--color-text-muted)' },
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--color-border-strong)"
                strokeOpacity={gridOpacity}
              />
            )}
            <XAxis
              dataKey={xAxisKey}
              {...commonAxisProps}
              {...xAxisProps}
              label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom' } : undefined}
            />
            <YAxis 
              {...commonAxisProps} 
              label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined}
              domain={calculatedDomain}
              ticks={yAxisTicks}
              tickFormatter={yAxisFormatter}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend wrapperStyle={{ fontSize: '13px', color: 'var(--color-text)' }} />}
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
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--color-border-strong)"
                strokeOpacity={gridOpacity}
              />
            )}
            <XAxis
              dataKey={xAxisKey}
              {...commonAxisProps}
              {...xAxisProps}
              label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom' } : undefined}
            />
            <YAxis 
              {...commonAxisProps} 
              label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined}
              domain={calculatedDomain}
              ticks={yAxisTicks}
              tickFormatter={yAxisFormatter}
              allowDecimals={allowDecimals}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend wrapperStyle={{ fontSize: '13px', color: 'var(--color-text)' }} />}
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
            <defs>
              {series.map((s) => (
                <linearGradient key={`gradient-${s.key}`} id={`gradient-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={s.color} stopOpacity={0.4} />
                  <stop offset="50%" stopColor={s.color} stopOpacity={0.2} />
                  <stop offset="100%" stopColor={s.color} stopOpacity={0.05} />
                </linearGradient>
              ))}
              {series.map((s) => (
                <filter key={`glow-${s.key}`} id={`glow-${s.key}`} x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
                  <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              ))}
            </defs>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--color-border-strong)"
                strokeOpacity={gridOpacity}
              />
            )}
            <XAxis
              dataKey={xAxisKey}
              {...commonAxisProps}
              {...xAxisProps}
              label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom' } : undefined}
            />
            <YAxis 
              {...commonAxisProps} 
              label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft' } : undefined}
              domain={calculatedDomain}
              ticks={yAxisTicks}
              allowDecimals={allowDecimals}
              tickFormatter={yAxisFormatter}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend wrapperStyle={{ fontSize: '13px', color: 'var(--color-text)' }} />}
            {series.map((s) => (
              <Area
                key={s.key}
                type={curved ? 'monotone' : 'linear'}
                dataKey={s.key}
                name={s.name}
                stroke={s.color}
                fill={`url(#gradient-${s.key})`}
                strokeWidth={3}
                style={{ filter: `url(#glow-${s.key})` }}
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
