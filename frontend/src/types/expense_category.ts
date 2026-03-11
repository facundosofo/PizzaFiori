export interface ExpenseCategory {
  id: number;
  nombre: string;
  descripcion?: string;
  padre_id?: number | null;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  subcategorias?: ExpenseCategory[];
}
