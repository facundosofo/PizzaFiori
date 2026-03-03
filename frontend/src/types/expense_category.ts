export interface ExpenseCategory {
  id: number;
  nombre: string;
  padre_id?: number | null;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  subcategorias?: ExpenseCategory[];
}
