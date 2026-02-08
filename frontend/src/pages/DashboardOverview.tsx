/**
 * DashboardOverview - Pantalla principal de reportes y analíticas
 * 
 * Vista desktop-first sin sidebar que muestra:
 * - Gráfico dominante de ventas diarias (últimos 30 días)
 * - Gráfico de ventas por franja horaria
 * - Tabla de productos más vendidos
 * 
 * Diseño centrado respetando guía UX (GUIA_UX_COLORES.md)
 */

import { useEffect, useState } from 'react';
import { getDashboardData, type DashboardData } from '../services/dashboardService';
import RevenueChart from '../components/Dashboard/RevenueChart';
import MonthlyChart from '../components/Dashboard/MonthlyChart';
import TopProductsTable from '../components/Dashboard/TopProductsTable';
import ErrorAlert from '../components/shared/ErrorAlert';
import '../styles/dashboard.css';
import '../styles/shared/page-header.css';

const DashboardOverview = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleCloseError = () => {
    setError(null);
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        console.log('[Dashboard] Iniciando carga de datos...');
        setError(null);
        setLoading(true);
        const dashboardData = await getDashboardData();
        console.log('[Dashboard] Datos recibidos:', dashboardData);
        setData(dashboardData);
        console.log('[Dashboard] Estado actualizado correctamente');
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar el dashboard';
        console.error('[Dashboard] Error:', err);
        setError(`Error al cargar dashboard: ${errorMessage}`);
      } finally {
        setLoading(false);
        console.log('[Dashboard] Loading finalizado');
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
        </div>
        <div className="dashboard-content">
          <div className="dashboard-skeleton">
            <div className="skeleton-chart"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
        </div>
        <ErrorAlert message={error} onClose={handleCloseError} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="dashboard-container">
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
        </div>
        <ErrorAlert message="No hay datos disponibles para mostrar" onClose={handleCloseError} />
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
      </div>

      <div className="dashboard-content">
          {/* Sección de métricas clave (opcional - puede agregarse luego) */}
          {/* <div className="metrics-row">
            <div className="metric-card">
              <span className="metric-label">Ingresos Totales</span>
              <span className="metric-value">${data.metrics.ingresoTotal.toLocaleString()}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Órdenes</span>
              <span className="metric-value">{data.metrics.ordenesTotal}</span>
            </div>
          </div> */}

          {/* Gráficos principales */}
          <div className="charts-grid">
            <div className="chart-section chart-main">
              <h2 className="chart-title">Ventas por período</h2>
              <RevenueChart 
                dailyData={data.dailyRevenue}
                weeklyData={data.weeklyRevenue}
                monthlyData={data.monthlyRevenue}
                yearlyData={data.yearlyRevenue}
                height={350} 
              />
            </div>

            <div className="chart-section chart-secondary">
              <h2 className="chart-title">Ventas mensuales</h2>
              <MonthlyChart data={data.monthlyRevenueByMonth} height={300} />
            </div>
          </div>

          {/* Tabla de productos más vendidos */}
          <div className="table-section">
            <h2 className="section-title">Productos más vendidos</h2>
            <TopProductsTable products={data.topProducts} />
          </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
