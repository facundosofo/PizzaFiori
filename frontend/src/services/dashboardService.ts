/**
 * Dashboard Service
 * 
 * TODO: Conectar con backend cuando los endpoints estén disponibles
 * 
 * Endpoints esperados:
 * - GET /api/dashboard/revenue/daily?days=30
 *   Response: Array<{ date: string, revenue: number, orders: number }>
 * 
 * - GET /api/dashboard/revenue/hourly?date=YYYY-MM-DD
 *   Response: Array<{ hour: string, revenue: number, orders: number }>
 * 
 * - GET /api/dashboard/products/top?limit=10
 *   Response: Array<{ id: number, name: string, category: string, price: number, quantity: number, inStock: boolean }>
 * 
 * - GET /api/dashboard/metrics
 *   Response: { totalRevenue: number, totalOrders: number, totalVisitors: number }
 */

import {
  mockDailyRevenue,
  mockWeeklyRevenue,
  mockMonthlyRevenue,
  mockYearlyRevenue,
  mockMonthlyRevenueByMonth,
  mockHourlyRevenue,
  mockTopProducts,
  mockDashboardMetrics,
  type DailyRevenue,
  type WeeklyRevenue,
  type MonthlyRevenue,
  type YearlyRevenue,
  type HourlyRevenue,
  type TopProduct,
  type DashboardMetrics,
} from '../mocks/dashboard';

export type { DailyRevenue, WeeklyRevenue, MonthlyRevenue, YearlyRevenue };
export type Period = 'daily' | 'weekly' | 'monthly' | 'yearly';

export interface DashboardData {
  dailyRevenue: DailyRevenue[];
  weeklyRevenue: WeeklyRevenue[];
  monthlyRevenue: MonthlyRevenue[];
  yearlyRevenue: YearlyRevenue[];
  monthlyRevenueByMonth: MonthlyRevenue[];
  hourlyRevenue: HourlyRevenue[];
  topProducts: TopProduct[];
  metrics: DashboardMetrics;
}

/**
 * Obtener todos los datos del dashboard
 * 
 * TODO: Reemplazar con llamadas reales al backend
 * Actualmente retorna datos mock para desarrollo y diseño
 */
export const getDashboardData = async (): Promise<DashboardData> => {
  // Simular delay de red
  await new Promise((resolve) => setTimeout(resolve, 300));

  // TODO: Implementar cuando backend esté listo:
  // const response = await fetch(`${API_BASE_URL}/api/dashboard/data`);
  // if (!response.ok) throw new Error('Failed to fetch dashboard data');
  // return response.json();

  return {
    dailyRevenue: mockDailyRevenue,
    weeklyRevenue: mockWeeklyRevenue,
    monthlyRevenue: mockMonthlyRevenue,
    yearlyRevenue: mockYearlyRevenue,
    monthlyRevenueByMonth: mockMonthlyRevenueByMonth,
    hourlyRevenue: mockHourlyRevenue,
    topProducts: mockTopProducts,
    metrics: mockDashboardMetrics,
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
  await new Promise((resolve) => setTimeout(resolve, 200));
  
  // TODO: const response = await fetch(`${API_BASE_URL}/api/dashboard/revenue?period=${period}&limit=${limit}`);
  
  switch (period) {
    case 'daily':
      return limit ? mockDailyRevenue.slice(-limit) : mockDailyRevenue;
    case 'weekly':
      return limit ? mockWeeklyRevenue.slice(-limit) : mockWeeklyRevenue;
    case 'monthly':
      return limit ? mockMonthlyRevenue.slice(-limit) : mockMonthlyRevenue;
    case 'yearly':
      return limit ? mockYearlyRevenue.slice(-limit) : mockYearlyRevenue;
    default:
      return mockDailyRevenue;
  }
};

/**
 * Obtener ventas diarias
 * 
 * TODO: Conectar con GET /api/dashboard/revenue/daily?days={days}
 */
export const getDailyRevenue = async (days: number = 30): Promise<DailyRevenue[]> => {
  await new Promise((resolve) => setTimeout(resolve, 200));
  
  // TODO: const response = await fetch(`${API_BASE_URL}/api/dashboard/revenue/daily?days=${days}`);
  
  return mockDailyRevenue.slice(-days);
};

/**
 * Obtener ventas por franja horaria
 * 
 * TODO: Conectar con GET /api/dashboard/revenue/hourly?date={date}
 */
export const getHourlyRevenue = async (date?: string): Promise<HourlyRevenue[]> => {
  await new Promise((resolve) => setTimeout(resolve, 200));
  
  // TODO: const response = await fetch(`${API_BASE_URL}/api/dashboard/revenue/hourly?date=${date || 'today'}`);
  
  return mockHourlyRevenue;
};

/**
 * Obtener productos más vendidos
 * 
 * TODO: Conectar con GET /api/dashboard/products/top?limit={limit}
 */
export const getTopProducts = async (limit: number = 10): Promise<TopProduct[]> => {
  await new Promise((resolve) => setTimeout(resolve, 200));
  
  // TODO: const response = await fetch(`${API_BASE_URL}/api/dashboard/products/top?limit=${limit}`);
  
  return mockTopProducts.slice(0, limit);
};

/**
 * Obtener métricas generales
 * 
 * TODO: Conectar con GET /api/dashboard/metrics
 */
export const getDashboardMetrics = async (): Promise<DashboardMetrics> => {
  await new Promise((resolve) => setTimeout(resolve, 200));
  
  // TODO: const response = await fetch(`${API_BASE_URL}/api/dashboard/metrics`);
  
  return mockDashboardMetrics;
};
