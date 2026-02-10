/**
 * Dashboard Service
 * 
 * Endpoints:
 * - GET /dashboard/revenue?period={period}&limit={limit}
 * - GET /dashboard/revenue/monthly
 * - GET /dashboard/products/top?limit={limit}
 * - GET /dashboard/metrics
 */

import env from '../config/env';

export interface DailyRevenue {
  fecha: string;
  ingresos: number;
  pedidos: number;
  cantidad: number;
}

export interface WeeklyRevenue {
  semana: string;
  ingresos: number;
  pedidos: number;
  cantidad: number;
}

export interface MonthlyRevenue {
  mes: string;
  ingresos: number;
  pedidos: number;
  cantidad: number;
}

export interface YearlyRevenue {
  año: string;
  ingresos: number;
  pedidos: number;
  cantidad: number;
}

export interface TopProduct {
  id?: number;
  nombre: string;
  categoria: string;
  precio: number;
  cantidad: number;
  enStock: boolean;
}

export interface DashboardMetrics {
  ingresoTotal: number;
  ordenesTotal: number;
}

export interface SalesByCategory {
  categoria: string;
  cantidad: number;
}

export interface WeekdayRevenue {
  dia_semana: string;
  promedio_ingresos: number;
  promedio_pedidos: number;
  promedio_cantidad: number;
}

export interface Category {
  id: number;
  nombre: string;
  descripcion: string | null;
}

export type Period = 'daily' | 'monthly' | 'yearly';
export type TimeFilter = 'today' | 'last_7_days' | 'last_month' | 'last_year' | 'all_time';
export type ProductSort = 'top' | 'bottom';

export interface DashboardData {
  dailyRevenue: DailyRevenue[];
  monthlyRevenue: MonthlyRevenue[];
  yearlyRevenue: YearlyRevenue[];
  topProducts: TopProduct[];
  salesByCategory: SalesByCategory[];
  metrics: DashboardMetrics;
}

const fetchJson = async <T>(path: string): Promise<T> => {
  const res = await fetch(`${env.API_BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Error ${res.status} al consultar ${path}`);
  }
  return res.json() as Promise<T>;
};

/**
 * Obtener todos los datos del dashboard
 * 
 * TODO: Reemplazar con llamadas reales al backend
 * Actualmente retorna datos mock para desarrollo y diseño
 */
export const getDashboardData = async (): Promise<DashboardData> => {
  const [
    dailyRevenue,
    monthlyRevenue,
    yearlyRevenue,
    topProducts,
    salesByCategory,
    metrics,
  ] = await Promise.all([
    getRevenueByPeriod('daily', 30) as Promise<DailyRevenue[]>,
    getRevenueByPeriod('monthly', 12) as Promise<MonthlyRevenue[]>,
    getRevenueByPeriod('yearly', 5) as Promise<YearlyRevenue[]>,
    getTopProducts(5, 'all_time'),
    getSalesByCategory(8, 'all_time'),
    getDashboardMetrics(),
  ]);

  return {
    dailyRevenue,
    monthlyRevenue,
    yearlyRevenue,
    topProducts,
    salesByCategory,
    metrics,
  };
};

/**
 * Obtener ventas según período
 * 
 * TODO: Conectar con GET /api/dashboard/revenue?period={period}&limit={limit}
 */
export const getRevenueByPeriod = async (
  period: Period,
  limit?: number
): Promise<DailyRevenue[] | MonthlyRevenue[] | YearlyRevenue[]> => {
  const params = new URLSearchParams({ period });
  if (limit) {
    params.set('limit', String(limit));
  }
  return fetchJson(`/dashboard/revenue?${params.toString()}`);
};

/**
 * Obtener ventas diarias
 * 
 * TODO: Conectar con GET /api/dashboard/revenue/daily?days={days}
 */
export const getDailyRevenue = async (days: number = 30): Promise<DailyRevenue[]> => {
  return getRevenueByPeriod('daily', days) as Promise<DailyRevenue[]>;
};

/**
 * Obtener productos más/menos vendidos
 * 
 * TODO: Conectar con GET /api/dashboard/products/top?limit={limit}&sort={sort}&category={category}
 */
export const getTopProducts = async (
  limit: number = 10,
  timeFilter?: TimeFilter,
  sort: ProductSort = 'top',
  category?: string
): Promise<TopProduct[]> => {
  const params = new URLSearchParams({ limit: String(limit), sort });
  if (timeFilter) {
    params.set('time_filter', timeFilter);
  }
  if (category) {
    params.set('category', category);
  }
  const url = `/dashboard/products/top?${params.toString()}`;
  console.log('[Service] Fetching products:', url);
  return fetchJson(url);
};

/**
 * Obtener métricas generales
 * 
 * TODO: Conectar con GET /api/dashboard/metrics
 */
export const getDashboardMetrics = async (): Promise<DashboardMetrics> => {
  return fetchJson('/dashboard/metrics');
};


export const getSalesByCategory = async (
  limit?: number,
  timeFilter?: TimeFilter
): Promise<SalesByCategory[]> => {
  const params = new URLSearchParams();
  if (limit) {
    params.set('limit', String(limit));
  }
  if (timeFilter) {
    params.set('time_filter', timeFilter);
  }
  const query = params.toString();
  const url = `/dashboard/sales-by-category${query ? `?${query}` : ''}`;
  console.log('[Service] Fetching sales by category:', url);
  return fetchJson(url);
};

/**
 * Obtener promedio de ventas por día de semana (datos históricos)
 * 
 * GET /api/dashboard/revenue/weekday?category={category}
 */
export const getWeekdayRevenue = async (
  category?: string
): Promise<WeekdayRevenue[]> => {
  const params = new URLSearchParams();
  if (category) {
    params.set('category', category);
  }
  const query = params.toString();
  const url = `/dashboard/revenue/weekday${query ? `?${query}` : ''}`;
  console.log('[Service] Fetching weekday revenue:', url);
  return fetchJson(url);
};

/**
 * Obtener todas las categorías
 * 
 * GET /api/categorias
 */
export const getCategories = async (): Promise<Category[]> => {
  const url = '/categorias';
  console.log('[Service] Fetching categories:', url);
  return fetchJson(url);
};
