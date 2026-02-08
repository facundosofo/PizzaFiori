/**
 * TopProductsTable - Tabla de productos más vendidos
 * Componente reutilizable para mostrar ranking de productos con estado de stock
 */

import type { TopProduct } from '../../mocks/dashboard';

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
            <tr key={product.id}>
              <td className="product-name">{product.name}</td>
              <td className="category">{product.category}</td>
              <td className="price">{formatCurrency(product.price)}</td>
              <td className="text-center quantity">{product.quantity}</td>
              <td className="text-center">
                <span className={`status-badge ${product.inStock ? 'in-stock' : 'out-of-stock'}`}>
                  {product.inStock ? 'Disponible' : 'Sin stock'}
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
