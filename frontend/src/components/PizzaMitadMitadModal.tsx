import { useState } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import MultiSelect, { type MultiSelectItem } from './shared/MultiSelect';
import type { Product } from '../types/product';
import type { Category } from '../types/category';
import { formatCurrency } from '../utils/formatters';
import * as Icons from './shared/Icons';
import '../styles/shared/quantity-controls.css';
import '../styles/pizza-mitad-mitad-modal.css';

interface PizzaMitadMitadModalProps {
  isOpen: boolean;
  onClose: () => void;
  products: Product[];
  categories: Category[];
  onConfirm: (pizzaMitadMitad: {
    producto_id_izquierda: number;
    producto_id_derecha: number;
    cantidad: number;
    nombre_completo: string;
    precio_unitario: number;
  }) => void;
}

export const PizzaMitadMitadModal: React.FC<PizzaMitadMitadModalProps> = ({
  isOpen,
  onClose,
  products,
  categories,
  onConfirm,
}) => {
  const [selectedPizzaIds, setSelectedPizzaIds] = useState<number[]>([]);
  const [cantidad, setCantidad] = useState(1);

  const isSameCantidad = (a: number, b: number) => Math.abs(a - b) < 1e-9;

  const getUnitPrice = (product: Product): number => {
    if (!product.precios || product.precios.length === 0) return 0;

    const unitPriceRow = product.precios.find((p) => isSameCantidad(Number(p.cantidad), 1));
    if (unitPriceRow) return Number(unitPriceRow.precio);

    const fallbackRow = [...product.precios].sort((a, b) => Number(a.cantidad) - Number(b.cantidad))[0];
    return Number(fallbackRow?.precio ?? 0);
  };

  // Filter only pizza products
  const pizzaProducts = products.filter(product => {
    const category = categories.find(cat => cat.id === product.categoria_id);
    return category?.nombre.toLowerCase() === 'pizzas' || 
           product.nombre.toLowerCase().includes('pizza');
  });

  // Convert to MultiSelect format: label sin precio (chips), optionLabel con precio (dropdown)
  const pizzaMultiSelect: MultiSelectItem[] = pizzaProducts.map(product => {
    const priceForOne = getUnitPrice(product);
    return {
      id: product.id,
      label: product.nombre, // Solo nombre para los chips seleccionados
      optionLabel: `${product.nombre} - ${formatCurrency(priceForOne)}`, // Nombre + precio para opciones
      disabled: false,
    };
  });

  const handlePizzaSelection = (selectedIds: number[]) => {
    // Limitar a máximo 2 selecciones
    if (selectedIds.length > 2) {
      // Mantener solo las 2 primeras selecciones
      setSelectedPizzaIds(selectedIds.slice(0, 2));
    } else {
      setSelectedPizzaIds(selectedIds);
    }
  };

  const calculatePrice = () => {
    if (selectedPizzaIds.length !== 2) return 0;
    
    // Get the selected products
    const selectedProducts = pizzaProducts.filter(p => selectedPizzaIds.includes(p.id));
    if (selectedProducts.length !== 2) return 0;
    
    const price1 = getUnitPrice(selectedProducts[0]);
    const price2 = getUnitPrice(selectedProducts[1]);
    
    // Price is the more expensive one
    return Math.max(price1, price2);
  };

  const limpiarNombrePizza = (nombre: string): string => {
  return nombre?.replace(/^pizza(\s+(de|con))?\s*/i, "").trim() ?? "";
  };

  const handleConfirm = () => {
    if (selectedPizzaIds.length !== 2) return;
    
    const selectedProducts = pizzaProducts.filter(p => selectedPizzaIds.includes(p.id));
    
    if (selectedProducts[0].id === selectedProducts[1].id) {
      alert('Los sabores deben ser diferentes');
      return;
    }

    const precio_unitario = calculatePrice();
    const nombre1 = limpiarNombrePizza(selectedProducts[0].nombre);
    const nombre2 = limpiarNombrePizza(selectedProducts[1].nombre);
    const nombre_completo = `Pizza Mitad ${nombre1}/${nombre2}`;
    
    onConfirm({
      producto_id_izquierda: selectedProducts[0].id,
      producto_id_derecha: selectedProducts[1].id,
      cantidad,
      nombre_completo,
      precio_unitario,
    });
    
    // Reset form
    setSelectedPizzaIds([]);
    setCantidad(1);
    onClose();
  };

  const handleClose = () => {
    setSelectedPizzaIds([]);
    setCantidad(1);
    onClose();
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="pizza-mitad-mitad-overlay">
      <motion.div
        className="pizza-mitad-mitad-modal"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{ duration: 0.2 }}
      >
        <div className="pizza-mitad-mitad-header">
          <h2>Crear Pizza Mitad-Mitad</h2>
          <button className="close-btn" onClick={handleClose}>
            <Icons.XIcon size={20} />
          </button>
        </div>

        <div className="pizza-mitad-mitad-content">
          <div className="pizza-mitad-mitad-form">
            <div className="form-group">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <label>Selecciona 2 sabores de pizza</label>
                <div className="info-tooltip">
                  <Icons.InfoIcon className="info-icon" />
                  <div className="tooltip-content">
                    Elige exactamente 2 sabores diferentes para la pizza mitad-mitad
                  </div>
                </div>
              </div>
              <MultiSelect
                items={pizzaMultiSelect}
                selectedIds={selectedPizzaIds}
                onChange={handlePizzaSelection}
                label=""
                searchable={pizzaProducts.length > 10}
                placeholder="Buscar pizzas..."
              />
            </div>
          </div>

          {/* Quantity and Price */}
          <div className="pizza-mitad-mitad-summary">
            <div className="pizza-mitad-mitad-table">
              <div className="pizza-mitad-mitad-row pizza-mitad-mitad-row-header">
                <div className="pizza-mitad-mitad-cell">Cantidad</div>
                <div className="pizza-mitad-mitad-cell">Precio unitario</div>
                <div className="pizza-mitad-mitad-cell">Subtotal</div>
              </div>
              <div className="pizza-mitad-mitad-row">
                <div className="pizza-mitad-mitad-cell">
                  <div className="quantity-control">
                    <button 
                      className="qty-btn qty-btn-minus"
                      onClick={() => setCantidad(Math.max(1, cantidad - 1))}
                      disabled={cantidad <= 1}
                    >
                      -
                    </button>
                    <input
                      type="number"
                      className="qty-input"
                      value={cantidad}
                      onChange={(e) => setCantidad(Math.max(1, parseInt(e.target.value) || 1))}
                      min="1"
                      max="99"
                    />
                    <button 
                      className="qty-btn qty-btn-plus"
                      onClick={() => setCantidad(cantidad + 1)}
                    >
                      +
                    </button>
                  </div>
                </div>
                <div className="pizza-mitad-mitad-cell">
                  <div className="price-value">
                    {formatCurrency(calculatePrice())}
                  </div>
                </div>
                <div className="pizza-mitad-mitad-cell">
                  <div className="total-value">
                    {formatCurrency(calculatePrice() * cantidad)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="pizza-mitad-mitad-footer">
          <button 
            className="cancel-btn" 
            onClick={handleClose}
          >
            Cancelar
          </button>
          <button 
            className="confirm-btn" 
            onClick={handleConfirm}
            disabled={selectedPizzaIds.length !== 2}
          >
            Agregar al Carrito
          </button>
        </div>
      </motion.div>
    </div>,
    document.body
  );
};
