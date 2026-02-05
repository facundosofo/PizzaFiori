import { motion } from 'framer-motion';
import type { Offer, OfferItem } from '../types/offer';
import { formatCurrency } from '../utils/formatters';
import '../styles/offer-quick-selector.css';
import * as Icons from './shared/Icons';

interface OfferQuickSelectorProps {
  offers: Offer[];
  cartQuantities: Map<number, number>; // oferta_id -> quantity in cart
  onAddOffer: (offer: Offer) => void;
  onConfigureOffer: (offer: Offer) => void;
}

// Detect offer type based on its configuration
const getOfferType = (offer: Offer): 'fixed' | 'category' | 'options' => {
  if (!offer.productos || offer.productos.length === 0) {
    return 'fixed'; // No items means fixed (shouldn't happen normally)
  }

  // Type 1: Fixed products (productos array is populated with single products)
  // Check if all items have productos populated and no category_id or multiple options
  const hasFixedProducts = offer.productos.every(
    (item) => item.productos && item.productos.length === 1 && !item.categoria_id
  );
  
  if (hasFixedProducts) {
    return 'fixed';
  }

  // Type 2: Category-based (customer chooses from category)
  const hasCategoryBased = offer.productos.some((item) => item.categoria_id !== null);
  if (hasCategoryBased) {
    return 'category';
  }

  // Type 3: Multiple options (customer chooses from list)
  const hasMultipleOptions = offer.productos.some(
    (item) => item.productos && item.productos.length > 1
  );
  if (hasMultipleOptions) {
    return 'options';
  }

  return 'fixed'; // Default fallback
};

const getItemDetail = (item: OfferItem): { cantidad: number; detalle: string } => {
  if (!item) return { cantidad: 0, detalle: "" };
  
  let detalle = "";
  
  // Opciones múltiples
  if (item.productos && item.productos.length > 1) {
    detalle = item.productos.map((p) => p.nombre).join(", ");
  }
  // Categoría
  else if (item.categoria_id) {
    detalle = item.categoria_nombre || "Categoría";
  }
  // Producto específico
  else if (item.productos && item.productos.length === 1) {
    detalle = item.productos[0].nombre;
  }
  else {
    detalle = "Producto";
  }
  
  return { cantidad: item.cantidad, detalle };
};

export const OfferQuickSelector: React.FC<OfferQuickSelectorProps> = ({
  offers,
  cartQuantities,
  onAddOffer,
  onConfigureOffer,
}) => {
  if (offers.length === 0) {
    return (
      <div className="offer-quick-selector">
        <div className="offer-selector-empty">
          <div className="offer-selector-empty-icon"><Icons.DiscountIcon size={36} /></div>
            <p>No hay ofertas disponibles</p>
        </div>
      </div>
    );
  }

  return (
    <div className="offer-quick-selector">
      <div className="offer-grid">
        {offers.map((offer) => {
          const qtyInCart = cartQuantities.get(offer.id) || 0;
          const offerType = getOfferType(offer);
          const isFixed = offerType === 'fixed';

          return (
            <motion.div
              key={offer.id}
              className="offer-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              whileHover={{ scale: 1.02, y: -4 }}
            >
              {qtyInCart > 0 && (
                <div className="offer-in-cart-badge">{qtyInCart}</div>
              )}

              {/* Contenido principal */}
              <div className="offer-card-content">
                <div className="offer-card-header">
                  <h3 className="offer-card-name">{offer.nombre}</h3>
                </div>

                {offer.descripcion && (
                  <p className="offer-card-description">{offer.descripcion}</p>
                )}

                {/* Items incluidos */}
                {offer.productos && offer.productos.length > 0 && (
                  <div className="offer-card-items">
                    <span className="offer-items-label">Incluye:</span>
                    <ul className="offer-items-list">
                      {offer.productos.map((item) => {
                        const { cantidad, detalle } = getItemDetail(item);
                        return (
                          <li key={item.id} className="offer-item">
                            <span className="offer-qty">{cantidad}x</span>
                            <span className="offer-item-detail">{detalle}</span>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>

              {/* Acciones - Abajo con precio y botón agregar */}
              <div className="offer-card-footer">
                <div className="offer-card-price">{formatCurrency(offer.precio)}</div>
                <button
                  className="offer-card-btn offer-card-btn-add"
                  onClick={() => isFixed ? onAddOffer(offer) : onConfigureOffer(offer)}
                >
                  <Icons.PlusIcon size={14} /> Agregar
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
