/**
 * TotalOrdersKPICard - Card KPI para mostrar pedidos del mes con ticket promedio
 *
 * Muestra:
 * - Total de pedidos del mes actual
 * - Variación porcentual vs mes anterior
 * - Ticket promedio (ingresos / pedidos)
 */

import { memo } from 'react';
import type { MonthlyRevenue } from '../../services/dashboardService';

interface TotalOrdersKPICardProps {
  monthlyRevenue: MonthlyRevenue[] | null;
}

const TotalOrdersKPICard = memo(({ monthlyRevenue }: TotalOrdersKPICardProps) => {
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const current =
    monthlyRevenue && monthlyRevenue.length > 0
      ? monthlyRevenue[monthlyRevenue.length - 1]
      : null;

  const previous =
    monthlyRevenue && monthlyRevenue.length > 1
      ? monthlyRevenue[monthlyRevenue.length - 2]
      : null;

  const variation =
    current && previous && previous.pedidos > 0
      ? ((current.pedidos - previous.pedidos) / previous.pedidos) * 100
      : null;

  const ticketPromedio =
    current && current.pedidos > 0 ? current.ingresos / current.pedidos : null;

  const getVariationColor = (value: number | null): string => {
    if (value === null) return 'var(--color-text-muted)';
    return value >= 0 ? 'var(--color-success, #16a34a)' : 'var(--color-danger, #ef4444)';
  };

  const formatVariation = (value: number | null): string => {
    if (value === null) return 'Sin datos comparativos';
    const direction = value >= 0 ? '↑' : '↓';
    return `${value >= 0 ? 'Aumento' : 'Bajo'} ${direction} ${Math.abs(value).toFixed(1)}% vs mes anterior`;
  };

  return (
    <div
      style={{
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        borderRadius: '12px',
        padding: '16px 18px',
        minHeight: '140px',
      }}
    >
      <div
        style={{
          color: 'var(--color-text-muted)',
          fontSize: '13px',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        Pedidos del mes
      </div>
      <div
        style={{
          color: 'var(--color-text)',
          fontSize: '32px',
          fontWeight: 700,
          marginTop: '14px',
          marginBottom: '12px',
        }}
      >
        {current ? current.pedidos.toLocaleString('es-AR') : '—'}
      </div>
      <div
        style={{
          color: getVariationColor(variation),
          fontSize: '13px',
          marginBottom: ticketPromedio !== null ? '4px' : undefined,
        }}
      >
        {formatVariation(variation)}
      </div>
      {ticketPromedio !== null && (
        <div style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
          Pedido promedio: {formatCurrency(ticketPromedio)}
        </div>
      )}
    </div>
  );
});

TotalOrdersKPICard.displayName = 'TotalOrdersKPICard';

export default TotalOrdersKPICard;
