/**
 * TotalExpensesKPICard - Card KPI para mostrar gastos totales con comparativa
 * 
 * Muestra:
 * - Total de gastos del período actual
 * - Comparativa contra período anterior (YoY o MoM)
 * - Variación porcentual e indicador de crecimiento/caída
 * - Para gastos: aumento es negativo (rojo), disminución es positivo (verde)
 */

import { memo, useEffect, useState } from 'react';
import { getTotalExpenses, type TotalExpensesKPI } from '../../services/dashboardService';
import ErrorAlert from '../shared/ErrorAlert';

interface TotalExpensesKPICardProps {
  days?: number;
  onDataLoaded?: (data: TotalExpensesKPI) => void;
}

const TotalExpensesKPICard = memo(({ 
  days = 30, 
  onDataLoaded 
}: TotalExpensesKPICardProps) => {
  const [data, setData] = useState<TotalExpensesKPI | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await getTotalExpenses(days);
        setData(result);
        onDataLoaded?.(result);
      } catch (err) {
        setError(`Error al cargar datos de gastos: ${err instanceof Error ? err.message : 'Error desconocido'}`);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [days, onDataLoaded]);

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
    // Para gastos: rojo es malo (aumento), verde es bueno (disminución)
    return value >= 0 ? 'var(--color-danger, #ef4444)' : 'var(--color-success, #16a34a)';
  };

  const calculateVariation = (current: number, previous: number | null): number | null => {
    if (previous === null || previous === 0) {
      return null;
    }
    return ((current - previous) / previous) * 100;
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

  if (error) {
    return <ErrorAlert message={error} onClose={() => setError(null)} />;
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
          Gastos Totales
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

  const variation = calculateVariation(data.current, data.previous);

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
        Gastos Totales
      </div>
      <div style={{ color: 'var(--color-text)', fontSize: '32px', fontWeight: 700, marginTop: '14px', marginBottom: '12px' }}>
        {formatCurrencyOrDash(data.current)}
      </div>
      <div style={{ color: getVariationColor(variation), fontSize: '13px', marginTop: '8px' }}>
        {formatVariation(variation, data.comparison_type)}
      </div>
    </div>
  );
});

TotalExpensesKPICard.displayName = 'TotalExpensesKPICard';

export default TotalExpensesKPICard;
