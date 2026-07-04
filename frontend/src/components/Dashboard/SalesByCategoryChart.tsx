/**
 * SalesByCategoryChart - Grafico de torta para ventas por categoria
 */

import { memo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { SalesByCategory } from '../../services/dashboardService';

interface SalesByCategoryChartProps {
  data: SalesByCategory[];
  height?: number;
}

const SalesByCategoryChart = memo(({ data, height = 300 }: SalesByCategoryChartProps) => {
  if (!data || data.length === 0) {
    return <div className="chart-container">No hay datos disponibles</div>;
  }

  // Colores para el pie chart
  const COLORS = [
    '#22c55e', // Verde
    '#3b82f6', // Azul
    '#f59e0b', // Amber
    '#ef4444', // Rojo
    '#8b5cf6', // Púrpura
    '#ec4899', // Rosa
    '#06b6d4', // Cyan
    '#14b8a6', // Teal
  ];

  // Calcular total
  const total = data.reduce((sum, item) => sum + item.cantidad, 0);
  const totalProductos = data.reduce((sum, item) => sum + (item.productos_vendidos ?? 0), 0);
  const totalPorciones = data.reduce((sum, item) => sum + (item.porciones_vendidas ?? 0), 0);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const entry = payload[0];
    const percentage = ((entry.value / total) * 100).toFixed(1);
    
    // Obtener el índice de la categoría para usar el color correcto
    const categoryIndex = data.findIndex(item => item.categoria === entry.name);
    const color = COLORS[categoryIndex % COLORS.length];

    const categoryRow = data.find(item => item.categoria === entry.name);

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
          {categoryRow?.cantidad_display ?? entry.value} ({percentage}%)
        </div>
        {!!categoryRow && categoryRow.productos_vendidos != null && categoryRow.porciones_vendidas != null && (
          <div style={{ color: 'var(--color-text-muted)', marginLeft: '18px', marginTop: '4px' }}>
            {categoryRow.productos_vendidos} productos + {categoryRow.porciones_vendidas} porciones
          </div>
        )}
        <div style={{ color: 'var(--color-text-muted)', marginLeft: '18px', marginTop: '4px' }}>
          Cantidad agregada (productos y porciones)
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
                const { categoria, cantidad } = payload as SalesByCategory;
                const percentage = ((cantidad / total) * 100);
                
                // Ocultar etiquetas de categorías muy pequeñas para evitar amontonamiento
                if (percentage < 3) return '';
                
                return `${categoria} (${percentage.toFixed(1)}%)`;
              }}
              outerRadius={90}
              fill="#8884d8"
              dataKey="cantidad"
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

      {/* Tabla de detalles */}
      <div style={{ marginTop: '20px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-strong)' }}>
              <th style={{ padding: '10px 8px', textAlign: 'left', color: 'var(--color-text-muted)', fontWeight: 500 }}>Categoría</th>
              <th style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text-muted)', fontWeight: 500 }}>Cantidad</th>
              <th style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text-muted)', fontWeight: 500 }}>Porcentaje</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              const percentage = ((item.cantidad / total) * 100).toFixed(1);
              return (
                <tr key={item.categoria} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '10px 8px', color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: COLORS[index % COLORS.length] }} />
                    {item.categoria}
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text)', fontWeight: 500 }}>
                    {item.cantidad_display ?? item.cantidad}
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text-muted)' }}>
                    {percentage}%
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr style={{ borderTop: '1px solid var(--color-border-strong)' }}>
              <td style={{ padding: '10px 8px', color: 'var(--color-text)', fontWeight: 600 }}>Total</td>
              <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text)', fontWeight: 600 }}>
                {`${totalProductos} productos + ${totalPorciones} porciones`}
              </td>
              <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-text)', fontWeight: 600 }}>
                100%
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
});

SalesByCategoryChart.displayName = 'SalesByCategoryChart';

export default SalesByCategoryChart;
