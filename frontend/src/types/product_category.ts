import type { Product } from './product';

export interface ProductoCategoria {
  id: number;
  nombre: string;
  orden?: number;
  activo?: boolean;
  productos?: Product[];
}
