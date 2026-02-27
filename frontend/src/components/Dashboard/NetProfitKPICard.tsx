/**
 * NetProfitKPICard - Card KPI para mostrar resultado neto
 * 
 * Muestra:
 * - Resultado neto del período (ventas - gastos)
 * - Comparativa contra período anterior
 * - Variación porcentual
 * - Soporta valores negativos (pérdida)
 */

import { memo } from 'react';
import type { NetProfitKPI } from '../../services/dashboardService';

interface NetProfitKPICardProps {
  data: NetProfitKPI | null;
  loading?: boolean;
}

const NetProfitKPICard = memo(({ data, loading = false }: NetProfitKPICardProps) => {
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatCurrencyOrDash = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—';
    return formatCurrency(value);
  };

  const formatVariation = (value: number | null, comparisonType: 'YoY' | 'MoM' | null): string => {
    if (value === null) return 'Sin datos comparativos';
    const status = value >= 0 ? 'Aumento' : 'Bajo';
    const direction = value >= 0 ? '↑' : '↓';
    const label = comparisonType === 'YoY' ? 'año anterior' : comparisonType === 'MoM' ? 'mes anterior' : 'período anterior';
    return `${status} ${direction} ${Math.abs(value).toFixed(1)}% vs ${label}`;
  };

  const getVariationColor = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'var(--color-text-muted)';
    // Para ganancia: verde es bueno (aumento), rojo es malo (disminución)
    return value >= 0 ? 'var(--color-success, #16a34a)' : 'var(--color-danger, #ef4444)';
  };

  const calculateVariation = (current: number, previous: number | null): number | null => {
    if (previous === null || previous === 0) {
      return null;
    }
    return ((current - previous) / Math.abs(previous)) * 100;
  };

  if (loading) {
    return (
      <div
        style={{
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)',
          borderRadius: '12px',
          padding: '16px 18px',
          minHeight: '140px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
          Cargando...
        </div>
      </div>
    );
  }

  if (!data) {
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
        <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Resultado Neto
        </div>
        <div style={{ color: 'var(--color-text)', fontSize: '32px', fontWeight: 700, marginTop: '14px', marginBottom: '12px' }}>
          —
        </div>
        <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '8px' }}>
          Sin datos disponibles
        </div>
      </div>
    );
  }

  const variation = calculateVariation(data.net_profit, data.previous_net);
  const isNegative = data.net_profit < 0;

  return (
    <div
      style={{
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        borderRadius: '12px',
        padding: '16px 18px',
      }}
    >
      <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        Resultado Neto
      </div>
      <div 
        style={{ 
          color: isNegative ? 'var(--color-danger, #ef4444)' : 'var(--color-success, #16a34a)', 
          fontSize: '32px', 
          fontWeight: 700, 
          marginTop: '14px', 
          marginBottom: '12px' 
        }}
      >
        {formatCurrencyOrDash(data.net_profit)}
      </div>
      <div style={{ color: getVariationColor(variation), fontSize: '13px', marginTop: '8px' }}>
        {formatVariation(variation, data.comparison_type)}
      </div>
    </div>
  );
});

NetProfitKPICard.displayName = 'NetProfitKPICard';

export default NetProfitKPICard;
