import { motion } from "framer-motion";
import { useState } from "react";
import type { Offer, OfferItem } from "../types/offer";
import { formatCurrency } from "../utils/formatters";
import "../styles/offer-quick-selector.css";
import * as Icons from "./shared/Icons";

interface OfferQuickSelectorProps {
  offers: Offer[];
  cartQuantities: Map<number, number>;
  onAddOffer: (offer: Offer) => void;
  onConfigureOffer: (offer: Offer) => void;
}

/* -------------------- Helpers -------------------- */

const getOfferType = (offer: Offer): "fixed" | "category" | "options" => {
  if (!offer.productos || offer.productos.length === 0) return "fixed";

  const hasFixedProducts = offer.productos.every(
    (item) =>
      item.productos &&
      item.productos.length === 1 &&
      !item.categoria_id
  );
  if (hasFixedProducts) return "fixed";

  const hasCategoryBased = offer.productos.some(
    (item) => item.categoria_id !== null
  );
  if (hasCategoryBased) return "category";

  const hasMultipleOptions = offer.productos.some(
    (item) => item.productos && item.productos.length > 1
  );
  if (hasMultipleOptions) return "options";

  return "fixed";
};

const getItemDetail = (
  item: OfferItem
): { cantidad: number; detalle: string } => {
  let detalle = "Producto";

  if (item.productos && item.productos.length > 1) {
    detalle = item.productos.map((p) => p.nombre).join(", ");
  } else if (item.categoria_id) {
    detalle = item.categoria_nombre || "Categoría";
  } else if (item.productos && item.productos.length === 1) {
    detalle = item.productos[0].nombre;
  }

  return { cantidad: item.cantidad, detalle };
};

/* -------------------- Component -------------------- */

export const OfferQuickSelector: React.FC<OfferQuickSelectorProps> = ({
  offers,
  cartQuantities,
  onAddOffer,
  onConfigureOffer,
}) => {
  const [expandedOfferId, setExpandedOfferId] = useState<number | null>(null);

  if (offers.length === 0) {
    return (
      <div className="offer-quick-selector">
        <div className="offer-selector-empty">
          <div className="offer-selector-empty-icon">
            <Icons.DiscountIcon size={36} />
          </div>
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
          const isFixed = offerType === "fixed";
          const isExpanded = expandedOfferId === offer.id;
          const shouldTruncate =
            offer.descripcion && offer.descripcion.length > 52;

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

              <div className="offer-card-content">
                <div className="offer-card-header">
                  <h3 className="offer-card-name">{offer.nombre}</h3>
                </div>

                {offer.descripcion && (
                  <>
                    <p
                      className={
                        isExpanded
                          ? "offer-card-description offer-card-description-expanded"
                          : "offer-card-description"
                      }
                    >
                      {isExpanded || !shouldTruncate ? (
                        offer.descripcion
                      ) : (
                        <>
                          {offer.descripcion.slice(0, 52)}
                          <span className="offer-card-ellipsis"> … </span>
                          <button
                            className="offer-card-see-more"
                            onClick={() => setExpandedOfferId(offer.id)}
                          >
                            Ver más
                          </button>
                        </>
                      )}
                    </p>

                    {isExpanded && (
                      <button
                        className="offer-card-see-more"
                        onClick={() => setExpandedOfferId(null)}
                      >
                        Ver menos
                      </button>
                    )}
                  </>
                )}

                {offer.productos && offer.productos.length > 0 && (
                  <div className="offer-card-items">
                    <div className="offer-card-separator" />
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

              <div className="offer-card-separator" />

              <div className="offer-card-footer">
                <div className="offer-card-price">
                  {formatCurrency(offer.precio)}
                </div>
                <button
                  className="offer-card-btn offer-card-btn-add"
                  onClick={() =>
                    isFixed ? onAddOffer(offer) : onConfigureOffer(offer)
                  }
                >
                  <Icons.PlusIcon size={14} />
                  Agregar
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
