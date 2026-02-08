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
  ordenes: number;
}

export interface WeeklyRevenue {
  semana: string;
  ingresos: number;
  ordenes: number;
}

export interface MonthlyRevenue {
  mes: string;
  ingresos: number;
  ordenes: number;
}

export interface YearlyRevenue {
  año: string;
  ingresos: number;
  ordenes: number;
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

export type { DailyRevenue, WeeklyRevenue, MonthlyRevenue, YearlyRevenue };
export type Period = 'daily' | 'weekly' | 'monthly' | 'yearly';

export interface DashboardData {
  dailyRevenue: DailyRevenue[];
  weeklyRevenue: WeeklyRevenue[];
  monthlyRevenue: MonthlyRevenue[];
  yearlyRevenue: YearlyRevenue[];
  monthlyRevenueByMonth: MonthlyRevenue[];
  topProducts: TopProduct[];
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
    weeklyRevenue,
    monthlyRevenue,
    yearlyRevenue,
    monthlyRevenueByMonth,
    topProducts,
    metrics,
  ] = await Promise.all([
    getRevenueByPeriod('daily', 30) as Promise<DailyRevenue[]>,
    getRevenueByPeriod('weekly', 12) as Promise<WeeklyRevenue[]>,
    getRevenueByPeriod('monthly', 12) as Promise<MonthlyRevenue[]>,
    getRevenueByPeriod('yearly', 5) as Promise<YearlyRevenue[]>,
    getMonthlyRevenue(),
    getTopProducts(10),
    getDashboardMetrics(),
  ]);

  return {
    dailyRevenue,
    weeklyRevenue,
    monthlyRevenue,
    yearlyRevenue,
    monthlyRevenueByMonth,
    topProducts,
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
): Promise<DailyRevenue[] | WeeklyRevenue[] | MonthlyRevenue[] | YearlyRevenue[]> => {
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
 * Obtener productos más vendidos
 * 
 * TODO: Conectar con GET /api/dashboard/products/top?limit={limit}
 */
export const getTopProducts = async (limit: number = 10): Promise<TopProduct[]> => {
  return fetchJson(`/dashboard/products/top?limit=${limit}`);
};

/**
 * Obtener métricas generales
 * 
 * TODO: Conectar con GET /api/dashboard/metrics
 */
export const getDashboardMetrics = async (): Promise<DashboardMetrics> => {
  return fetchJson('/dashboard/metrics');
};

export const getMonthlyRevenue = async (): Promise<MonthlyRevenue[]> => {
  return fetchJson('/dashboard/revenue/monthly');
};
