import { useState } from 'react';
import { motion } from 'framer-motion';
import type { Product } from '../types/product';
import type { Category } from '../types/category';
import { formatCurrency } from '../utils/formatters';
import * as Icons from './shared/Icons';
import env from '../config/env';
import pizzaMitadImage from '../assets/PizzaMitad.png';
import '../styles/product-quick-selector.css';
import '../styles/shared/quantity-controls.css';

interface ProductQuickSelectorProps {
  products: Product[];
  categories: Category[];
  cartQuantities: Map<number, number>; // producto_id -> quantity in cart
  onAddProduct: (product: Product) => void;
  onUpdateProductQuantity: (productId: number, newQuantity: number) => void;
  onOpenPizzaMitadMitad?: () => void; // Nuevo prop para abrir modal de pizza mitad-mitad
}

export const ProductQuickSelector: React.FC<ProductQuickSelectorProps> = ({
  products,
  categories,
  cartQuantities,
  onAddProduct,
  onUpdateProductQuantity,
  onOpenPizzaMitadMitad,
}) => {
  const [collapsedCategories, setCollapsedCategories] = useState<Set<number>>(new Set());
  
  // Format quantity label
  const formatCantidad = (cantidad: number): string => {
    switch (cantidad) {
      case 1:
        return "Unidad";
      case 6:
        return "1/2 Docena";
      case 12:
        return "Docena";
      default:
        return `${cantidad} unid.`;
    }
  };
  
  // Group products by category
  const productsByCategory = categories.map((category) => ({
    category,
    products: products.filter((p) => p.categoria_id === category.id),
  })).filter(({ products }) => products.length > 0);

  const handleIncrement = (product: Product) => {
    const currentQty = cartQuantities.get(product.id) || 0;
    if (currentQty === 0) {
      // Add new product to cart
      onAddProduct(product);
    } else {
      // Increment existing product
      onUpdateProductQuantity(product.id, currentQty + 1);
    }
  };

  const handleDecrement = (productId: number) => {
    const currentQty = cartQuantities.get(productId) || 0;
    if (currentQty > 0) {
      onUpdateProductQuantity(productId, currentQty - 1);
    }
  };

  const toggleCategoryCollapse = (categoryId: number) => {
    setCollapsedCategories((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  if (productsByCategory.length === 0) {
    return (
      <div className="product-quick-selector">
        <div className="product-selector-empty product-selector-empty-box">
          <div className="product-selector-empty-icon"><Icons.PizzaIcon size={36} /></div>
          <p>No hay productos disponibles</p>
        </div>
      </div>
    );
  }

  return (
    <div className="product-quick-selector">
      {productsByCategory.map(({ category, products }) => {
        const isCollapsed = collapsedCategories.has(category.id);
        return (
        <section key={category.id} className="product-category-section">
          <div className="product-category-header">
            <h3 className="product-category-title">{category.nombre}</h3>
            <button
              className={`product-category-toggle ${isCollapsed ? "collapsed" : ""}`}
              onClick={() => toggleCategoryCollapse(category.id)}
              aria-label={isCollapsed ? "Expandir" : "Colapsar"}
            >
              <Icons.ChevronDownIcon size={16} />
            </button>
          </div>
          {!isCollapsed && (
          <div className="product-scroll-horizontal">
            {/* Botón especial de Pizza Mitad-Mitad para categoría Pizzas */}
            {category.nombre.toLowerCase() === 'pizzas' && onOpenPizzaMitadMitad && (
              <motion.div
                className="product-card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: 0.12 }}
              >
                <div className="product-card-image">
                  <img src={pizzaMitadImage} alt="Pizza mitad y mitad" />
                </div>
                <div className="product-card-content">
                  <h4 className="product-card-name">Pizza Mitad-Mitad</h4>
                  <div className="product-card-prices">
                    <div className="price-item no-price">Precio de la pizza más cara</div>
                  </div>
                  <div className="product-qty-controls">
                    <button
                      className="product-qty-btn-add"
                      onClick={onOpenPizzaMitadMitad}
                      title="Crear pizza mitad-mitad"
                    >
                      Agregar
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
            
            {products.map((product) => {
              const qtyInCart = cartQuantities.get(product.id) || 0;
              const imageUrl = product.imagen ? `${env.API_BASE_URL}/${product.imagen}` : "/placeholder.png";

              return (
                <motion.div
                  key={product.id}
                  className="product-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {qtyInCart > 0 && (
                    <div className="product-in-cart-badge">
                      {qtyInCart}
                    </div>
                  )}

                  <div className="product-card-image">
                    <img src={imageUrl} alt={product.nombre} />
                  </div>

                  <div className="product-card-content">
                    <h4 className="product-card-name">{product.nombre}</h4>
                    
                    <div className="product-card-prices">
                      {product.precios && product.precios.length > 0 ? (
                        product.precios.map((precio_item) => (
                          <div key={precio_item.id} className="price-item">
                            <span className="price-cantidad">{formatCantidad(precio_item.cantidad)}</span>
                            <span className="price-amount">{formatCurrency(precio_item.precio)}</span>
                          </div>
                        ))
                      ) : (
                        <div className="price-item no-price">Sin precios</div>
                      )}
                    </div>

                    <div className="product-qty-controls">
                      {qtyInCart > 0 ? (
                        <div className="quantity-control">
                          <button
                            type="button"
                            className="qty-btn qty-btn-minus"
                            onClick={() => handleDecrement(product.id)}
                            aria-label="Disminuir cantidad"
                          >
                            <Icons.MinusIcon size={14} />
                          </button>
                          <input
                            type="number"
                            min="0"
                            max="1000"
                            className="qty-input"
                            value={qtyInCart}
                            onFocus={(e) => e.target.select()}
                            onChange={(e) => {
                              const newQty = parseInt(e.target.value) || 0;
                              if (newQty === 0) {
                                handleDecrement(product.id);
                              } else {
                                onUpdateProductQuantity(product.id, newQty);
                              }
                            }}
                          />
                          <button
                            type="button"
                            className="qty-btn qty-btn-plus"
                            onClick={() => handleIncrement(product)}
                            aria-label="Aumentar cantidad"
                          >
                            <Icons.PlusIcon size={14} />
                          </button>
                        </div>
                      ) : (
                        <button
                          className="product-qty-btn-add"
                          onClick={() => handleIncrement(product)}
                          title="Agregar al carrito"
                        >
                          Agregar
                        </button>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
          )}
        </section>
        );
      })}
    </div>
  );
};
