import type { Product } from './product';

export interface ProductoCategoria {
  id: number;
  nombre: string;
  activo?: boolean;
  productos?: Product[];
}
