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

import { useCallback, useEffect, useState } from 'react';
import {
  getDashboardData,
  getExpensesByPeriod,
  getExpensesByCategory,
  getSalesByCategory,
  getTopProducts,
  getWeekdayRevenue,
  getCategories,
  type DashboardData,
  type ExpenseByCategory,
  type MonthlyExpense,
  type YearlyExpense,
  type ProductSort,
  type WeekdayRevenue,
  type TimeFilter,
  type Period,
} from '../services/dashboardService';
import RevenueChart from '../components/Dashboard/RevenueChart';
import SalesByCategoryChart from '../components/Dashboard/SalesByCategoryChart';
import TopProductsTable from '../components/Dashboard/TopProductsTable';
import WeekdayChart from '../components/Dashboard/WeekdayChart';
import ExpenseByMonthChart from '../components/Dashboard/ExpenseByMonthChart';
import ExpenseByCategoryChart from '../components/Dashboard/ExpenseByCategoryChart';
import ErrorAlert from '../components/shared/ErrorAlert';
import PeriodSelector from '../components/shared/PeriodSelector';
import TimeFilterSelector, { type TimeFilterOption } from '../components/shared/TimeFilterSelector';
import MetricSelector, { type Metric } from '../components/shared/MetricSelector';
import WeekdayMetricSelector, { type WeekdayMetric } from '../components/shared/WeekdayMetricSelector';
import CategorySelector from '../components/shared/CategorySelector';
import { ChartColumnIncreasingIcon, ChartLineIcon } from '../components/shared/Icons';
import { getGastosCategorias } from '../services/gastosCategoriasService';
import '../styles/dashboard.css';
import '../styles/shared/page-header.css';

type DashboardTab = 'general' | 'balance' | 'ventas' | 'gastos' | 'productos';

const DashboardOverview = () => {
  const [activeTab, setActiveTab] = useState<DashboardTab>('general');
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [expenseCategories, setExpenseCategories] = useState<string[]>([]);
  const [revenuePeriod, setRevenuePeriod] = useState<Period>('monthly');
  const [revenueMetric, setRevenueMetric] = useState<Metric>('ingresos');
  const [revenueChartType, setRevenueChartType] = useState<'bar' | 'area'>('area');
  const [salesByCategoryTimeFilter, setSalesByCategoryTimeFilter] = useState<TimeFilter>('last_year');
  const [topProductsTimeFilter, setTopProductsTimeFilter] = useState<TimeFilter>('last_year');
  const [topProductsSort, setTopProductsSort] = useState<ProductSort>('top');
  const [topProductsCategory, setTopProductsCategory] = useState<string>('');
  const [topProductsLimit, setTopProductsLimit] = useState<number>(5);

  const [expensesByPeriod, setExpensesByPeriod] = useState<MonthlyExpense[] | YearlyExpense[]>([]);
  const [expensesByCategory, setExpensesByCategory] = useState<ExpenseByCategory[]>([]);
  const [expensesLoading, setExpensesLoading] = useState(false);
  const [expensePeriod, setExpensePeriod] = useState<Period>('monthly');
  const [expenseCategory, setExpenseCategory] = useState<string>('');
  const [expenseChartType, setExpenseChartType] = useState<'bar' | 'area'>('area');
  const [expenseCategoryTimeFilter, setExpenseCategoryTimeFilter] = useState<TimeFilter>('last_month');
  
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

  const fetchDashboardData = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      
      // Cargar datos del dashboard y categorías en paralelo
      const [dashboardData, categoriesData, expenseCategoriesData] = await Promise.all([
        getDashboardData(),
        getCategories(),
        getGastosCategorias(),
      ]);
      
      setData(dashboardData);
      
      // Usar las categorías del endpoint de categorías
      const categories = categoriesData.map(c => c.nombre).sort();
      setAvailableCategories(categories);

      const expenseCategoryNames = Array.from(
        new Set(
          expenseCategoriesData
            .filter(c => c.padre_id == null)
            .map(c => c.nombre)
        )
      ).sort();
      setExpenseCategories(expenseCategoryNames);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar el dashboard';
      setError(`Error al cargar dashboard: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSalesByCategory = useCallback(async () => {
    try {
      const salesByCategory = await getSalesByCategory(8, salesByCategoryTimeFilter);
      setData((prev) => (prev ? { ...prev, salesByCategory } : prev));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar ventas por categoria';
      setError(`Error al cargar ventas por categoria: ${errorMessage}`);
    }
  }, [salesByCategoryTimeFilter]);

  const fetchTopProducts = useCallback(async () => {
    try {
      const topProducts = await getTopProducts(
        topProductsLimit,
        topProductsTimeFilter,
        topProductsSort,
        topProductsCategory || undefined
      );
      setData((prev) => (prev ? { ...prev, topProducts } : prev));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar productos mas vendidos';
      setError(`Error al cargar productos mas vendidos: ${errorMessage}`);
    }
  }, [topProductsLimit, topProductsTimeFilter, topProductsSort, topProductsCategory]);

  const fetchWeekdayRevenue = useCallback(async () => {
    try {
      setWeekdayLoading(true);
      const weekdayRevenue = await getWeekdayRevenue(weekdayCategory || undefined, weekdayTimeFilter);
      setWeekdayData(weekdayRevenue);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar promedio por día de semana';
      setError(`Error al cargar promedio por día de semana: ${errorMessage}`);
    } finally {
      setWeekdayLoading(false);
    }
  }, [weekdayCategory, weekdayTimeFilter]);

  const fetchExpensesByPeriod = useCallback(async () => {
    try {
      setExpensesLoading(true);
      const limit = expensePeriod === 'monthly' ? 12 : 5;
      const expenses = await getExpensesByPeriod(expensePeriod, limit, expenseCategory || undefined);
      setExpensesByPeriod(expenses);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar gastos por período';
      setError(`Error al cargar gastos por período: ${errorMessage}`);
    } finally {
      setExpensesLoading(false);
    }
  }, [expensePeriod, expenseCategory]);

  const fetchExpensesByCategory = useCallback(async () => {
    try {
      const expenses = await getExpensesByCategory(8, expenseCategoryTimeFilter, true); // true para incluir subcategorías
      setExpensesByCategory(expenses);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar gastos por categoria';
      setError(`Error al cargar gastos por categoria: ${errorMessage}`);
    }
  }, [expenseCategoryTimeFilter]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    fetchSalesByCategory();
  }, [fetchSalesByCategory]);

  useEffect(() => {
    fetchTopProducts();
  }, [fetchTopProducts]);

  useEffect(() => {
    fetchWeekdayRevenue();
  }, [fetchWeekdayRevenue]);

  useEffect(() => {
    fetchExpensesByPeriod();
  }, [fetchExpensesByPeriod]);

  useEffect(() => {
    fetchExpensesByCategory();
  }, [fetchExpensesByCategory]);

  useEffect(() => {
    const saleEventKey = 'pizza_fiori:sale_created_at';

    const handleSaleCreated = async () => {
      await fetchDashboardData();
      await Promise.all([
        fetchSalesByCategory(),
        fetchTopProducts(),
        fetchWeekdayRevenue(),
      ]);
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === saleEventKey) {
        void handleSaleCreated();
      }
    };

    window.addEventListener('sale:created', handleSaleCreated);
    window.addEventListener('storage', handleStorage);

    return () => {
      window.removeEventListener('sale:created', handleSaleCreated);
      window.removeEventListener('storage', handleStorage);
    };
  }, [fetchDashboardData, fetchSalesByCategory, fetchTopProducts, fetchWeekdayRevenue]);

  const renderGeneralTab = () => (
    <div className="dashboard-placeholder">
      <h2>Bienvenido al Dashboard</h2>
      <p>Selecciona una pestaña para ver el análisis detallado</p>
    </div>
  );

  const renderBalanceTab = () => (
    <div className="dashboard-placeholder">
      <h2>Tab Balance</h2>
      <p>Contenido para análisis de balance (ingresos vs gastos)</p>
    </div>
  );

  const renderVentasTab = () => (
    <div className="charts-grid">
      <div className="chart-section chart-main">
        <div className="section-header">
          <h2 className="chart-title">Ventas por período</h2>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px', width: '100%' }}>
            <MetricSelector 
              selectedMetric={revenueMetric} 
              onMetricChange={setRevenueMetric} 
            />
            <PeriodSelector 
              selectedPeriod={revenuePeriod} 
              onPeriodChange={setRevenuePeriod} 
            />
            <span style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }} />
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center', backgroundColor: 'var(--color-hover)', padding: '4px', borderRadius: '8px', height: '36px' }}>
              <button
                onClick={() => setRevenueChartType('area')}
                aria-label="Cambiar a linea"
                title="Linea"
                style={{
                  padding: '8px 12px',
                  height: '36px',
                  background: revenueChartType === 'area' ? 'var(--color-accent)' : 'transparent',
                  color: revenueChartType === 'area' ? '#ffffff' : 'var(--color-text-muted)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: revenueChartType === 'area' ? '600' : '500',
                  transition: 'all 0.2s ease',
                }}
              >
                <ChartLineIcon size={18} />
              </button>
              <button
                onClick={() => setRevenueChartType('bar')}
                aria-label="Cambiar a barras"
                title="Barras"
                style={{
                  padding: '8px 12px',
                  height: '36px',
                  background: revenueChartType === 'bar' ? 'var(--color-accent)' : 'transparent',
                  color: revenueChartType === 'bar' ? '#ffffff' : 'var(--color-text-muted)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: revenueChartType === 'bar' ? '600' : '500',
                  transition: 'all 0.2s ease',
                }}
              >
                <ChartColumnIncreasingIcon size={18} />
              </button>
            </div>
          </div>
        </div>
        <RevenueChart 
          dailyData={data?.dailyRevenue || []}
          monthlyData={data?.monthlyRevenue || []}
          yearlyData={data?.yearlyRevenue || []}
          selectedPeriod={revenuePeriod}
          selectedMetric={revenueMetric}
          chartType={revenueChartType}
          height={350} 
        />
      </div>

      <div className="chart-section chart-secondary chart-span-rows">
        <div className="section-header">
          <h2 className="chart-title">Ventas por categoria</h2>
          <TimeFilterSelector
            value={salesByCategoryTimeFilter}
            onChange={setSalesByCategoryTimeFilter}
          />
        </div>
        <SalesByCategoryChart data={data?.salesByCategory || []} height={300} />
      </div>

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
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
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
  );

  const renderGastosTab = () => (
    <div className="charts-grid">
      <div className="chart-section chart-main">
        <div className="section-header">
          <h2 className="chart-title">Gastos por período</h2>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px', width: '100%' }}>
            <PeriodSelector
              selectedPeriod={expensePeriod}
              onPeriodChange={setExpensePeriod}
              options={[
                { value: 'monthly', label: 'Mensual' },
                { value: 'yearly', label: 'Anual' },
              ]}
            />
            <CategorySelector
              categories={expenseCategories}
              selectedCategory={expenseCategory}
              onCategoryChange={setExpenseCategory}
            />
            <span style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }} />
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center', backgroundColor: 'var(--color-hover)', padding: '4px', borderRadius: '8px', height: '36px' }}>
              <button
                onClick={() => setExpenseChartType('area')}
                aria-label="Cambiar a linea"
                title="Linea"
                style={{
                  padding: '8px 12px',
                  height: '36px',
                  background: expenseChartType === 'area' ? 'var(--color-accent)' : 'transparent',
                  color: expenseChartType === 'area' ? '#ffffff' : 'var(--color-text-muted)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: expenseChartType === 'area' ? '600' : '500',
                  transition: 'all 0.2s ease',
                }}
              >
                <ChartLineIcon size={18} />
              </button>
              <button
                onClick={() => setExpenseChartType('bar')}
                aria-label="Cambiar a barras"
                title="Barras"
                style={{
                  padding: '8px 12px',
                  height: '36px',
                  background: expenseChartType === 'bar' ? 'var(--color-accent)' : 'transparent',
                  color: expenseChartType === 'bar' ? '#ffffff' : 'var(--color-text-muted)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: expenseChartType === 'bar' ? '600' : '500',
                  transition: 'all 0.2s ease',
                }}
              >
                <ChartColumnIncreasingIcon size={18} />
              </button>
            </div>
          </div>
        </div>
        {expensesLoading ? (
          <div
            style={{
              height: '300px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-text-muted)',
            }}
          >
            Cargando...
          </div>
        ) : (
          <ExpenseByMonthChart
            data={expensesByPeriod}
            height={350}
            chartType={expenseChartType}
          />
        )}
      </div>
      <div className="chart-section chart-secondary chart-span-rows">
        <div className="section-header">
          <h2 className="chart-title">Gastos por categoria</h2>
          <TimeFilterSelector
            value={expenseCategoryTimeFilter}
            onChange={setExpenseCategoryTimeFilter}
            options={[
              { value: 'last_month', label: 'Mes actual', description: 'Últimos 30 días' },
              { value: 'last_year', label: 'Último año', description: 'Últimos 12 meses' },
            ]}
          />
        </div>
        <ExpenseByCategoryChart data={expensesByCategory} height={300} />
      </div>
    </div>
  );

  const renderProductosTab = () => (
    <div className="table-section">
      <div className="section-header">
        <h2 className="section-title">Ranking de productos</h2>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* Selector de top de productos */}
          <select
            value={topProductsLimit}
            onChange={(e) => setTopProductsLimit(Number(e.target.value))}
            style={{
              padding: '8px 12px',
              backgroundColor: 'var(--color-hover)',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '500',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
            <option value={15}>Top 15</option>
            <option value={20}>Top 20</option>
          </select>

          {/* Selector de ordenamiento */}
          <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--color-hover)', padding: '4px', borderRadius: '8px' }}>
            <button
              onClick={() => setTopProductsSort('top')}
              style={{
                padding: '8px 16px',
                background: topProductsSort === 'top' ? 'var(--color-accent)' : 'transparent',
                color: topProductsSort === 'top' ? '#ffffff' : 'var(--color-text-muted)',
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
                background: topProductsSort === 'bottom' ? 'var(--color-accent)' : 'transparent',
                color: topProductsSort === 'bottom' ? '#ffffff' : 'var(--color-text-muted)',
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
        products={data?.topProducts || []}
      />
    </div>
  );

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

      {/* Pestañas */}
      <div className="dashboard-tabs-wrapper">
        <div className="dashboard-tabs">
          <button
            className={`dashboard-tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            General
          </button>
          <button
            className={`dashboard-tab ${activeTab === 'balance' ? 'active' : ''}`}
            onClick={() => setActiveTab('balance')}
          >
            Balance
          </button>
          <button
            className={`dashboard-tab ${activeTab === 'ventas' ? 'active' : ''}`}
            onClick={() => setActiveTab('ventas')}
          >
            Ventas
          </button>
          <button
            className={`dashboard-tab ${activeTab === 'gastos' ? 'active' : ''}`}
            onClick={() => setActiveTab('gastos')}
          >
            Gastos
          </button>
          <button
            className={`dashboard-tab ${activeTab === 'productos' ? 'active' : ''}`}
            onClick={() => setActiveTab('productos')}
          >
            Productos
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {/* PESTAÑA: GENERAL */}
        {activeTab === 'general' && renderGeneralTab()}

        {/* PESTAÑA: BALANCE */}
        {activeTab === 'balance' && renderBalanceTab()}

        {/* PESTAÑA: VENTAS */}
        {activeTab === 'ventas' && renderVentasTab()}

        {/* PESTAÑA: GASTOS */}
        {activeTab === 'gastos' && renderGastosTab()}

        {/* PESTAÑA: PRODUCTOS */}
        {activeTab === 'productos' && renderProductosTab()}
      </div>
    </div>
  );
}

export default DashboardOverview;
