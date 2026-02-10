/**
 * Mock data for Dashboard Overview
 * TODO: Replace with actual API data once backend endpoints are ready
 */

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
  id: number;
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
    
    const revenue = Math.round(baseRevenue * (1 + variance));
    data.push({
      fecha: date.toISOString().split('T')[0],
      ingresos: revenue,
      pedidos: Math.round(revenue / 450), // ~450 pesos por orden promedio
      cantidad: Math.round(revenue / 180), // ~180 pesos por item promedio
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
    
    const revenue = Math.round(baseRevenue * (1 + variance));
    data.push({
      semana: `W${weekNum} ${month}`,
      ingresos: revenue,
      pedidos: Math.round(revenue / 450),
      cantidad: Math.round(revenue / 180),
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
    
    const revenue = Math.round(baseRevenue * (1 + variance));
    data.push({
      mes: month.charAt(0).toUpperCase() + month.slice(1),
      ingresos: revenue,
      pedidos: Math.round(revenue / 450),
      cantidad: Math.round(revenue / 180),
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
    
    const revenue = Math.round(baseRevenue * growth);
    data.push({
      año: year.toString(),
      ingresos: revenue,
      pedidos: Math.round(revenue / 450),
      cantidad: Math.round(revenue / 180),
    });
  }
  
  return data;
};

// Datos por mes del año actual (para gráfico de barras mensual)
export const mockMonthlyRevenueByMonth: MonthlyRevenue[] = [
  { mes: 'Ene', ingresos: 245000, pedidos: 544, cantidad: 1361 },
  { mes: 'Feb', ingresos: 268000, pedidos: 596, cantidad: 1489 },
  { mes: 'Mar', ingresos: 292000, pedidos: 649, cantidad: 1622 },
  { mes: 'Abr', ingresos: 278000, pedidos: 618, cantidad: 1544 },
  { mes: 'May', ingresos: 310000, pedidos: 689, cantidad: 1722 },
  { mes: 'Jun', ingresos: 295000, pedidos: 656, cantidad: 1639 },
  { mes: 'Jul', ingresos: 325000, pedidos: 722, cantidad: 1806 },
  { mes: 'Ago', ingresos: 318000, pedidos: 707, cantidad: 1767 },
  { mes: 'Sep', ingresos: 288000, pedidos: 640, cantidad: 1600 },
  { mes: 'Oct', ingresos: 305000, pedidos: 678, cantidad: 1694 },
  { mes: 'Nov', ingresos: 298000, pedidos: 662, cantidad: 1656 },
  { mes: 'Dic', ingresos: 342000, pedidos: 760, cantidad: 1900 },
];

// Productos más vendidos
export const mockTopProducts: TopProduct[] = [
  {
    id: 1,
    nombre: 'Muzzarella',
    categoria: 'Pizzas',
    precio: 4500,
    cantidad: 248,
    enStock: true,
  },
  {
    id: 2,
    nombre: 'Napolitana',
    categoria: 'Pizzas',
    precio: 5200,
    cantidad: 186,
    enStock: true,
  },
  {
    id: 3,
    nombre: 'Fugazzeta',
    categoria: 'Pizzas',
    precio: 4800,
    cantidad: 142,
    enStock: false,
  },
  {
    id: 4,
    nombre: 'Coca-Cola 1.5L',
    categoria: 'Bebidas',
    precio: 800,
    cantidad: 312,
    enStock: true,
  },
];

// Métricas clave
export const mockDashboardMetrics: DashboardMetrics = {
  ingresoTotal: 345280,
  ordenesTotal: 1542,
};

export const mockDailyRevenue = generateDailyRevenue();
export const mockWeeklyRevenue = generateWeeklyRevenue();
export const mockMonthlyRevenue = generateMonthlyRevenue();
export const mockYearlyRevenue = generateYearlyRevenue();
