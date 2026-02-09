/**
 * DashboardOverview - Pantalla principal de reportes y analíticas
 * 
 * Vista desktop-first sin sidebar que muestra:
 * - Gráfico dominante de ventas diarias (últimos 30 días)
 * - Gráfico de ventas por franja horaria
 * - Tabla de ranking de prodcutos
 * 
 * Diseño centrado respetando guía UX (GUIA_UX_COLORES.md)
 */

import { useEffect, useState } from 'react';
import {
  getDashboardData,
  getSalesByCategory,
  getTopProducts,
  type DashboardData,
  type ProductSort,
} from '../services/dashboardService';
import RevenueChart from '../components/Dashboard/RevenueChart';
import SalesByCategoryChart from '../components/Dashboard/SalesByCategoryChart';
import TopProductsTable from '../components/Dashboard/TopProductsTable';
import ErrorAlert from '../components/shared/ErrorAlert';
import PeriodSelector, { type Period } from '../components/shared/PeriodSelector';
import MetricSelector, { type Metric } from '../components/shared/MetricSelector';
import CategorySelector from '../components/shared/CategorySelector';
import '../styles/dashboard.css';
import '../styles/shared/page-header.css';

const DashboardOverview = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [revenuePeriod, setRevenuePeriod] = useState<Period>('monthly');
  const [revenueMetric, setRevenueMetric] = useState<Metric>('ingresos');
  const [salesByCategoryPeriod, setSalesByCategoryPeriod] = useState<Period>('monthly');
  const [topProductsPeriod, setTopProductsPeriod] = useState<Period>('monthly');
  const [topProductsSort, setTopProductsSort] = useState<ProductSort>('top');
  const [topProductsCategory, setTopProductsCategory] = useState<string>('');

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
        
        // Calcular categorías disponibles una sola vez
        const categories = [...new Set(dashboardData.topProducts.map(p => p.categoria))].sort();
        setAvailableCategories(categories);
        
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

  useEffect(() => {
    const fetchSalesByCategory = async () => {
      try {
        console.log('[Dashboard] Fetching sales by category for period:', salesByCategoryPeriod);
        const salesByCategory = await getSalesByCategory(8, salesByCategoryPeriod);
        console.log('[Dashboard] Sales by category received:', salesByCategory);
        setData((prev) => (prev ? { ...prev, salesByCategory } : prev));
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar ventas por categoria';
        console.error('[Dashboard] Error ventas por categoria:', err);
        setError(`Error al cargar ventas por categoria: ${errorMessage}`);
      }
    };

    if (data) {
      fetchSalesByCategory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [salesByCategoryPeriod]);

  useEffect(() => {
    const fetchTopProducts = async () => {
      try {
        console.log('[Dashboard] Fetching top products for period:', topProductsPeriod, 'sort:', topProductsSort, 'category:', topProductsCategory);
        const topProducts = await getTopProducts(10, topProductsPeriod, topProductsSort, topProductsCategory || undefined);
        console.log('[Dashboard] Top products received:', topProducts);
        setData((prev) => (prev ? { ...prev, topProducts } : prev));
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar productos mas vendidos';
        console.error('[Dashboard] Error productos mas vendidos:', err);
        setError(`Error al cargar productos mas vendidos: ${errorMessage}`);
      }
    };

    if (data) {
      fetchTopProducts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topProductsPeriod, topProductsSort, topProductsCategory]);

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
              <div className="section-header">
                <h2 className="chart-title">Ventas por período</h2>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <MetricSelector 
                    selectedMetric={revenueMetric} 
                    onMetricChange={setRevenueMetric} 
                  />
                  <PeriodSelector 
                    selectedPeriod={revenuePeriod} 
                    onPeriodChange={setRevenuePeriod} 
                  />
                </div>
              </div>
              <RevenueChart 
                dailyData={data.dailyRevenue}
                weeklyData={data.weeklyRevenue}
                monthlyData={data.monthlyRevenue}
                yearlyData={data.yearlyRevenue}
                selectedPeriod={revenuePeriod}
                selectedMetric={revenueMetric}
                height={350} 
              />
            </div>

            <div className="chart-section chart-secondary">
              <div className="section-header">
                <h2 className="chart-title">Ventas por categoria</h2>
                <PeriodSelector
                  selectedPeriod={salesByCategoryPeriod}
                  onPeriodChange={setSalesByCategoryPeriod}
                />
              </div>
              <SalesByCategoryChart data={data.salesByCategory} height={300} />
            </div>
          </div>

          {/* Tabla de ranking de productos */}
          <div className="table-section">
            <div className="section-header">
              <h2 className="section-title">Ranking de productos</h2>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                {/* Selector de ordenamiento */}
                <div style={{ display: 'flex', gap: '4px', backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: '4px', borderRadius: '8px' }}>
                  <button
                    onClick={() => setTopProductsSort('top')}
                    style={{
                      padding: '8px 16px',
                      background: topProductsSort === 'top' ? '#22c55e' : 'transparent',
                      color: topProductsSort === 'top' ? '#ffffff' : '#888888',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: topProductsSort === 'top' ? '600' : '500',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    Más vendidos
                  </button>
                  <button
                    onClick={() => setTopProductsSort('bottom')}
                    style={{
                      padding: '8px 16px',
                      background: topProductsSort === 'bottom' ? '#22c55e' : 'transparent',
                      color: topProductsSort === 'bottom' ? '#ffffff' : '#888888',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: topProductsSort === 'bottom' ? '600' : '500',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    Menos vendidos
                  </button>
                </div>

                {/* Selector de categoría */}
                <CategorySelector
                  categories={availableCategories}
                  selectedCategory={topProductsCategory}
                  onCategoryChange={setTopProductsCategory}
                />

                <PeriodSelector
                  selectedPeriod={topProductsPeriod}
                  onPeriodChange={setTopProductsPeriod}
                />
              </div>
            </div>
            <TopProductsTable 
              products={data.topProducts}
            />
          </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
