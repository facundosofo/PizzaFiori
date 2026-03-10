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
  getExpensesSummary,
  getSalesByCategory,
  getTopProducts,
  getWeekdayRevenue,
  getCategories,
  getProductsSummary,
  getBalanceMetrics,
  getMonthlyBalanceData,
  type DashboardData,
  type ExpenseByCategory,
  type ExpenseSummary,
  type ProductSummary,
  type MonthlyExpense,
  type YearlyExpense,
  type ProductSort,
  type WeekdayRevenue,
  type TimeFilter,
  type Period,
  type BalanceMetrics,
  type MonthlyBalanceList,
  type SalesByCategory,
  type TopProduct,
} from '../services/dashboardService';
import RevenueChart from '../components/Dashboard/RevenueChart';
import SalesByCategoryChart from '../components/Dashboard/SalesByCategoryChart';
import TopProductsTable from '../components/Dashboard/TopProductsTable';
import WeekdayChart from '../components/Dashboard/WeekdayChart';
import ExpenseByMonthChart from '../components/Dashboard/ExpenseByMonthChart';
import ExpenseByCategoryChart from '../components/Dashboard/ExpenseByCategoryChart';
import TotalSalesKPICard from '../components/Dashboard/TotalSalesKPICard';
import TotalExpensesKPICard from '../components/Dashboard/TotalExpensesKPICard';
import NetProfitKPICard from '../components/Dashboard/NetProfitKPICard';
import NetMarginKPICard from '../components/Dashboard/NetMarginKPICard';
import MonthlyBalanceBarChart from '../components/Dashboard/MonthlyBalanceBarChart';
import NetMarginLineChart from '../components/Dashboard/NetMarginLineChart';
import TotalOrdersKPICard from '../components/Dashboard/TotalOrdersKPICard';
import ErrorAlert from '../components/shared/ErrorAlert';
import PeriodSelector from '../components/shared/PeriodSelector';
import TimeFilterSelector, { type TimeFilterOption } from '../components/shared/TimeFilterSelector';
import MetricSelector, { type Metric } from '../components/shared/MetricSelector';
import WeekdayMetricSelector, { type WeekdayMetric } from '../components/shared/WeekdayMetricSelector';
import CategorySelector from '../components/shared/CategorySelector';
import { ChartColumnIncreasingIcon, ChartLineIcon, ShieldOffIcon } from '../components/shared/Icons';
import { getGastosCategorias } from '../services/gastosCategoriasService';
import { useAuth } from '../contexts/AuthContext';
import '../styles/dashboard.css';
import '../styles/shared/page-header.css';

type DashboardTab = 'general' | 'balance' | 'ventas' | 'gastos' | 'productos';

const DashboardOverview = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const [activeTab, setActiveTab] = useState<DashboardTab>('general');
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  if (!isAdmin) {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <ShieldOffIcon size={64} color="#ef4444" />
          <h1>Acceso Denegado</h1>
          <p>Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    );
  }
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
  const [expenseSummary, setExpenseSummary] = useState<ExpenseSummary | null>(null);
  const [productsSummary, setProductsSummary] = useState<ProductSummary | null>(null);
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

  // Estados para la tab de balance
  const [balanceMetrics, setBalanceMetrics] = useState<BalanceMetrics | null>(null);
  const [balanceLoading, setBalanceLoading] = useState(false);
  const [monthlyBalanceData, setMonthlyBalanceData] = useState<MonthlyBalanceList | null>(null);
  const [monthlyBalanceLoading, setMonthlyBalanceLoading] = useState(false);
  const [balancePeriod, setBalancePeriod] = useState<Period>('monthly');

  // Estados para el tab General
  const [generalWeekdayMetric, setGeneralWeekdayMetric] = useState<WeekdayMetric>('ingresos');
  const [generalWeekdayData, setGeneralWeekdayData] = useState<WeekdayRevenue[]>([]);
  const [generalWeekdayLoading, setGeneralWeekdayLoading] = useState(false);
  const [generalBalancePeriod, setGeneralBalancePeriod] = useState<Period>('monthly');
  const [generalBalanceData, setGeneralBalanceData] = useState<MonthlyBalanceList | null>(null);
  const [generalBalanceLoading, setGeneralBalanceLoading] = useState(false);
  const [generalBalanceMetrics, setGeneralBalanceMetrics] = useState<BalanceMetrics | null>(null);
  const [generalBalanceMetricsLoading, setGeneralBalanceMetricsLoading] = useState(false);
  const [generalSalesCategoryFilter, setGeneralSalesCategoryFilter] = useState<TimeFilter>('last_month');
  const [generalSalesByCategory, setGeneralSalesByCategory] = useState<SalesByCategory[]>([]);
  const [generalExpenseCategoryFilter, setGeneralExpenseCategoryFilter] = useState<TimeFilter>('last_month');
  const [generalExpensesByCategory, setGeneralExpensesByCategory] = useState<ExpenseByCategory[]>([]);
  const [generalTopProducts, setGeneralTopProducts] = useState<TopProduct[]>([]);
  const [generalTopProductsFilter, setGeneralTopProductsFilter] = useState<TimeFilter>('last_year');

  const weekdayTimeFilterOptions: TimeFilterOption[] = [
    { value: 'last_month', label: 'Mes actual', description: 'Del 1° del mes hasta hoy' },
    { value: 'last_year', label: 'Año actual', description: 'Del 1° de enero hasta hoy' },
    { value: 'all_time', label: 'Histórico', description: 'Todos los datos' },
  ];

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

  const formatVariation = (value: number | null, label: string): string => {
    if (value === null || value === undefined) return `— vs ${label}`;
    const status = value >= 0 ? 'Aumento' : 'Bajo';
    const direction = value >= 0 ? '↑' : '↓';
    return `${status} ${direction} ${Math.abs(value).toFixed(1)}% vs ${label}`;
  };

  const getVariationColor = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'var(--color-text-muted)';
    return value >= 0 ? 'var(--color-danger, #ef4444)' : 'var(--color-success, #16a34a)';
  };

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

  const fetchExpensesSummary = useCallback(async () => {
    try {
      const summary = await getExpensesSummary();
      setExpenseSummary(summary);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar resumen de gastos';
      setError(`Error al cargar resumen de gastos: ${errorMessage}`);
    }
  }, []);

  const fetchProductsSummary = useCallback(async () => {
    try {
      const summary = await getProductsSummary('last_month');
      setProductsSummary(summary);
    } catch (err) {
      // No propagar al error global para no bloquear el dashboard completo.
      // Las cards de resumen mostrarán '—' cuando no haya datos.
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar resumen de productos';
      console.warn('fetchProductsSummary:', errorMessage);
    }
  }, []);

  const fetchBalanceMetrics = useCallback(async () => {
    try {
      setBalanceLoading(true);
      const metrics = await getBalanceMetrics();
      setBalanceMetrics(metrics);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar balance';
      setError(`Error al cargar balance: ${errorMessage}`);
    } finally {
      setBalanceLoading(false);
    }
  }, []);

  const fetchMonthlyBalanceData = useCallback(async () => {
    try {
      setMonthlyBalanceLoading(true);
      const data = await getMonthlyBalanceData(balancePeriod);
      setMonthlyBalanceData(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar datos mensuales';
      setError(`Error al cargar datos mensuales: ${errorMessage}`);
    } finally {
      setMonthlyBalanceLoading(false);
    }
  }, [balancePeriod]);

  const fetchGeneralBalanceMetrics = useCallback(async () => {
    try {
      setGeneralBalanceMetricsLoading(true);
      const metrics = await getBalanceMetrics();
      setGeneralBalanceMetrics(metrics);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar balance';
      setError(`Error al cargar balance: ${errorMessage}`);
    } finally {
      setGeneralBalanceMetricsLoading(false);
    }
  }, []);

  const fetchGeneralBalanceData = useCallback(async () => {
    try {
      setGeneralBalanceLoading(true);
      const result = await getMonthlyBalanceData(generalBalancePeriod);
      setGeneralBalanceData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar datos de balance';
      setError(`Error al cargar datos de balance: ${errorMessage}`);
    } finally {
      setGeneralBalanceLoading(false);
    }
  }, [generalBalancePeriod]);

  const fetchGeneralSalesByCategory = useCallback(async () => {
    try {
      const result = await getSalesByCategory(8, generalSalesCategoryFilter);
      setGeneralSalesByCategory(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar ventas por categoría';
      setError(`Error al cargar ventas por categoría: ${errorMessage}`);
    }
  }, [generalSalesCategoryFilter]);

  const fetchGeneralExpensesByCategory = useCallback(async () => {
    try {
      const result = await getExpensesByCategory(8, generalExpenseCategoryFilter, false);
      setGeneralExpensesByCategory(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar gastos por categoría';
      setError(`Error al cargar gastos por categoría: ${errorMessage}`);
    }
  }, [generalExpenseCategoryFilter]);

  const fetchGeneralTopProducts = useCallback(async () => {
    try {
      const result = await getTopProducts(5, generalTopProductsFilter, 'top');
      setGeneralTopProducts(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar top productos';
      setError(`Error al cargar top productos: ${errorMessage}`);
    }
  }, [generalTopProductsFilter]);

  const fetchGeneralWeekdayRevenue = useCallback(async () => {
    try {
      setGeneralWeekdayLoading(true);
      const result = await getWeekdayRevenue(undefined, 'last_month');
      setGeneralWeekdayData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar promedio por día de semana';
      setError(`Error al cargar promedio por día de semana (general): ${errorMessage}`);
    } finally {
      setGeneralWeekdayLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    if (activeTab !== 'ventas') return;
    fetchSalesByCategory();
  }, [activeTab, fetchSalesByCategory]);

  useEffect(() => {
    if (activeTab !== 'ventas') return;
    fetchTopProducts();
  }, [activeTab, fetchTopProducts]);

  useEffect(() => {
    if (activeTab !== 'ventas') return;
    fetchWeekdayRevenue();
  }, [activeTab, fetchWeekdayRevenue]);

  useEffect(() => {
    if (activeTab !== 'gastos') return;
    fetchExpensesByPeriod();
  }, [activeTab, fetchExpensesByPeriod]);

  useEffect(() => {
    if (activeTab !== 'gastos') return;
    fetchExpensesByCategory();
  }, [activeTab, fetchExpensesByCategory]);

  useEffect(() => {
    if (activeTab !== 'gastos') return;
    fetchExpensesSummary();
  }, [activeTab, fetchExpensesSummary]);

  useEffect(() => {
    if (activeTab !== 'productos') return;
    fetchProductsSummary();
  }, [activeTab, fetchProductsSummary]);

  useEffect(() => {
    if (activeTab !== 'balance') return;
    fetchBalanceMetrics();
    fetchMonthlyBalanceData();
  }, [activeTab, balancePeriod, fetchBalanceMetrics, fetchMonthlyBalanceData]);

  useEffect(() => {
    if (activeTab !== 'general') return;
    fetchGeneralBalanceMetrics();
  }, [activeTab, fetchGeneralBalanceMetrics]);

  useEffect(() => {
    if (activeTab !== 'general') return;
    fetchGeneralBalanceData();
  }, [activeTab, fetchGeneralBalanceData]);

  useEffect(() => {
    if (activeTab !== 'general') return;
    fetchGeneralSalesByCategory();
  }, [activeTab, fetchGeneralSalesByCategory]);

  useEffect(() => {
    if (activeTab !== 'general') return;
    fetchGeneralExpensesByCategory();
  }, [activeTab, fetchGeneralExpensesByCategory]);

  useEffect(() => {
    if (activeTab !== 'general') return;
    fetchGeneralTopProducts();
  }, [activeTab, fetchGeneralTopProducts]);

  useEffect(() => {
    if (activeTab !== 'general') return;
    fetchGeneralWeekdayRevenue();
  }, [activeTab, fetchGeneralWeekdayRevenue]);

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Row 1 — KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
          minHeight: '140px',
        }}
      >
        <NetProfitKPICard data={generalBalanceMetrics?.net_profit ?? null} loading={generalBalanceMetricsLoading} />
        <TotalSalesKPICard />
        <TotalExpensesKPICard />
        <TotalOrdersKPICard monthlyRevenue={data?.monthlyRevenue ?? null} />
      </div>

      {/* Row 2 — WeekdayChart + MonthlyBalanceBarChart (50/50) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div className="chart-section">
          <div className="section-header">
            <h2 className="chart-title">Ventas por día de semana</h2>
            <WeekdayMetricSelector
              selectedMetric={generalWeekdayMetric}
              onMetricChange={setGeneralWeekdayMetric}
            />
          </div>
          {generalWeekdayLoading ? (
              <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>Cargando...</div>
            ) : (
              <WeekdayChart data={generalWeekdayData} selectedMetric={generalWeekdayMetric} height={300} />
            )}
        </div>

        <div className="chart-section">
          <div className="section-header">
            <h2 className="chart-title">Resultado neto</h2>
            <PeriodSelector
              selectedPeriod={generalBalancePeriod}
              onPeriodChange={setGeneralBalancePeriod}
              options={[
                { value: 'monthly', label: 'Mensual' },
                { value: 'yearly', label: 'Anual' },
              ]}
            />
          </div>
          {generalBalanceLoading ? (
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
          ) : generalBalanceData ? (
            <MonthlyBalanceBarChart
              data={generalBalanceData.data}
              currentMonth={generalBalanceData.current_month}
              height={300}
            />
          ) : null}
        </div>
      </div>

      {/* Row 3 — Ventas por categoría, Gastos por categoría, Top productos */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div className="chart-section">
          <div className="section-header">
            <h2 className="chart-title">Ventas por categoría</h2>
            <TimeFilterSelector
              value={generalSalesCategoryFilter}
              onChange={setGeneralSalesCategoryFilter}
              options={[
                { value: 'last_month', label: 'Mes actual', description: 'Del 1° del mes hasta hoy' },
                { value: 'last_year', label: 'Año actual', description: 'Del 1° de enero hasta hoy' },
              ]}
            />
          </div>
          <SalesByCategoryChart data={generalSalesByCategory} height={250} />
        </div>

        <div className="chart-section">
          <div className="section-header">
            <h2 className="chart-title">Gastos por categoría</h2>
            <TimeFilterSelector
              value={generalExpenseCategoryFilter}
              onChange={setGeneralExpenseCategoryFilter}
              options={[
                { value: 'last_month', label: 'Mes actual', description: 'Del 1° del mes hasta hoy' },
                { value: 'last_year', label: 'Año actual', description: 'Del 1° de enero hasta hoy' },
              ]}
            />
          </div>
          <ExpenseByCategoryChart data={generalExpensesByCategory} height={250} />
        </div>

        <div className="chart-section">
          <div className="section-header">
            <h2 className="chart-title">Top productos</h2>
            <TimeFilterSelector
              value={generalTopProductsFilter}
              onChange={setGeneralTopProductsFilter}
              options={[
                { value: 'last_month', label: 'Mes actual', description: 'Del 1° del mes hasta hoy' },
                { value: 'last_year', label: 'Año actual', description: 'Del 1° de enero hasta hoy' },
              ]}
            />
          </div>
          <TopProductsTable products={generalTopProducts} />
        </div>
      </div>
    </div>
  );

  const renderBalanceTab = () => (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Cards de resumen */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
          minHeight: '140px',
        }}
      >
        <NetProfitKPICard data={balanceMetrics?.net_profit ?? null} loading={balanceLoading} />
        <TotalSalesKPICard />
        <NetMarginKPICard data={balanceMetrics?.net_margin ?? null} loading={balanceLoading} />
        <TotalExpensesKPICard />
      </div>

      {/* Gráficos de balance */}
      {monthlyBalanceData && monthlyBalanceData.data.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '16px',
          }}
        >
          {/* Gráfico de barras agrupadas */}
          <div
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              padding: '16px 18px',
            }}
          >
            <div className="section-header">
              <h2 className="chart-title">Resultado Neto</h2>
              <PeriodSelector
                selectedPeriod={balancePeriod}
                onPeriodChange={setBalancePeriod}
                options={[
                  { value: 'monthly', label: 'Mensual' },
                  { value: 'yearly', label: 'Anual' },
                ]}
              />
            </div>
            {monthlyBalanceLoading ? (
              <div style={{ height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
                Cargando...
              </div>
            ) : (
              <MonthlyBalanceBarChart 
                data={monthlyBalanceData.data}
                currentMonth={monthlyBalanceData.current_month}
                height={350}
              />
            )}
          </div>

          {/* Gráfico de línea del margen neto */}
          <div
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              padding: '16px 18px',
            }}
          >
            <div className="section-header">
              <h2 className="chart-title">Evolución del Margen Neto</h2>
              <PeriodSelector
                selectedPeriod={balancePeriod}
                onPeriodChange={setBalancePeriod}
                options={[
                  { value: 'monthly', label: 'Mensual' },
                  { value: 'yearly', label: 'Anual' },
                ]}
              />
            </div>
            {monthlyBalanceLoading ? (
              <div style={{ height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
                Cargando...
              </div>
            ) : (
              <NetMarginLineChart 
                data={monthlyBalanceData.data}
                currentMonth={monthlyBalanceData.current_month}
                height={350}
              />
            )}
          </div>
        </div>
      )}
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
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)',
        gap: '16px',
        alignItems: 'stretch',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '12px',
            minHeight: '140px',
          }}
        >
          <div
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              padding: '16px 18px',
            }}
          >
            <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Resultado mensual
            </div>
            <div style={{ color: 'var(--color-text)', fontSize: '32px', fontWeight: 700, marginTop: '14px', marginBottom: '12px' }}>
              {formatCurrencyOrDash(expenseSummary?.resultado_mensual)}
            </div>
            <div style={{ color: getVariationColor(expenseSummary?.variacion_mensual_pct), fontSize: '13px', marginTop: '8px' }}>
              {formatVariation(expenseSummary?.variacion_mensual_pct ?? null, expenseSummary?.comparacion_mes || 'mes anterior')}
            </div>
          </div>
          <div
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              padding: '16px 18px',
            }}
          >
            <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Resultado anual
            </div>
            <div style={{ color: 'var(--color-text)', fontSize: '32px', fontWeight: 700, marginTop: '14px', marginBottom: '12px' }}>
              {formatCurrencyOrDash(expenseSummary?.resultado_anual)}
            </div>
            <div style={{ color: getVariationColor(expenseSummary?.variacion_anual_pct), fontSize: '13px', marginTop: '8px' }}>
              {formatVariation(expenseSummary?.variacion_anual_pct ?? null, expenseSummary?.comparacion_ano?.toString() || 'año anterior')}
            </div>
          </div>
          <div
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              padding: '16px 18px',
            }}
          >
            <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Categoría que más creció
            </div>
            <div style={{ color: 'var(--color-text)', fontSize: '30px', fontWeight: 700, marginTop: '14px', marginBottom: '12px' }}>
              {expenseSummary?.categoria_mayor_crecimiento?.categoria || '—'}
            </div>
            <div style={{ color: getVariationColor(expenseSummary?.categoria_mayor_crecimiento?.porcentaje), fontSize: '13px', marginTop: '8px' }}>
              {formatVariation(expenseSummary?.categoria_mayor_crecimiento?.porcentaje ?? null, expenseSummary?.comparacion_mes || 'mes anterior')}
            </div>
          </div>
        </div>
        <div className="chart-section chart-main" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
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
            <div style={{ flex: 1, minHeight: 0 }}>
              <ExpenseByMonthChart
                data={expensesByPeriod}
                height="100%"
                chartType={expenseChartType}
              />
            </div>
          )}
        </div>
      </div>
      <div className="chart-section chart-secondary">
        <div className="section-header">
          <h2 className="chart-title">Gastos por categoria</h2>
          <TimeFilterSelector
            value={expenseCategoryTimeFilter}
            onChange={setExpenseCategoryTimeFilter}
            options={[
              { value: 'last_month', label: 'Mes actual', description: 'Del 1° del mes hasta hoy' },
              { value: 'last_year', label: 'Año actual', description: 'Del 1° de enero hasta hoy' },
            ]}
          />
        </div>
        <ExpenseByCategoryChart data={expensesByCategory} height={300} />
      </div>
    </div>
  );

  const renderProductosTab = () => (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
      }}
    >
      {/* Cards de resumen de productos */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
          minHeight: '140px',
        }}
      >
        <div
          style={{
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border)',
            borderRadius: '12px',
            padding: '16px 18px',
          }}
        >
          <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Producto más vendido
          </div>
          <div style={{ color: 'var(--color-text)', fontSize: '28px', fontWeight: 700, marginTop: '14px', marginBottom: '4px' }}>
            {productsSummary?.producto_mas_vendido || '—'}
          </div>
          {productsSummary?.categoria_mas_vendida && (
            <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginBottom: '8px' }}>
              {productsSummary.categoria_mas_vendida}
            </div>
          )}
          <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '8px' }}>
            {productsSummary?.mes_actual || ''} • {productsSummary?.cantidad_mas_vendida ? `${productsSummary.cantidad_mas_vendida} unidades` : '—'}
          </div>
        </div>
        <div
          style={{
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border)',
            borderRadius: '12px',
            padding: '16px 18px',
          }}
        >
          <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Promoción más vendida
          </div>
          <div style={{ color: 'var(--color-text)', fontSize: '32px', fontWeight: 700, marginTop: '14px', marginBottom: '12px' }}>
            {productsSummary?.promocion_mas_vendida || '—'}
          </div>
          <div style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '8px' }}>
            {productsSummary?.mes_actual || ''} • {productsSummary?.cantidad_promocion ? `${productsSummary.cantidad_promocion} vendidas` : '—'}
          </div>
        </div>
      </div>

      {/* Tabla de ranking */}
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
