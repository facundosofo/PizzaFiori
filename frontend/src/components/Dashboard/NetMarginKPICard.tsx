/**
 * NetMarginKPICard - Card KPI para mostrar margen neto porcentual
 * 
 * Muestra:
 * - Margen neto del período ((ventas - gastos) / ventas * 100)
 * - Comparativa en puntos porcentuales (no variación relativa)
 * - Maneja correctamente sales = 0
 */

import { memo } from 'react';
import type { NetMarginKPI } from '../../services/dashboardService';

interface NetMarginKPICardProps {
  data: NetMarginKPI | null;
  loading?: boolean;
}

const NetMarginKPICard = memo(({ data, loading = false }: NetMarginKPICardProps) => {
  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  const formatPercentageOrDash = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—';
    return formatPercentage(value);
  };

  const formatMarginDifference = (current: number, previous: number | null, comparisonType: 'YoY' | 'MoM' | null): string => {
    if (previous === null) return 'Sin datos comparativos';
    
    // Diferencia en puntos porcentuales (no variación relativa)
    const diff = current - previous;
    const direction = diff >= 0 ? '↑' : '↓';
    const label = comparisonType === 'YoY' ? 'año anterior' : comparisonType === 'MoM' ? 'mes anterior' : 'período anterior';
    
    return `${direction} ${Math.abs(diff).toFixed(1)} p.p. vs ${label}`;
  };

  const getDifferenceColor = (current: number, previous: number | null): string => {
    if (previous === null) return 'var(--color-text-muted)';
    const diff = current - previous;
    // Para margen: aumento es bueno (verde), disminución es malo (rojo)
    return diff >= 0 ? 'var(--color-success, #16a34a)' : 'var(--color-danger, #ef4444)';
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
          Margen Neto
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

  const isNegativeMargin = data.margin < 0;

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
        Margen Neto
      </div>
      <div 
        style={{ 
          color: isNegativeMargin ? 'var(--color-danger, #ef4444)' : 'var(--color-text)', 
          fontSize: '32px', 
          fontWeight: 700, 
          marginTop: '14px', 
          marginBottom: '12px' 
        }}
      >
        {formatPercentageOrDash(data.margin)}
      </div>
      <div style={{ color: getDifferenceColor(data.margin, data.previous_margin), fontSize: '13px', marginTop: '8px' }}>
        {formatMarginDifference(data.margin, data.previous_margin, data.comparison_type)}
      </div>
    </div>
  );
});

NetMarginKPICard.displayName = 'NetMarginKPICard';

export default NetMarginKPICard;
