import type { ExpenseCategory } from "./expense_category";

export interface Expense {
  id: number;
  categoria_gasto_id: number;
  descripcion?: string | null;
  monto: number;
  fecha_pago: string;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  categoria_gasto?: ExpenseCategory | null;
}
