import type { Product } from './product';

export interface Category {
  id: number;
  nombre: string;
  productos?: Product[];
}
