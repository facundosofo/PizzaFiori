export type StockEstado = "ok" | "warning" | "critical" | "sin_stock";

export interface CategoryStock {
  categoria_id: number;
  categoria_nombre: string;
  cantidad: number;
  umbral_amarillo: number | null;
  umbral_rojo: number | null;
  estado: StockEstado;
}

export interface StockMovement {
  id: number;
  timestamp: string;
  username: string;
  action: string;
  changes: {
    tipo: "INGRESO" | "AJUSTE_BAJA" | "VENTA_DESCUENTO" | "CONFIG_ALERTAS";
    cantidad?: number;
    cantidad_descontada?: number;
    stock_anterior?: number;
    stock_nuevo?: number;
    numero_orden?: string;
    umbral_amarillo?: number | null;
    umbral_rojo?: number | null;
    categoria_nombre?: string;
  };
}

export interface AddStockRequest {
  cantidad: number;
}

export interface ConfigureAlertsRequest {
  umbral_amarillo: number | null;
  umbral_rojo: number | null;
}

export const STOCK_ESTADO_LABELS: Record<StockEstado, string> = {
  ok: "Normal",
  warning: "Stock bajo",
  critical: "Stock crítico",
  sin_stock: "Sin stock",
};

export const STOCK_ESTADO_BADGE: Record<
  StockEstado,
  "success" | "warning" | "danger" | "neutral"
> = {
  ok: "success",
  warning: "warning",
  critical: "danger",
  sin_stock: "neutral",
};
