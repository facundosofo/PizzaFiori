/**
 * Mock data for Dashboard Overview
 * TODO: Replace with actual API data once backend endpoints are ready
 */

export interface DailyRevenue {
  date: string;
  revenue: number;
  orders: number;
}

export interface HourlyRevenue {
  hour: string;
  revenue: number;
  orders: number;
}

export interface WeeklyRevenue {
  week: string;
  revenue: number;
  orders: number;
}

export interface MonthlyRevenue {
  month: string;
  revenue: number;
  orders: number;
}

export interface YearlyRevenue {
  year: string;
  revenue: number;
  orders: number;
}

export interface TopProduct {
  id: number;
  name: string;
  category: string;
  price: number;
  quantity: number;
  inStock: boolean;
}

export interface DashboardMetrics {
  totalRevenue: number;
  totalOrders: number;
  totalVisitors: number;
}

// Generar datos de los últimos 30 días
const generateDailyRevenue = (): DailyRevenue[] => {
  const data: DailyRevenue[] = [];
  const today = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    // Simular variación realista: más ventas viernes/sábado
    const dayOfWeek = date.getDay();
    const isWeekend = dayOfWeek === 5 || dayOfWeek === 6;
    const baseRevenue = isWeekend ? 15000 : 8000;
    const variance = Math.random() * 0.3 - 0.15; // ±15%
    
    data.push({
      date: date.toISOString().split('T')[0],
      revenue: Math.round(baseRevenue * (1 + variance)),
      orders: Math.round((baseRevenue * (1 + variance)) / 450), // ~450 pesos por orden promedio
    });
  }
  
  return data;
};

// Generar datos de las últimas 12 semanas
const generateWeeklyRevenue = (): WeeklyRevenue[] => {
  const data: WeeklyRevenue[] = [];
  const today = new Date();
  
  for (let i = 11; i >= 0; i--) {
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() - (i * 7));
    
    const weekNum = Math.ceil(weekStart.getDate() / 7);
    const month = weekStart.toLocaleDateString('es-ES', { month: 'short' });
    
    const baseRevenue = 65000;
    const variance = Math.random() * 0.25 - 0.125; // ±12.5%
    
    data.push({
      week: `W${weekNum} ${month}`,
      revenue: Math.round(baseRevenue * (1 + variance)),
      orders: Math.round((baseRevenue * (1 + variance)) / 450),
    });
  }
  
  return data;
};

// Generar datos de los últimos 12 meses
const generateMonthlyRevenue = (): MonthlyRevenue[] => {
  const data: MonthlyRevenue[] = [];
  const today = new Date();
  
  for (let i = 11; i >= 0; i--) {
    const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
    const month = date.toLocaleDateString('es-ES', { month: 'short' });
    
    const baseRevenue = 280000;
    const variance = Math.random() * 0.2 - 0.1; // ±10%
    
    data.push({
      month: month.charAt(0).toUpperCase() + month.slice(1),
      revenue: Math.round(baseRevenue * (1 + variance)),
      orders: Math.round((baseRevenue * (1 + variance)) / 450),
    });
  }
  
  return data;
};

// Generar datos de los últimos 5 años
const generateYearlyRevenue = (): YearlyRevenue[] => {
  const data: YearlyRevenue[] = [];
  const currentYear = new Date().getFullYear();
  
  for (let i = 4; i >= 0; i--) {
    const year = currentYear - i;
    const baseRevenue = 3200000;
    const growth = i === 0 ? 1.15 : 1 - (i * 0.08); // Crecimiento año actual
    
    data.push({
      year: year.toString(),
      revenue: Math.round(baseRevenue * growth),
      orders: Math.round((baseRevenue * growth) / 450),
    });
  }
  
  return data;
};

// Datos por mes del año actual (para gráfico de barras mensual)
export const mockMonthlyRevenueByMonth: MonthlyRevenue[] = [
  { month: 'Ene', revenue: 245000, orders: 544 },
  { month: 'Feb', revenue: 268000, orders: 596 },
  { month: 'Mar', revenue: 292000, orders: 649 },
  { month: 'Abr', revenue: 278000, orders: 618 },
  { month: 'May', revenue: 310000, orders: 689 },
  { month: 'Jun', revenue: 295000, orders: 656 },
  { month: 'Jul', revenue: 325000, orders: 722 },
  { month: 'Ago', revenue: 318000, orders: 707 },
  { month: 'Sep', revenue: 288000, orders: 640 },
  { month: 'Oct', revenue: 305000, orders: 678 },
  { month: 'Nov', revenue: 298000, orders: 662 },
  { month: 'Dic', revenue: 342000, orders: 760 },
];

// Datos por franja horaria (11:00 - 23:00)
export const mockHourlyRevenue: HourlyRevenue[] = [
  { hour: '11:00', revenue: 1200, orders: 3 },
  { hour: '12:00', revenue: 3800, orders: 9 },
  { hour: '13:00', revenue: 5200, orders: 12 },
  { hour: '14:00', revenue: 4100, orders: 10 },
  { hour: '15:00', revenue: 2600, orders: 6 },
  { hour: '16:00', revenue: 1800, orders: 4 },
  { hour: '17:00', revenue: 2400, orders: 5 },
  { hour: '18:00', revenue: 3200, orders: 7 },
  { hour: '19:00', revenue: 6800, orders: 15 },
  { hour: '20:00', revenue: 8900, orders: 20 },
  { hour: '21:00', revenue: 9400, orders: 21 },
  { hour: '22:00', revenue: 7200, orders: 16 },
  { hour: '23:00', revenue: 4500, orders: 10 },
];

// Productos más vendidos
export const mockTopProducts: TopProduct[] = [
  {
    id: 1,
    name: 'Muzzarella',
    category: 'Pizzas',
    price: 4500,
    quantity: 248,
    inStock: true,
  },
  {
    id: 2,
    name: 'Napolitana',
    category: 'Pizzas',
    price: 5200,
    quantity: 186,
    inStock: true,
  },
  {
    id: 3,
    name: 'Fugazzeta',
    category: 'Pizzas',
    price: 4800,
    quantity: 142,
    inStock: false,
  },
  {
    id: 4,
    name: 'Coca-Cola 1.5L',
    category: 'Bebidas',
    price: 800,
    quantity: 312,
    inStock: true,
  },
];

// Métricas clave
export const mockDashboardMetrics: DashboardMetrics = {
  totalRevenue: 345280,
  totalOrders: 1542,
  totalVisitors: 2834,
};

export const mockDailyRevenue = generateDailyRevenue();
export const mockWeeklyRevenue = generateWeeklyRevenue();
export const mockMonthlyRevenue = generateMonthlyRevenue();
export const mockYearlyRevenue = generateYearlyRevenue();
