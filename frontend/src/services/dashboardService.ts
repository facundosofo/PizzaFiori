/**
 * Dashboard Service
 * 
 * Endpoints:
 * - GET /dashboard/revenue?period={period}&limit={limit}
 * - GET /dashboard/revenue/monthly
 * - GET /dashboard/products/top?limit={limit}
 */

import api from './http';

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

export interface MonthlyExpense {
  mes: string;
  gastos: number;
}

export interface YearlyExpense {
  año: string;
  gastos: number;
}

export interface ExpenseByCategory {
  categoria: string;
  gastos: number;
  subcategorias?: ExpenseSubcategory[];
}

export interface ExpenseSubcategory {
  categoria: string;
  gastos: number;
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
}

const fetchJson = async <T>(path: string): Promise<T> => {
  const response = await api.get<T>(path);
  return response.data;
};

/**
 * Obtener todos los datos del dashboard
 * 
 * Obtiene datos del backend
 */
export const getDashboardData = async (): Promise<DashboardData> => {
  const [
    dailyRevenue,
    monthlyRevenue,
    yearlyRevenue,
    topProducts,
    salesByCategory,
  ] = await Promise.all([
    getRevenueByPeriod('daily', 30) as Promise<DailyRevenue[]>,
    getRevenueByPeriod('monthly', 12) as Promise<MonthlyRevenue[]>,
    getRevenueByPeriod('yearly', 5) as Promise<YearlyRevenue[]>,
    getTopProducts(5, 'last_year'),
    getSalesByCategory(8, 'last_year'),
  ]);

  return {
    dailyRevenue,
    monthlyRevenue,
    yearlyRevenue,
    topProducts,
    salesByCategory,
  };
};

/**
 * Obtener ventas según período
 * 
 * GET /api/dashboard/revenue?period={period}&limit={limit}
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
 * GET /api/dashboard/revenue/daily?days={days}
 */
export const getDailyRevenue = async (days: number = 30): Promise<DailyRevenue[]> => {
  return getRevenueByPeriod('daily', days) as Promise<DailyRevenue[]>;
};

/**
 * Obtener productos más/menos vendidos
 * 
 * GET /api/dashboard/products/top?limit={limit}&sort={sort}&category={category}
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
  return fetchJson(url);
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
  return fetchJson(url);
};

/**
 * Obtener promedio de ventas por día de semana (datos históricos)
 * 
 * GET /api/dashboard/revenue/weekday?category={category}&time_filter={time_filter}
 */
export const getWeekdayRevenue = async (
  category?: string,
  timeFilter?: TimeFilter
): Promise<WeekdayRevenue[]> => {
  const params = new URLSearchParams();
  if (category) {
    params.set('category', category);
  }
  if (timeFilter) {
    params.set('time_filter', timeFilter);
  }
  const query = params.toString();
  const url = `/dashboard/revenue/weekday${query ? `?${query}` : ''}`;
  return fetchJson(url);
};

/**
 * Obtener gastos según período
 * 
 * GET /api/dashboard/expenses?period={period}&limit={limit}&category={category}
 */
export const getExpensesByPeriod = async (
  period: Period,
  limit?: number,
  category?: string
): Promise<MonthlyExpense[] | YearlyExpense[]> => {
  const params = new URLSearchParams({ period });
  if (limit) {
    params.set('limit', String(limit));
  }
  if (category) {
    params.set('category', category);
  }
  return fetchJson(`/dashboard/expenses?${params.toString()}`);
};

/**
 * Obtener gastos por mes
 * 
 * GET /api/dashboard/expenses/monthly?limit={limit}&category={category}
 */
export const getExpensesByMonth = async (
  limit: number = 12,
  category?: string
): Promise<MonthlyExpense[]> => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (category) {
    params.set('category', category);
  }
  const url = `/dashboard/expenses/monthly?${params.toString()}`;
  return fetchJson(url);
};

/**
 * Obtener gastos por categoria
 * 
 * GET /api/dashboard/expenses/by-category?limit={limit}&time_filter={time_filter}&include_subcategories={includeSubcategories}
 */
export const getExpensesByCategory = async (
  limit: number = 8,
  timeFilter?: TimeFilter,
  includeSubcategories: boolean = false
): Promise<ExpenseByCategory[]> => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (timeFilter) {
    params.set('time_filter', timeFilter);
  }
  if (includeSubcategories) {
    params.set('include_subcategories', 'true');
  }
  const url = `/dashboard/expenses/by-category?${params.toString()}`;
  return fetchJson(url);
};

/**
 * Obtener todas las categorías
 * 
 * GET /api/categorias
 */
export const getCategories = async (): Promise<Category[]> => {
  const url = '/categorias';
  return fetchJson(url);
};
