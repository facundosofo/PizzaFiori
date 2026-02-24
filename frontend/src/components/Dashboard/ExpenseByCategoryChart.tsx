/**
 * ExpenseByCategoryChart - Grafico de torta para gastos por categoria
 */

import { memo, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { ExpenseByCategory } from '../../services/dashboardService';

interface ExpenseByCategoryChartProps {
  data: ExpenseByCategory[];
  height?: number;
}

const ExpenseByCategoryChart = memo(({ data, height = 300 }: ExpenseByCategoryChartProps) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  if (!data || data.length === 0) {
    return <div className="chart-container">No hay datos disponibles</div>;
  }

  const toggleCategory = (categoria: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoria)) {
        newSet.delete(categoria);
      } else {
        newSet.add(categoria);
      }
      return newSet;
    });
  };

  const COLORS = [
    '#ef4444',
    '#f59e0b',
    '#22c55e',
    '#3b82f6',
    '#8b5cf6',
    '#ec4899',
    '#06b6d4',
    '#14b8a6',
  ];

  const total = data.reduce((sum, item) => sum + item.gastos, 0);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const entry = payload[0];
    const percentage = total === 0 ? '0.0' : ((entry.value / total) * 100).toFixed(1);
    const categoryIndex = data.findIndex(item => item.categoria === entry.name);
    const color = COLORS[categoryIndex % COLORS.length];

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
        <div style={{ color: color, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
          <span
            style={{
              width: '12px',
              height: '12px',
              backgroundColor: color,
              borderRadius: '2px',
              display: 'inline-block',
            }}
          />
          <strong>{entry.name}</strong>
        </div>
        <div style={{ color: color, marginLeft: '18px' }}>
          {formatCurrency(entry.value)} ({percentage}%)
        </div>
      </div>
    );
  };

  return (
    <div className="chart-container">
      <div style={{ marginBottom: '20px' }}>
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ payload }) => {
                if (!payload) return '';
                const { categoria, gastos } = payload as ExpenseByCategory;
                const percentage = total === 0 ? 0 : ((gastos / total) * 100);

                if (percentage < 3) return '';

                return `${categoria} (${percentage.toFixed(1)}%)`;
              }}
              outerRadius={90}
              fill="#8884d8"
              dataKey="gastos"
              nameKey="categoria"
              style={{ fontWeight: 700, fontSize: '12px' }}
              animationBegin={0}
              animationDuration={800}
              animationEasing="ease-out"
            >
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                  stroke="var(--color-border-strong)"
                  strokeWidth={2}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div style={{ marginTop: '20px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-strong)' }}>
              <th style={{ padding: '10px 8px', textAlign: 'left', color: 'var(--color-text-muted)', fontWeight: 500 }}>Categoría</th>
              <th style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text-muted)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>Gastos</th>
              <th style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text-muted)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>Porcentaje</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              const percentage = total === 0 ? '0.0' : ((item.gastos / total) * 100).toFixed(1);
              const hasSubcategories = item.subcategorias && item.subcategorias.length > 0;
              const isExpanded = expandedCategories.has(item.categoria);
              
              return (
                <>
                  <tr key={item.categoria} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '10px 8px', color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {hasSubcategories ? (
                        <button
                          onClick={() => toggleCategory(item.categoria)}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '0',
                            display: 'flex',
                            alignItems: 'center',
                            color: 'var(--color-text-muted)',
                            fontSize: '12px',
                            transition: 'transform 0.2s',
                            transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                          }}
                          aria-label={isExpanded ? 'Colapsar' : 'Expandir'}
                        >
                          ▶
                        </button>
                      ) : (
                        <span style={{ width: '12px' }} />
                      )}
                      <span style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: COLORS[index % COLORS.length] }} />
                      {item.categoria}
                    </td>
                    <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
                      {formatCurrency(item.gastos)}
                    </td>
                    <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                      {percentage}%
                    </td>
                  </tr>
                  {hasSubcategories && isExpanded && item.subcategorias!.map((subitem) => {
                    const subPercentage = total === 0 ? '0.0' : ((subitem.gastos / total) * 100).toFixed(1);
                    return (
                      <tr 
                        key={`${item.categoria}-${subitem.categoria}`}
                        style={{ 
                          borderBottom: '1px solid var(--color-border)',
                          backgroundColor: 'var(--color-surface-1)',
                        }}
                      >
                        <td style={{ 
                          padding: '8px 8px 8px 44px', 
                          color: 'var(--color-text-muted)', 
                          fontSize: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}>
                          <span style={{ color: 'var(--color-text-muted)' }}>└</span>
                          {subitem.categoria}
                        </td>
                        <td style={{ 
                          padding: '8px 8px', 
                          textAlign: 'right', 
                          color: 'var(--color-text-muted)', 
                          fontSize: '12px',
                          fontVariantNumeric: 'tabular-nums',
                        }}>
                          {formatCurrency(subitem.gastos)}
                        </td>
                        <td style={{ 
                          padding: '8px 8px', 
                          textAlign: 'right', 
                          color: 'var(--color-text-muted)', 
                          fontSize: '12px',
                          fontVariantNumeric: 'tabular-nums',
                        }}>
                          {subPercentage}%
                        </td>
                      </tr>
                    );
                  })}
                </>
              );
            })}
          </tbody>
          <tfoot>
            <tr style={{ borderTop: '1px solid var(--color-border-strong)' }}>
              <td style={{ padding: '10px 8px', color: 'var(--color-text)', fontWeight: 600 }}>Total</td>
              <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                {formatCurrency(total)}
              </td>
              <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                100%
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
});

ExpenseByCategoryChart.displayName = 'ExpenseByCategoryChart';

export default ExpenseByCategoryChart;
