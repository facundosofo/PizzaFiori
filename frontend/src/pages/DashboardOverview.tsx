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
  getWeekdayRevenue,
  getCategories,
  type DashboardData,
  type ProductSort,
  type WeekdayRevenue,
  type TimeFilter,
} from '../services/dashboardService';
import RevenueChart from '../components/Dashboard/RevenueChart';
import SalesByCategoryChart from '../components/Dashboard/SalesByCategoryChart';
import TopProductsTable from '../components/Dashboard/TopProductsTable';
import WeekdayChart from '../components/Dashboard/WeekdayChart';
import ErrorAlert from '../components/shared/ErrorAlert';
import PeriodSelector, { type Period } from '../components/shared/PeriodSelector';
import TimeFilterSelector, { type TimeFilterOption } from '../components/shared/TimeFilterSelector';
import MetricSelector, { type Metric } from '../components/shared/MetricSelector';
import WeekdayMetricSelector, { type WeekdayMetric } from '../components/shared/WeekdayMetricSelector';
import CategorySelector from '../components/shared/CategorySelector';
import * as Icons from '../components/shared/Icons';
import '../styles/dashboard.css';
import '../styles/shared/page-header.css';

const DashboardOverview = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [revenuePeriod, setRevenuePeriod] = useState<Period>('monthly');
  const [revenueMetric, setRevenueMetric] = useState<Metric>('ingresos');
  const [salesByCategoryTimeFilter, setSalesByCategoryTimeFilter] = useState<TimeFilter>('last_year');
  const [topProductsTimeFilter, setTopProductsTimeFilter] = useState<TimeFilter>('last_year');
  const [topProductsSort, setTopProductsSort] = useState<ProductSort>('top');
  const [topProductsCategory, setTopProductsCategory] = useState<string>('');
  
  // Estados para el gráfico de weekday revenue
  const [weekdayMetric, setWeekdayMetric] = useState<WeekdayMetric>('items');
  const [weekdayCategory, setWeekdayCategory] = useState<string>('');
  const [weekdayData, setWeekdayData] = useState<WeekdayRevenue[]>([]);
  const [weekdayLoading, setWeekdayLoading] = useState(false);
  const [weekdayTimeFilter, setWeekdayTimeFilter] = useState<TimeFilter>('last_year');

  const weekdayTimeFilterOptions: TimeFilterOption[] = [
    { value: 'last_month', label: 'Último mes', description: 'Últimos 30 días' },
    { value: 'last_year', label: 'Último año', description: 'Últimos 12 meses' },
    { value: 'all_time', label: 'Histórico', description: 'Todos los datos' },
  ];

  const handleCloseError = () => {
    setError(null);
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        console.log('[Dashboard] Iniciando carga de datos...');
        setError(null);
        setLoading(true);
        
        // Cargar datos del dashboard y categorías en paralelo
        const [dashboardData, categoriesData] = await Promise.all([
          getDashboardData(),
          getCategories(),
        ]);
        
        console.log('[Dashboard] Datos recibidos:', dashboardData);
        console.log('[Dashboard] Categorías recibidas:', categoriesData);
        setData(dashboardData);
        
        // Usar las categorías del endpoint de categorías
        const categories = categoriesData.map(c => c.nombre).sort();
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
        console.log('[Dashboard] Fetching sales by category for time filter:', salesByCategoryTimeFilter);
        const salesByCategory = await getSalesByCategory(8, salesByCategoryTimeFilter);
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
  }, [salesByCategoryTimeFilter]);

  useEffect(() => {
    const fetchTopProducts = async () => {
      try {
        console.log('[Dashboard] Fetching top products for time filter:', topProductsTimeFilter, 'sort:', topProductsSort, 'category:', topProductsCategory);
        const topProducts = await getTopProducts(5, topProductsTimeFilter, topProductsSort, topProductsCategory || undefined);
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
  }, [topProductsTimeFilter, topProductsSort, topProductsCategory]);

  useEffect(() => {
    const fetchWeekdayRevenue = async () => {
      try {
        console.log('[Dashboard] Fetching weekday revenue for category:', weekdayCategory);
        setWeekdayLoading(true);
        const weekdayRevenue = await getWeekdayRevenue(weekdayCategory || undefined, weekdayTimeFilter);
        console.log('[Dashboard] Weekday revenue received:', weekdayRevenue);
        setWeekdayData(weekdayRevenue);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar promedio por día de semana';
        console.error('[Dashboard] Error weekday revenue:', err);
        setError(`Error al cargar promedio por día de semana: ${errorMessage}`);
      } finally {
        setWeekdayLoading(false);
      }
    };

    fetchWeekdayRevenue();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weekdayCategory, weekdayTimeFilter]);

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
        <div className="dashboard-header-info">
          <div className="info-tooltip">
            <Icons.InfoIcon className="info-icon" />
            <div className="tooltip-content">
              ¿Por qué algunas ventas después de medianoche aparecen en el día anterior?
              <br />
              El sistema agrupa las ventas según el horario de trabajo del local (16:00 a 06:00).
              <br />
              Las ventas entre 00:00 y 05:59 se asignan al día anterior.
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
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
                monthlyData={data.monthlyRevenue}
                yearlyData={data.yearlyRevenue}
                selectedPeriod={revenuePeriod}
                selectedMetric={revenueMetric}
                height={350} 
              />
            </div>

            <div className="chart-section chart-secondary chart-span-rows chart-span-rows">
              <div className="section-header">
                <h2 className="chart-title">Ventas por categoria</h2>
                <TimeFilterSelector
                  value={salesByCategoryTimeFilter}
                  onChange={setSalesByCategoryTimeFilter}
                />
              </div>
              <SalesByCategoryChart data={data.salesByCategory} height={300} />
            </div>

            {/* Nuevo: Promedio de Ventas por Día de Semana */}
            <div className="chart-section chart-main">
              <div className="section-header">
                <h2 className="chart-title">Promedio de Ventas por Día de Semana</h2>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <WeekdayMetricSelector 
                    selectedMetric={weekdayMetric} 
                    onMetricChange={setWeekdayMetric} 
                  />
                  <CategorySelector
                    categories={availableCategories}
                    selectedCategory={weekdayCategory}
                    onCategoryChange={setWeekdayCategory}
                  />
                  <TimeFilterSelector
                    value={weekdayTimeFilter}
                    onChange={setWeekdayTimeFilter}
                    options={weekdayTimeFilterOptions}
                  />
                </div>
              </div>
              {weekdayLoading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888888' }}>
                  Cargando...
                </div>
              ) : (
                <WeekdayChart 
                  data={weekdayData}
                  selectedMetric={weekdayMetric}
                  height={300} 
                />
              )}
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

                <TimeFilterSelector
                  value={topProductsTimeFilter}
                  onChange={setTopProductsTimeFilter}
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
