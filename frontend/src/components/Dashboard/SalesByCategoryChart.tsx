/**
 * SalesByCategoryChart - Grafico de torta para ventas por categoria
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { SalesByCategory } from '../../services/dashboardService';

interface SalesByCategoryChartProps {
  data: SalesByCategory[];
  height?: number;
}

const SalesByCategoryChart = ({ data, height = 300 }: SalesByCategoryChartProps) => {
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

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const entry = payload[0];
    const percentage = ((entry.value / total) * 100).toFixed(1);
    
    // Obtener el índice de la categoría para usar el color correcto
    const categoryIndex = data.findIndex(item => item.categoria === entry.name);
    const color = COLORS[categoryIndex % COLORS.length];

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
          {entry.value} ({percentage}%)
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
                  stroke="rgba(255, 255, 255, 0.3)"
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
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.15)' }}>
              <th style={{ padding: '10px 8px', textAlign: 'left', color: '#e8e8e8', fontWeight: 500 }}>Categoría</th>
              <th style={{ padding: '10px 8px', textAlign: 'right', color: '#e8e8e8', fontWeight: 500 }}>Cantidad</th>
              <th style={{ padding: '10px 8px', textAlign: 'right', color: '#e8e8e8', fontWeight: 500 }}>Porcentaje</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              const percentage = ((item.cantidad / total) * 100).toFixed(1);
              return (
                <tr key={item.categoria} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <td style={{ padding: '10px 8px', color: '#f5f5f5', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: COLORS[index % COLORS.length] }} />
                    {item.categoria}
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'right', color: '#f5f5f5', fontWeight: 500 }}>
                    {item.cantidad}
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'right', color: '#e8e8e8' }}>
                    {percentage}%
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr style={{ borderTop: '1px solid rgba(255, 255, 255, 0.15)' }}>
              <td style={{ padding: '10px 8px', color: '#ffffff', fontWeight: 600 }}>Total</td>
              <td style={{ padding: '10px 8px', textAlign: 'right', color: '#ffffff', fontWeight: 600 }}>
                {total}
              </td>
              <td style={{ padding: '10px 8px', textAlign: 'right', color: '#ffffff', fontWeight: 600 }}>
                100%
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};

export default SalesByCategoryChart;
