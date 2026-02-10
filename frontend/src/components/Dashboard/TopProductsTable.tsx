/**
 * TopProductsTable - Tabla de Ranking de productos
 * Componente reutilizable para mostrar ranking de productos con estado de stock
 */

import type { TopProduct } from '../../services/dashboardService';

interface TopProductsTableProps {
  products: TopProduct[];
}

const TopProductsTable = ({ products }: TopProductsTableProps) => {
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="top-products-table">
      <table>
        <thead>
          <tr>
            <th>Producto</th>
            <th>Categoría</th>
            <th>Precio</th>
            <th className="text-center">Cantidad vendida</th>
            <th className="text-center">Estado</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={`${product.nombre}-${product.categoria}`}>
              <td className="product-name">{product.nombre}</td>
              <td className="category">{product.categoria}</td>
              <td className="price">{formatCurrency(product.precio)}</td>
              <td className="text-center quantity">{product.cantidad}</td>
              <td className="text-center">
                <span className={`status-badge ${product.enStock ? 'in-stock' : 'out-of-stock'}`}>
                  {product.enStock ? 'Disponible' : 'Sin stock'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TopProductsTable;
