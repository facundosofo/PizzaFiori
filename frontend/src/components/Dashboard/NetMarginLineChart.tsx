/**
 * NetMarginLineChart - Gráfico de área para evolución del margen neto mensual
 *
 * El área y la línea cambian de color en el cruce del 0%:
 *   - Verde (#16a34a) cuando el margen es positivo (ganancia)
 *   - Rojo  (#ef4444) cuando el margen es negativo (pérdida)
 *
 * Técnica: se calcula el offset (0-1) donde 0% cae dentro del dominio
 * y se usan dos linearGradient SVG (stroke + fill) con un stop exacto en ese punto.
 */

import { memo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from 'recharts';
import type { MonthlyBalanceData } from '../../services/dashboardService';

const COLOR_PROFIT = '#16a34a';
const COLOR_LOSS   = '#ef4444';

interface NetMarginLineChartProps {
  data: MonthlyBalanceData[];
  currentMonth: string;
  height?: number;
}

const NetMarginLineChart = memo(({
  data,
  currentMonth,
  height = 350,
}: NetMarginLineChartProps) => {

  const calculateMargin = (sales: number, expenses: number): number => {
    if (sales === 0) return 0;
    return ((sales - expenses) / sales) * 100;
  };

  const chartData = data.map((item) => ({
    month: item.month,
    margin: calculateMargin(item.sales, item.expenses),
    isCurrentMonth: item.month === currentMonth,
  }));

  // ── Dominio ──────────────────────────────────────────────────────────────
  const margins  = chartData.map((d) => d.margin);
  const rawMin   = Math.min(...margins);
  const rawMax   = Math.max(...margins);
  const pad      = Math.max((rawMax - rawMin) * 0.15, 5);
  const domainMin = Math.floor((rawMin - pad) / 10) * 10;
  const domainMax = Math.ceil((rawMax  + pad) / 10) * 10;

  // Offset [0-1] donde cae el cero dentro del dominio (svg: top=0, bottom=1)
  const zeroOffset = domainMax === domainMin
    ? 0.5
    : Math.max(0, Math.min(1, domainMax / (domainMax - domainMin)));

  const yTicks: number[] = [];
  const tickCount = 5;
  const step = (domainMax - domainMin) / tickCount;
  for (let i = 0; i <= tickCount; i++) {
    yTicks.push(Math.round(domainMin + step * i));
  }

  // ── Tooltip ───────────────────────────────────────────────────────────────
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const val: number = payload[0]?.value ?? 0;
    const color = val >= 0 ? COLOR_PROFIT : COLOR_LOSS;
    return (
      <div
        style={{
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border-strong)',
          borderRadius: '6px',
          padding: '8px 12px',
          fontSize: '13px',
        }}
      >
        <div style={{ color, fontWeight: 600 }}>
          Margen: {val.toFixed(1)}%
        </div>
        <div style={{ color: 'var(--color-text-muted)', fontSize: '11px', marginTop: 2 }}>
          {val >= 0 ? 'Ganancia' : 'Pérdida'}
        </div>
      </div>
    );
  };

  // ── Dot ───────────────────────────────────────────────────────────────────
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    const color = (payload?.margin ?? 0) >= 0 ? COLOR_PROFIT : COLOR_LOSS;
    if (payload?.isCurrentMonth) {
      return (
        <g>
          <circle cx={cx} cy={cy} r={5} fill={color} stroke="#fff" strokeWidth={2} />
          <circle cx={cx} cy={cy} r={9} fill="none" stroke={color} strokeWidth={1} opacity={0.4} />
        </g>
      );
    }
    return <circle cx={cx} cy={cy} r={3} fill={color} stroke="none" />;
  };

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
          <defs>
            {/* Gradiente para el trazo (stroke) */}
            <linearGradient id="strokeGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset={zeroOffset} stopColor={COLOR_PROFIT} />
              <stop offset={zeroOffset} stopColor={COLOR_LOSS} />
            </linearGradient>

            {/* Gradiente para el relleno superior (zona positiva) */}
            <linearGradient id="fillAbove" x1="0" y1="0" x2="0" y2="1">
              <stop offset={0}          stopColor={COLOR_PROFIT} stopOpacity={0.25} />
              <stop offset={zeroOffset} stopColor={COLOR_PROFIT} stopOpacity={0.05} />
              <stop offset={zeroOffset} stopColor={COLOR_LOSS}   stopOpacity={0.05} />
              <stop offset={1}          stopColor={COLOR_LOSS}   stopOpacity={0.20} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border-strong)"
            strokeOpacity={0.05}
          />
          <XAxis
            dataKey="month"
            stroke="var(--color-text-muted)"
            style={{ fontSize: '12px', fill: 'var(--color-text-muted)' }}
          />
          <YAxis
            stroke="var(--color-text-muted)"
            style={{ fontSize: '12px', fill: 'var(--color-text-muted)' }}
            domain={[domainMin, domainMax]}
            ticks={yTicks}
            tickFormatter={(v) => `${v}%`}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Línea de referencia en el cero */}
          <ReferenceLine
            y={0}
            stroke="var(--color-text-muted)"
            strokeDasharray="4 3"
            strokeOpacity={0.4}
          />

          <Area
            type="monotone"
            dataKey="margin"
            name="Margen Neto"
            stroke="url(#strokeGradient)"
            strokeWidth={2}
            fill="url(#fillAbove)"
            dot={<CustomDot />}
            activeDot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
});

NetMarginLineChart.displayName = 'NetMarginLineChart';

export default NetMarginLineChart;
